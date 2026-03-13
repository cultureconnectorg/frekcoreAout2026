"""
FREK v1 — Endpoints Identite
"""
from fastapi import APIRouter, HTTPException, Depends

from .models import (
    EmitRequest, EmitResponse, ActivateRequest,
    StatusResponse, DetailResponse, LookupRequest,
    FrekStage, STAGE_ORDER,
)
from .auth import get_current_client, require_permission, db as _auth_db
from .utils import hash_email, generate_frek_id, generate_qr_token, now_iso

identity_router = APIRouter(prefix="/identity", tags=["FREK v1 Identity"])

db = None


def set_db(database):
    global db
    db = database


@identity_router.post("/emit", response_model=EmitResponse)
async def emit_identity(
    request: EmitRequest,
    client: dict = Depends(require_permission("emit")),
):
    email_hash = hash_email(request.email)

    existing = await db.frek_identities.find_one(
        {"email_hash": email_hash, "client_id": client["client_id"]},
        {"_id": 0}
    )

    if existing:
        return EmitResponse(
            frek_id=existing["frek_id"],
            created=False,
            stage=existing.get("current_stage", "GENESIS"),
            message="Identite FREK existante retournee (idempotent)",
        )

    frek_id = generate_frek_id()
    qr_token = generate_qr_token(frek_id)
    now = now_iso()

    identity = {
        "frek_id": frek_id,
        "email_hash": email_hash,
        "client_id": client["client_id"],
        "source": request.source,
        "event": request.event,
        "current_stage": FrekStage.GENESIS.value,
        "stages_completed": [FrekStage.GENESIS.value],
        "active": False,
        "qr_token": qr_token,
        "created_at": now,
        "activated_at": None,
        "metadata": request.metadata or {},
    }

    await db.frek_identities.insert_one(identity)

    # Record GENESIS stage
    await db.frek_stages.insert_one({
        "frek_id": frek_id,
        "stage": FrekStage.GENESIS.value,
        "fingerprint": email_hash[:64],
        "metadata_hash": None,
        "timestamp": now,
        "source": request.source,
        "sequence": 1,
        "client_id": client["client_id"],
    })

    return EmitResponse(
        frek_id=frek_id,
        created=True,
        stage=FrekStage.GENESIS.value,
        message="Identite FREK creee — stage GENESIS enregistre",
    )


@identity_router.post("/{frek_id}/activate")
async def activate_identity(
    frek_id: str,
    request: ActivateRequest = None,
    client: dict = Depends(require_permission("emit")),
):
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]},
        {"_id": 0}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    if identity["active"]:
        return {"frek_id": frek_id, "active": True, "message": "Deja active"}

    await db.frek_identities.update_one(
        {"frek_id": frek_id},
        {"$set": {"active": True, "activated_at": now_iso()}}
    )

    return {
        "frek_id": frek_id,
        "active": True,
        "message": "Identite activee (1er scan physique)",
    }


@identity_router.get("/{frek_id}/status", response_model=StatusResponse)
async def get_status(frek_id: str):
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id}, {"_id": 0}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    stages_completed = identity.get("stages_completed", [])
    progression = (len(stages_completed) / 5) * 100

    return StatusResponse(
        frek_id=frek_id,
        active=identity["active"],
        current_stage=identity["current_stage"],
        stages_completed=stages_completed,
        progression=round(progression, 1),
        created_at=identity["created_at"],
    )


@identity_router.get("/{frek_id}/detail", response_model=DetailResponse)
async def get_detail(
    frek_id: str,
    client: dict = Depends(get_current_client),
):
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]},
        {"_id": 0}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    stages = await db.frek_stages.find(
        {"frek_id": frek_id}, {"_id": 0}
    ).sort("sequence", 1).to_list(100)

    return DetailResponse(
        frek_id=frek_id,
        active=identity["active"],
        current_stage=identity["current_stage"],
        stages=stages,
        email_hash=identity["email_hash"],
        source=identity["source"],
        event=identity.get("event"),
        created_at=identity["created_at"],
        activated_at=identity.get("activated_at"),
    )


@identity_router.post("/lookup")
async def lookup_by_qr(request: LookupRequest):
    identity = await db.frek_identities.find_one(
        {"qr_token": request.qr_token}, {"_id": 0}
    )
    if not identity:
        raise HTTPException(status_code=404, detail="QR token introuvable")

    return {
        "frek_id": identity["frek_id"],
        "current_stage": identity["current_stage"],
        "active": identity["active"],
    }
