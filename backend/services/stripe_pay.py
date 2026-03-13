"""
CC2026 Stripe Payment — Recharge Jetons via Checkout
"""
import os
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse, CheckoutStatusResponse,
)
from frek_v1.utils import now_iso

stripe_router = APIRouter(prefix="/payments", tags=["CC2026 Paiements"])
logger = logging.getLogger("frek.payments")

db = None

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")

# Pack definitions — NEVER accept amounts from frontend
JETON_PACKS = {
    "decouverte": {"jetons": 10, "prix": 13.50, "label": "Pack Decouverte (10 Jetons)"},
    "culture": {"jetons": 25, "prix": 30.00, "label": "Pack Culture (25 Jetons)"},
    "diaspora": {"jetons": 50, "prix": 55.00, "label": "Pack Diaspora (50 Jetons)"},
    "vip": {"jetons": 100, "prix": 100.00, "label": "Pack VIP (100 Jetons)"},
}


def set_db(database):
    global db
    db = database


class CheckoutRequest(BaseModel):
    pack_id: str = Field(..., description="decouverte, culture, diaspora, vip")
    badge_id: str = Field(..., description="Badge ID du participant")
    origin_url: str = Field(..., description="Frontend origin URL (window.location.origin)")


@stripe_router.post("/checkout")
async def create_checkout(request: CheckoutRequest, http_request: Request):
    pack = JETON_PACKS.get(request.pack_id)
    if not pack:
        raise HTTPException(status_code=400, detail=f"Pack invalide. Choix: {list(JETON_PACKS.keys())}")

    # Verify badge exists
    badge = await db.badges.find_one({"badge_id": request.badge_id}, {"_id": 0, "badge_id": 1, "prenom": 1, "frek_id": 1})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {request.badge_id} introuvable")

    # Build URLs from frontend origin
    success_url = f"{request.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/payment/cancel"

    # Initialize Stripe
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    # Create checkout session with backend-defined amount
    checkout_request = CheckoutSessionRequest(
        amount=pack["prix"],
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "pack_id": request.pack_id,
            "badge_id": request.badge_id,
            "frek_id": badge.get("frek_id", ""),
            "jetons": str(pack["jetons"]),
            "source": "cc2026_jeton_recharge",
        },
    )

    try:
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Stripe checkout error: {error_msg}")
        if "API key" in error_msg or "Invalid" in error_msg or "Authentication" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Stripe non configure: cle API invalide. Verifiez sk_test_ ou sk_live_ dans .env"
            )
        raise HTTPException(status_code=502, detail=f"Erreur Stripe: {error_msg}")

    # Create payment transaction record BEFORE redirect
    tx = {
        "payment_id": str(uuid.uuid4())[:12],
        "session_id": session.session_id,
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
    tx.pop("_id", None)

    logger.info(f"Checkout created: {session.session_id} | {request.badge_id} | Pack {request.pack_id}")
    return {"url": session.url, "session_id": session.session_id}


@stripe_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, http_request: Request):
    # Check if already processed
    tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    if tx.get("payment_status") == "paid":
        return {"status": "complete", "payment_status": "paid", "already_processed": True}

    # Poll Stripe for status
    host_url = str(http_request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    try:
        checkout_status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    except Exception as e:
        logger.warning(f"Stripe status error: {e}")
        return {"status": tx.get("status", "pending"), "payment_status": tx.get("payment_status", "initiated")}

    now = now_iso()

    if checkout_status.payment_status == "paid" and tx.get("payment_status") != "paid":
        # Credit wallet
        badge_id = tx["badge_id"]
        jetons = tx["jetons"]

        await db.badges.update_one(
            {"badge_id": badge_id},
            {"$inc": {"jetons_solde": jetons}}
        )

        # Record transaction in jetons system
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

        # Update payment transaction
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "status": "complete", "updated_at": now}}
        )

        logger.info(f"Payment confirmed: {session_id} | +{jetons}J -> {badge_id}")
        return {"status": "complete", "payment_status": "paid", "jetons_credited": jetons}

    elif checkout_status.status == "expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "expired", "status": "expired", "updated_at": now}}
        )
        return {"status": "expired", "payment_status": "expired"}

    return {"status": checkout_status.status, "payment_status": checkout_status.payment_status}


@stripe_router.get("/packs")
async def list_packs():
    return {"packs": JETON_PACKS, "currency": "eur", "stripe_public_key": os.environ.get("STRIPE_PUBLIC_KEY", "")}
