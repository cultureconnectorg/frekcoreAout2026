"""
FREK Staff Scan — endpoints PWA terrain.
Reutilise la logique metier des modules badges/jetons/event mais avec auth staff (PIN).
Le client_id Kiltikonet est utilise par delegation. agent_id propage dans tous les logs.
"""
import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from badges.nomenclature import BADGE_TYPES, generate_badge_id, check_zone_access
from frek_v1.utils import (
    hash_email, generate_frek_id, generate_qr_token, now_iso,
)

from .routes import require_staff_perm, get_current_staff

logger = logging.getLogger("frek.staff.scan")
scan_router = APIRouter(prefix="/staff/scan", tags=["FREK Staff PWA — Scan"])

db = None


def set_db(database):
    global db
    db = database


def _client_id() -> str:
    return os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")


# Lazy import notarize_event (avoid circular)
async def _notarize(payload_type: str, payload_id: str, payload_data: dict, metadata: dict):
    try:
        from notary.service import notarize_event
        await notarize_event(payload_type, payload_id, payload_data, metadata)
    except Exception as e:
        logger.warning(f"Notarize failed: {e}")


# --- Models ---
class ScanAccessRequest(BaseModel):
    code: str = Field(..., description="badge_id OU qr_token OU frek_id (auto-detect)")
    zone: str = Field(..., description="ENTREE, SCENE, VIP_LOUNGE, BACKSTAGE, EXPOSANTS, PRESSE, ATELIERS")


class ScanCashlessRequest(BaseModel):
    code: str = Field(..., description="badge_id OU qr_token (auto-detect)")
    montant_jetons: int = Field(..., gt=0)
    marchand_id: str
    description: Optional[str] = None


class WalkinEmitRequest(BaseModel):
    email: str
    prenom: str
    nom: str
    type_badge: str = "PARTICIPANT"
    organisation: Optional[str] = None
    event: str = "CC2026"


class SyncBatchRequest(BaseModel):
    """Replay offline : liste d'actions a rejouer en bulk."""
    actions: list = Field(..., description="Liste d'objets {kind, payload, client_uuid}")


# --- Helpers ---
async def _resolve_badge(code: str) -> dict:
    """Resoud un code (badge_id, qr_token ou frek_id) vers un badge."""
    code = (code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Code vide")
    badge = await db.badges.find_one(
        {"$or": [{"badge_id": code}, {"qr_token": code}, {"frek_id": code}]},
        {"_id": 0},
    )
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge introuvable pour code={code}")
    return badge


# --- Endpoints ---
@scan_router.get("/zones")
async def scan_zones(staff: dict = Depends(get_current_staff)):
    from badges.nomenclature import ZONE_ACCESS
    return {
        "zones": ZONE_ACCESS,
        "allowed_for_agent": staff.get("allowed_zones", []),
    }


@scan_router.get("/marchands")
async def scan_marchands(staff: dict = Depends(require_staff_perm("scan_cashless"))):
    marchands = await db.marchands.find({}, {"_id": 0}).to_list(500)
    return {"marchands": marchands}


@scan_router.get("/badge/{code}")
async def scan_lookup(code: str, staff: dict = Depends(get_current_staff)):
    """Resolve QR/badge_id/frek_id → badge complet (read-only)."""
    badge = await _resolve_badge(code)
    return {
        "badge_id": badge["badge_id"],
        "frek_id": badge.get("frek_id"),
        "prenom": badge.get("prenom"),
        "nom": badge.get("nom"),
        "type_badge": badge.get("type_badge"),
        "type_name": badge.get("type_name"),
        "statut": badge.get("statut"),
        "nfc_enabled": badge.get("nfc_enabled", False),
        "jetons_solde": badge.get("jetons_solde", 0),
        "remis": badge.get("remis", False),
    }


@scan_router.post("/access")
async def scan_access(
    request: ScanAccessRequest,
    staff: dict = Depends(require_staff_perm("scan_access")),
):
    badge = await _resolve_badge(request.code)
    if badge.get("statut") == "REVOQUE":
        raise HTTPException(status_code=403, detail="Badge revoque")

    if not check_zone_access(badge["type_badge"], request.zone):
        raise HTTPException(
            status_code=403,
            detail=f"Acces REFUSE - badge {badge['type_badge']} non autorise zone {request.zone}",
        )

    # Optional: enforce staff allowed_zones
    allowed = staff.get("allowed_zones") or []
    if allowed and request.zone not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Agent {staff['agent_id']} non autorise zone {request.zone}",
        )

    now = now_iso()
    scan_id = str(uuid.uuid4())[:12]
    scan_doc = {
        "scan_id": scan_id,
        "badge_id": badge["badge_id"],
        "frek_id": badge.get("frek_id"),
        "zone": request.zone,
        "agent_id": staff["agent_id"],
        "type_badge": badge.get("type_badge"),
        "prenom": badge.get("prenom"),
        "nom": badge.get("nom"),
        "nfc_enabled": badge.get("nfc_enabled", False),
        "timestamp": now,
        "client_id": _client_id(),
        "via": "pwa_staff",
    }
    await db.scans.insert_one(scan_doc)
    scan_doc.pop("_id", None)

    # Notarize on FREK-Chain (immutable proof of access)
    await _notarize(
        "access_scan",
        badge.get("frek_id") or badge["badge_id"],
        {
            "scan_id": scan_id,
            "badge_id": badge["badge_id"],
            "zone": request.zone,
            "timestamp": now,
        },
        {"agent_id": staff["agent_id"], "client_id": _client_id()},
    )

    # Trigger EMISSION stage if scene/vip/backstage
    if request.zone in ("SCENE", "VIP_LOUNGE", "BACKSTAGE") and badge.get("frek_id"):
        seq_doc = await db.frek_stages.find_one(
            {"frek_id": badge["frek_id"]}, {"_id": 0, "sequence": 1},
            sort=[("sequence", -1)],
        )
        next_seq = (seq_doc["sequence"] + 1) if seq_doc else 1
        await db.frek_stages.insert_one({
            "frek_id": badge["frek_id"],
            "stage": "EMISSION",
            "fingerprint": scan_id,
            "metadata_hash": None,
            "timestamp": now,
            "source": f"pwa_scan_{request.zone.lower()}",
            "sequence": next_seq,
            "client_id": _client_id(),
        })
        await db.frek_identities.update_one(
            {"frek_id": badge["frek_id"]},
            {"$addToSet": {"stages_completed": "EMISSION"},
             "$set": {"current_stage": "EMISSION"}},
        )

    return {
        "access": "AUTORISE",
        "scan": scan_doc,
        "badge": {
            "badge_id": badge["badge_id"],
            "frek_id": badge.get("frek_id"),
            "prenom": badge.get("prenom"),
            "nom": badge.get("nom"),
            "type_badge": badge.get("type_badge"),
            "type_name": badge.get("type_name"),
            "jetons_solde": badge.get("jetons_solde", 0),
        },
    }


