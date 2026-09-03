"""
CC2026 Stripe Payment — Recharge Jetons via Checkout Session
Utilise stripe SDK directement
"""
import os
import logging
import uuid

import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from frek_v1.utils import now_iso
from security.policies import check_rate_limit

stripe_router = APIRouter(prefix="/payments", tags=["CC2026 Paiements"])
logger = logging.getLogger("frek.payments")

db = None

# Load Stripe key from .env (not system env)
from dotenv import dotenv_values
_env = dotenv_values("/app/backend/.env")
STRIPE_API_KEY = _env.get("STRIPE_API_KEY", os.environ.get("STRIPE_API_KEY", ""))
STRIPE_PUBLIC_KEY = _env.get("STRIPE_PUBLIC_KEY", os.environ.get("STRIPE_PUBLIC_KEY", ""))

JETON_PACKS = {
    "decouverte": {"jetons": 10, "prix_cents": 1350, "prix": 13.50, "label": "Pack Decouverte (10 Jetons CC)"},
    "culture": {"jetons": 25, "prix_cents": 3000, "prix": 30.00, "label": "Pack Culture (25 Jetons CC)"},
    "diaspora": {"jetons": 50, "prix_cents": 5500, "prix": 55.00, "label": "Pack Diaspora (50 Jetons CC)"},
    "vip": {"jetons": 100, "prix_cents": 10000, "prix": 100.00, "label": "Pack VIP (100 Jetons CC)"},
}


def set_db(database):
    global db
    db = database


class CheckoutRequest(BaseModel):
    pack_id: str = Field(..., description="decouverte, culture, diaspora, vip")
    badge_id: str = Field(..., description="Badge ID du participant")
    success_url: str = Field(..., description="URL de redirection apres paiement")
    cancel_url: str = Field(..., description="URL de redirection si annule")


@stripe_router.post("/checkout")
async def create_checkout(request: CheckoutRequest):
    """P0 review (docs/decisions/0001-founder-decisions-2026-08-31.md):
    left PUBLIC — CC2026 participants have no account/session system at
    all (badge_id, scanned or typed at a kiosk, is the only thing they
    hold), so requiring a credential here would break the real self-service
    top-up flow this route exists for. This is also lower real-world risk
    than it first looks: no jetons are ever credited from this endpoint —
    get_checkout_status() only credits after Stripe itself reports
    payment_status=="paid", so initiating a session for someone else's
    badge_id cannot move funds or credit jetons, only create a pending,
    unpaid payment_transactions row and an unused Stripe session (Stripe
    Checkout sessions expire on their own). Residual risk: badge_id has
    low entropy (badges/nomenclature.py:generate_badge_id — 4 random
    alphanumeric chars + a predictable trailing digit, ~1.6M keyspace per
    badge type), so it is guessable/enumerable, not a real bearer secret.
    Hardened with a rate limit per badge_id (bounds enumeration/pollution
    volume) rather than authentication (would break the real flow).
    Required change for a stronger fix: a real participant session/claim
    mechanism (e.g. a short-lived signed token issued at badge scan-in);
    not implemented here — new capability, not a route-level hardening,
    tracked in reports/FREKCORE_COMPLETION_BACKLOG.md.
    """
    pack = JETON_PACKS.get(request.pack_id)
    if not pack:
        raise HTTPException(status_code=400, detail=f"Pack invalide. Choix: {list(JETON_PACKS.keys())}")

    if not await check_rate_limit(scope=request.badge_id, action="checkout_create"):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    badge = await db.badges.find_one({"badge_id": request.badge_id}, {"_id": 0, "badge_id": 1, "prenom": 1, "frek_id": 1})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {request.badge_id} introuvable")

    stripe.api_key = STRIPE_API_KEY

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "unit_amount": pack["prix_cents"],
                    "product_data": {
                        "name": pack["label"],
                        "description": f"Culture Connect 2026 — {pack['jetons']} Jetons CC (1J = 1.50 EUR)",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata={
                "pack_id": request.pack_id,
                "badge_id": request.badge_id,
                "frek_id": badge.get("frek_id", ""),
                "jetons": str(pack["jetons"]),
            },
        )
    except stripe.error.AuthenticationError as e:
        logger.warning(f"Stripe auth error: {e}")
        raise HTTPException(status_code=503, detail="Stripe: cle API invalide ou permissions insuffisantes")
    except stripe.error.StripeError as e:
        logger.warning(f"Stripe error: {e}")
        raise HTTPException(status_code=502, detail=f"Erreur Stripe: {str(e)}")

    # Record pending transaction
    tx = {
        "payment_id": str(uuid.uuid4())[:12],
        "session_id": session.id,
        "badge_id": request.badge_id,
        "frek_id": badge.get("frek_id", ""),
        "pack_id": request.pack_id,
        "amount": pack["prix"],
        "currency": "eur",
        "jetons": pack["jetons"],
        "payment_status": "initiated",
        "status": "pending",
        "created_at": now_iso(),
        "updated_at": None,
    }
    await db.payment_transactions.insert_one(tx)

    logger.info(f"Checkout: {session.id} | {request.badge_id} | {request.pack_id}")
    return {"url": session.url, "session_id": session.id}


@stripe_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    if tx.get("payment_status") == "paid":
        return {"status": "complete", "payment_status": "paid", "jetons_credited": tx["jetons"]}

    stripe.api_key = STRIPE_API_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return {"status": tx.get("status", "pending"), "payment_status": tx.get("payment_status", "initiated")}

    now = now_iso()

    if session.payment_status == "paid" and tx.get("payment_status") != "paid":
        badge_id = tx["badge_id"]
        jetons = tx["jetons"]

        await db.badges.update_one(
            {"badge_id": badge_id},
            {"$inc": {"jetons_solde": jetons}}
        )

        await db.transactions.insert_one({
            "tx_id": tx["payment_id"],
            "type": "RECHARGE",
            "badge_id": badge_id,
            "frek_id": tx.get("frek_id"),
            "montant_jetons": jetons,
            "montant_eur": tx["amount"],
            "pack": tx["pack_id"],
            "payment_method": "stripe",
            "marchand_id": None,
            "description": f"Recharge Stripe pack {tx['pack_id']}",
            "solde_apres": None,
            "timestamp": now,
            "client_id": "stripe",
        })

        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "status": "complete", "updated_at": now}}
        )

        logger.info(f"Payment OK: {session_id} | +{jetons}J -> {badge_id}")
        return {"status": "complete", "payment_status": "paid", "jetons_credited": jetons}

    return {"status": session.status, "payment_status": session.payment_status}


@stripe_router.get("/packs")
async def list_packs():
    return {"packs": JETON_PACKS, "currency": "eur", "stripe_public_key": STRIPE_PUBLIC_KEY}
