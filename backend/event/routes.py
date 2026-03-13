"""
CC2026 Evenement J-0 — Scan, Zones, Live Stats
"""
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from badges.nomenclature import check_zone_access, ZONE_ACCESS
from frek_v1.auth import require_permission
from frek_v1.utils import now_iso

event_router = APIRouter(prefix="/event", tags=["CC2026 Evenement"])
logger = logging.getLogger("frek.event")

db = None


def set_db(database):
    global db
    db = database


class ScanRequest(BaseModel):
    badge_id: str
    zone: str = Field(..., description="ENTREE, SCENE, VIP_LOUNGE, BACKSTAGE, EXPOSANTS, PRESSE, ATELIERS")
    agent_id: str = Field(..., description="ID agent staff")


class NfcTapRequest(BaseModel):
    nfc_uid: str
    montant_jetons: int = Field(..., gt=0)
    marchand_id: str
    description: Optional[str] = None


@event_router.get("/zones")
async def list_zones():
    return {"zones": ZONE_ACCESS}


@event_router.post("/scan")
async def scan_entree(
    request: ScanRequest,
    client: dict = Depends(require_permission("stage")),
):
    badge = await db.badges.find_one({"badge_id": request.badge_id}, {"_id": 0})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {request.badge_id} introuvable")

    if badge["statut"] == "REVOQUE":
        raise HTTPException(status_code=403, detail="Badge revoque")

    # Check zone access
    if not check_zone_access(badge["type_badge"], request.zone):
        raise HTTPException(
            status_code=403,
            detail=f"Badge {badge['type_badge']} non autorise en zone {request.zone}"
        )

    now = now_iso()
    scan_id = str(uuid.uuid4())[:12]

    scan_doc = {
        "scan_id": scan_id,
        "badge_id": request.badge_id,
        "frek_id": badge.get("frek_id"),
        "zone": request.zone,
        "agent_id": request.agent_id,
        "type_badge": badge["type_badge"],
        "prenom": badge.get("prenom"),
        "nom": badge.get("nom"),
        "nfc_enabled": badge.get("nfc_enabled", False),
        "timestamp": now,
        "client_id": client["client_id"],
    }
    await db.scans.insert_one(scan_doc)

    # Record EMISSION stage if entering SCENE
    if request.zone in ("SCENE", "VIP_LOUNGE", "BACKSTAGE"):
        seq_doc = await db.frek_stages.find_one(
            {"frek_id": badge["frek_id"]}, {"_id": 0, "sequence": 1},
            sort=[("sequence", -1)]
        )
        next_seq = (seq_doc["sequence"] + 1) if seq_doc else 1

        await db.frek_stages.insert_one({
            "frek_id": badge["frek_id"],
            "stage": "EMISSION",
            "fingerprint": scan_id,
            "metadata_hash": None,
            "timestamp": now,
            "source": f"scan_{request.zone.lower()}",
            "sequence": next_seq,
            "client_id": client["client_id"],
        })
        await db.frek_identities.update_one(
            {"frek_id": badge["frek_id"]},
            {"$addToSet": {"stages_completed": "EMISSION"},
             "$set": {"current_stage": "EMISSION"}}
        )

    scan_doc.pop("_id", None)
    logger.info(f"Scan: {request.badge_id} -> {request.zone} par {request.agent_id}")
    return {
        "scan": scan_doc,
        "access": "AUTORISE",
        "badge_info": {
            "prenom": badge.get("prenom"),
            "nom": badge.get("nom"),
            "type_badge": badge["type_badge"],
            "type_name": badge.get("type_name"),
            "nfc_enabled": badge.get("nfc_enabled", False),
            "jetons_solde": badge.get("jetons_solde", 0),
        }
    }