@scan_router.post("/cashless")
async def scan_cashless(
    request: ScanCashlessRequest,
    staff: dict = Depends(require_staff_perm("scan_cashless")),
):
    badge = await _resolve_badge(request.code)
    solde = int(badge.get("jetons_solde", 0))
    if solde < request.montant_jetons:
        raise HTTPException(
            status_code=400,
            detail=f"Solde insuffisant: {solde}J disponibles, {request.montant_jetons}J requis",
        )

    marchand = await db.marchands.find_one({"marchand_id": request.marchand_id}, {"_id": 0})
    if not marchand:
        raise HTTPException(status_code=404, detail=f"Marchand {request.marchand_id} introuvable")

    now = now_iso()
    tx_id = str(uuid.uuid4())[:12]
    new_solde = solde - request.montant_jetons
    montant_eur = request.montant_jetons * 1.50

    await db.badges.update_one(
        {"badge_id": badge["badge_id"]},
        {"$set": {"jetons_solde": new_solde}},
    )
    await db.marchands.update_one(
        {"marchand_id": request.marchand_id},
        {"$inc": {"solde_du": montant_eur}},
    )
    tx = {
        "tx_id": tx_id,
        "type": "PAIEMENT",
        "badge_id": badge["badge_id"],
        "frek_id": badge.get("frek_id"),
        "montant_jetons": request.montant_jetons,
        "montant_eur": montant_eur,
        "pack": None,
        "payment_method": "jeton",
        "marchand_id": request.marchand_id,
        "agent_id": staff["agent_id"],
        "description": request.description or f"Paiement {marchand.get('nom', request.marchand_id)}",
        "solde_apres": new_solde,
        "timestamp": now,
        "client_id": _client_id(),
        "via": "pwa_staff",
    }
    await db.transactions.insert_one(tx)
    tx.pop("_id", None)

    await _notarize(
        "jeton_tx",
        badge.get("frek_id") or badge["badge_id"],
        {
            "tx_id": tx_id,
            "type": "PAIEMENT",
            "montant_jetons": request.montant_jetons,
            "marchand_id": request.marchand_id,
            "solde_apres": new_solde,
            "timestamp": now,
        },
        {"agent_id": staff["agent_id"], "client_id": _client_id()},
    )

    return {"transaction": tx, "new_solde": new_solde, "marchand": marchand.get("nom")}


