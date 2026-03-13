"""
CC2026 Badges API — 14 types, lifecycle complet
"""
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from badges.nomenclature import BADGE_TYPES, BADGE_STATUTS, generate_badge_id, is_nfc_enabled, check_zone_access
from frek_v1.auth import get_current_client, require_permission
from frek_v1.utils import hash_email, generate_frek_id, generate_qr_token, now_iso

badge_router = APIRouter(prefix="/badges", tags=["CC2026 Badges"])
logger = logging.getLogger("frek.badges")

db = None


def set_db(database):
    global db
    db = database


class BadgeCreateRequest(BaseModel):
    email: str
    prenom: str
    nom: str
    type_badge: str
    organisation: Optional[str] = None
    event: str = "CC2026"


class BadgeBatchRequest(BaseModel):
    badges: List[BadgeCreateRequest]


@badge_router.get("/types")
async def list_badge_types():
    """Liste les 14 types de badges CC2026"""
    return {"types": BADGE_TYPES, "count": len(BADGE_TYPES)}


@badge_router.post("/create")
async def create_badge(
    request: BadgeCreateRequest,
    client: dict = Depends(require_permission("emit")),
):
    if request.type_badge not in BADGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Type badge invalide. Types: {list(BADGE_TYPES.keys())}")

    email_hash = hash_email(request.email)

    # Check existing badge for this email
    existing = await db.badges.find_one(
        {"email_hash": email_hash, "event": request.event},
        {"_id": 0}
    )
    if existing:
        return {"badge": existing, "created": False, "message": "Badge existant retourne (idempotent)"}

    # Generate FREK-ID + badge
    frek_id = generate_frek_id()
    seq = await db.badges.count_documents({"event": request.event}) + 1
    badge_id = generate_badge_id(request.type_badge, seq)
    qr_token = generate_qr_token(frek_id)
    now = now_iso()

    badge_type_info = BADGE_TYPES[request.type_badge]
    badge_doc = {
        "badge_id": badge_id,
        "frek_id": frek_id,
        "email_hash": email_hash,
        "prenom": request.prenom,
        "nom": request.nom,
        "type_badge": request.type_badge,
        "type_name": badge_type_info["name"],
        "statut": "INSCRIT",
        "qr_token": qr_token,
        "nfc_enabled": badge_type_info["nfc"],
        "nfc_uid": None,
        "jetons_solde": 0,
        "organisation": request.organisation,
        "event": request.event,
        "client_id": client["client_id"],
        "date_inscription": now,
        "date_emission": None,
        "imprime": False,
        "remis": False,
        "created_at": now,
    }

    await db.badges.insert_one(badge_doc)

    # Also create FREK identity
    await db.frek_identities.insert_one({
        "frek_id": frek_id,
        "email_hash": email_hash,
        "client_id": client["client_id"],
        "source": "badge",
        "event": request.event,
        "current_stage": "GENESIS",
        "stages_completed": ["GENESIS"],
        "active": False,
        "qr_token": qr_token,
        "created_at": now,
        "activated_at": None,
        "metadata": {"badge_id": badge_id, "type": request.type_badge},
    })

    # Record GENESIS stage
    await db.frek_stages.insert_one({
        "frek_id": frek_id,
        "stage": "GENESIS",
        "fingerprint": email_hash[:64],
        "metadata_hash": None,
        "timestamp": now,
        "source": "badge_creation",
        "sequence": 1,
        "client_id": client["client_id"],
    })

    badge_doc.pop("_id", None)
    logger.info(f"Badge cree: {badge_id} ({request.type_badge}) pour {request.prenom}")
    return {"badge": badge_doc, "created": True, "message": f"Badge {badge_id} cree — FREK GENESIS"}


@badge_router.post("/batch-create")
async def batch_create_badges(
    request: BadgeBatchRequest,
    client: dict = Depends(require_permission("emit")),
):
    if len(request.badges) > 200:
        raise HTTPException(status_code=400, detail="Max 200 badges par batch")

    results = []
    created = 0
    for b in request.badges:
        try:
            result = await create_badge(b, client)
            results.append({"badge_id": result["badge"].get("badge_id"), "created": result["created"]})
            if result["created"]:
                created += 1
        except HTTPException as e:
            results.append({"email": b.email, "error": e.detail})

    return {"total": len(request.badges), "created": created, "results": results}