@event_router.post("/nfc/tap")
async def nfc_tap_payment(
    request: NfcTapRequest,
    client: dict = Depends(require_permission("stage")),
):
    badge = await db.badges.find_one({"nfc_uid": request.nfc_uid}, {"_id": 0})
    if not badge:
        raise HTTPException(status_code=404, detail="Badge NFC introuvable")

    if not badge.get("nfc_enabled"):
        raise HTTPException(status_code=400, detail="Badge non equipe NFC")

    solde = badge.get("jetons_solde", 0)
    if solde < request.montant_jetons:
        raise HTTPException(status_code=400, detail=f"Solde insuffisant: {solde}J")

    now = now_iso()
    tx_id = str(uuid.uuid4())[:12]
    new_solde = solde - request.montant_jetons

    await db.badges.update_one(
        {"nfc_uid": request.nfc_uid},
        {"$set": {"jetons_solde": new_solde}}
    )

    marchand = await db.marchands.find_one({"marchand_id": request.marchand_id})
    if marchand:
        await db.marchands.update_one(
            {"marchand_id": request.marchand_id},
            {"$inc": {"solde_du": request.montant_jetons * 1.50}}
        )

    tx = {
        "tx_id": tx_id,
        "type": "NFC_PAIEMENT",
        "badge_id": badge["badge_id"],
        "frek_id": badge.get("frek_id"),
        "montant_jetons": request.montant_jetons,
        "montant_eur": request.montant_jetons * 1.50,
        "marchand_id": request.marchand_id,
        "description": request.description or "Paiement NFC",
        "solde_apres": new_solde,
        "timestamp": now,
        "client_id": client["client_id"],
    }
    await db.transactions.insert_one(tx)
    tx.pop("_id", None)

    return {"transaction": tx, "new_solde": new_solde}


@event_router.get("/stats/live")
async def live_stats(event: str = "CC2026"):
    total_scans = await db.scans.count_documents({})
    badges_total = await db.badges.count_documents({"event": event})
    badges_active = await db.badges.count_documents({"event": event, "statut": "ACTIVE"})
    badges_remis = await db.badges.count_documents({"event": event, "remis": True})

    # Scans by zone
    by_zone = {}
    async for doc in db.scans.aggregate([
        {"$group": {"_id": "$zone", "count": {"$sum": 1}}},
    ]):
        by_zone[doc["_id"]] = doc["count"]

    # Scans by hour (last 24h)
    by_hour = {}
    async for doc in db.scans.aggregate([
        {"$group": {"_id": {"$substr": ["$timestamp", 11, 2]}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]):
        by_hour[doc["_id"]] = doc["count"]

    # Recent scans
    recent = await db.scans.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(10)

    # Float jetons
    pipeline_float = [
        {"$match": {"type": {"$in": ["RECHARGE", "PAIEMENT", "NFC_PAIEMENT"]}}},
        {"$group": {
            "_id": "$type",
            "total_eur": {"$sum": "$montant_eur"},
            "total_jetons": {"$sum": "$montant_jetons"},
        }},
    ]
    float_data = {}
    async for doc in db.transactions.aggregate(pipeline_float):
        float_data[doc["_id"]] = {"eur": doc["total_eur"], "jetons": doc["total_jetons"]}

    return {
        "event": event,
        "timestamp": now_iso(),
        "scans_total": total_scans,
        "badges": {"total": badges_total, "active": badges_active, "remis": badges_remis},
        "scans_by_zone": by_zone,
        "scans_by_hour": by_hour,
        "recent_scans": recent,
        "float_jetons": float_data,
    }


@event_router.get("/stats/export")
async def export_stats(event: str = "CC2026"):
    """Export complet CSV-ready"""
    badges = await db.badges.find({"event": event}, {"_id": 0}).to_list(50000)
    transactions = await db.transactions.find({}, {"_id": 0}).to_list(50000)
    scans = await db.scans.find({}, {"_id": 0}).to_list(50000)

    return {
        "event": event,
        "export_date": now_iso(),
        "badges": {"count": len(badges), "data": badges},
        "transactions": {"count": len(transactions), "data": transactions},
        "scans": {"count": len(scans), "data": scans},
    }