@scan_router.post("/emit")
async def scan_emit_walkin(
    request: WalkinEmitRequest,
    staff: dict = Depends(require_staff_perm("emit_walkin")),
):
    """Walk-in : creer un badge + FREK-ID a la volee sur le terrain."""
    if request.type_badge not in BADGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type invalide. Types: {list(BADGE_TYPES.keys())}",
        )

    email_hash = hash_email(request.email)
    existing = await db.badges.find_one(
        {"email_hash": email_hash, "event": request.event},
        {"_id": 0},
    )
    if existing:
        return {
            "badge": existing,
            "created": False,
            "message": "Badge existant retourne",
        }

    frek_id = generate_frek_id()
    seq = await db.badges.count_documents({"event": request.event}) + 1
    badge_id = generate_badge_id(request.type_badge, seq)
    qr_token = generate_qr_token(frek_id)
    now = now_iso()
    type_info = BADGE_TYPES[request.type_badge]

    badge_doc = {
        "badge_id": badge_id,
        "frek_id": frek_id,
        "email_hash": email_hash,
        "prenom": request.prenom,
        "nom": request.nom,
        "type_badge": request.type_badge,
        "type_name": type_info["name"],
        "statut": "ACTIVE",
        "qr_token": qr_token,
        "nfc_enabled": type_info["nfc"],
        "nfc_uid": None,
        "jetons_solde": 0,
        "organisation": request.organisation,
        "event": request.event,
        "client_id": _client_id(),
        "agent_id": staff["agent_id"],
        "date_inscription": now,
        "date_emission": now,
        "imprime": False,
        "remis": True,
        "created_at": now,
        "via": "pwa_walkin",
    }
    await db.badges.insert_one(badge_doc)

    await db.frek_identities.insert_one({
        "frek_id": frek_id,
        "email_hash": email_hash,
        "client_id": _client_id(),
        "source": "pwa_walkin",
        "event": request.event,
        "current_stage": "GENESIS",
        "stages_completed": ["GENESIS"],
        "active": True,
        "qr_token": qr_token,
        "created_at": now,
        "activated_at": now,
        "metadata": {"badge_id": badge_id, "agent_id": staff["agent_id"]},
    })
    await db.frek_stages.insert_one({
        "frek_id": frek_id,
        "stage": "GENESIS",
        "fingerprint": email_hash[:64],
        "metadata_hash": None,
        "timestamp": now,
        "source": "pwa_walkin",
        "sequence": 1,
        "client_id": _client_id(),
    })

    await _notarize(
        "walkin_emit",
        frek_id,
        {
            "badge_id": badge_id,
            "frek_id": frek_id,
            "email_hash": email_hash,
            "type_badge": request.type_badge,
            "timestamp": now,
        },
        {"agent_id": staff["agent_id"], "client_id": _client_id()},
    )

    badge_doc.pop("_id", None)
    logger.info(f"Walk-in emit: {badge_id} par {staff['agent_id']}")
    return {"badge": badge_doc, "created": True, "qr_token": qr_token}


@scan_router.post("/sync")
async def scan_sync(
    request: SyncBatchRequest,
    staff: dict = Depends(get_current_staff),
):
    """Replay actions offline en bulk. Chaque action : {kind, payload, client_uuid}."""
    results = []
    perms = set(staff.get("permissions", []))
    for idx, action in enumerate(request.actions or []):
        kind = action.get("kind")
        payload = action.get("payload") or {}
        client_uuid = action.get("client_uuid") or f"sync-{idx}"
        try:
            need = {"access": "scan_access", "cashless": "scan_cashless", "emit": "emit_walkin"}.get(kind)
            if need and need not in perms:
                results.append({"client_uuid": client_uuid, "ok": False, "error": f"Permission requise: {need}", "status": 403})
                continue
            if kind == "access":
                req = ScanAccessRequest(**payload)
                res = await scan_access(req, staff=staff)
            elif kind == "cashless":
                req = ScanCashlessRequest(**payload)
                res = await scan_cashless(req, staff=staff)
            elif kind == "emit":
                req = WalkinEmitRequest(**payload)
                res = await scan_emit_walkin(req, staff=staff)
            else:
                results.append({"client_uuid": client_uuid, "ok": False, "error": f"kind inconnu: {kind}"})
                continue
            results.append({"client_uuid": client_uuid, "ok": True, "result": res})
        except HTTPException as e:
            results.append({"client_uuid": client_uuid, "ok": False, "error": e.detail, "status": e.status_code})
        except Exception as e:
            logger.exception(f"sync action {kind} failed: {e}")
            results.append({"client_uuid": client_uuid, "ok": False, "error": str(e)})
    succ = sum(1 for r in results if r.get("ok"))
    return {"total": len(results), "success": succ, "failed": len(results) - succ, "results": results}