@badge_router.get("/{badge_id}")
async def get_badge(badge_id: str):
    badge = await db.badges.find_one({"badge_id": badge_id}, {"_id": 0})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {badge_id} introuvable")
    return badge


@badge_router.post("/{badge_id}/activate")
async def activate_badge(
    badge_id: str,
    client: dict = Depends(require_permission("emit")),
):
    badge = await db.badges.find_one({"badge_id": badge_id}, {"_id": 0})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {badge_id} introuvable")

    if badge["statut"] == "ACTIVE":
        return {"badge_id": badge_id, "statut": "ACTIVE", "message": "Deja active"}

    now = now_iso()
    await db.badges.update_one(
        {"badge_id": badge_id},
        {"$set": {"statut": "ACTIVE", "date_emission": now}}
    )

    # Activate FREK identity
    await db.frek_identities.update_one(
        {"frek_id": badge["frek_id"]},
        {"$set": {"active": True, "activated_at": now}}
    )

    return {"badge_id": badge_id, "statut": "ACTIVE", "message": "Badge active"}


@badge_router.post("/{badge_id}/confirm")
async def confirm_badge(
    badge_id: str,
    client: dict = Depends(require_permission("emit")),
):
    await db.badges.update_one(
        {"badge_id": badge_id},
        {"$set": {"statut": "CONFIRME"}}
    )
    return {"badge_id": badge_id, "statut": "CONFIRME"}


@badge_router.post("/{badge_id}/emit")
async def emit_badge(
    badge_id: str,
    client: dict = Depends(require_permission("emit")),
):
    now = now_iso()
    await db.badges.update_one(
        {"badge_id": badge_id},
        {"$set": {"statut": "BADGE_EMIS", "date_emission": now}}
    )
    return {"badge_id": badge_id, "statut": "BADGE_EMIS", "date_emission": now}


@badge_router.post("/{badge_id}/print")
async def mark_printed(
    badge_id: str,
    client: dict = Depends(require_permission("emit")),
):
    await db.badges.update_one(
        {"badge_id": badge_id},
        {"$set": {"imprime": True}}
    )
    return {"badge_id": badge_id, "imprime": True}


@badge_router.post("/{badge_id}/deliver")
async def mark_delivered(
    badge_id: str,
    client: dict = Depends(require_permission("emit")),
):
    await db.badges.update_one(
        {"badge_id": badge_id},
        {"$set": {"remis": True}}
    )
    return {"badge_id": badge_id, "remis": True}


@badge_router.get("/")
async def list_badges(
    event: str = "CC2026",
    type_badge: Optional[str] = None,
    statut: Optional[str] = None,
    page: int = 1,
    size: int = 50,
):
    query = {"event": event}
    if type_badge:
        query["type_badge"] = type_badge
    if statut:
        query["statut"] = statut

    total = await db.badges.count_documents(query)
    skip = (page - 1) * size
    badges = await db.badges.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(size).to_list(size)

    return {"total": total, "page": page, "size": size, "badges": badges}


@badge_router.get("/stats/overview")
async def badge_stats(event: str = "CC2026"):
    total = await db.badges.count_documents({"event": event})
    by_type = {}
    async for doc in db.badges.aggregate([
        {"$match": {"event": event}},
        {"$group": {"_id": "$type_badge", "count": {"$sum": 1}}},
    ]):
        by_type[doc["_id"]] = doc["count"]

    by_statut = {}
    async for doc in db.badges.aggregate([
        {"$match": {"event": event}},
        {"$group": {"_id": "$statut", "count": {"$sum": 1}}},
    ]):
        by_statut[doc["_id"]] = doc["count"]

    nfc_count = await db.badges.count_documents({"event": event, "nfc_enabled": True})
    printed = await db.badges.count_documents({"event": event, "imprime": True})
    delivered = await db.badges.count_documents({"event": event, "remis": True})

    return {
        "event": event,
        "total": total,
        "by_type": by_type,
        "by_statut": by_statut,
        "nfc_count": nfc_count,
        "printed": printed,
        "delivered": delivered,
    }
