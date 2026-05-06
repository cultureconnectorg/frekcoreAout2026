"""
FREK v1 — Endpoints Identite
"""
import io
import os
import qrcode
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from .models import (
    EmitRequest, EmitResponse, ActivateRequest,
    StatusResponse, DetailResponse, LookupRequest,
    RevokeRequest, RenewRequest,
    FrekStage, STAGE_ORDER,
)
from .auth import get_current_client, require_permission, db as _auth_db
from .utils import hash_email, generate_frek_id, generate_qr_token, now_iso

try:
    from notary.service import notarize_event
except Exception:
    async def notarize_event(*args, **kwargs):
        return None

identity_router = APIRouter(prefix="/identity", tags=["FREK v1 Identity"])
logger = logging.getLogger("frek.identity")

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
        "revoked": False,
        "revoked_at": None,
        "revoked_by": None,
        "revoke_reason": None,
        "expires_at": request.expires_at,
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

    # Notarize on FREK-Chain (auto-anchor to Bitcoin via OTS)
    await notarize_event(
        payload_type="identity_emit",
        payload_id=frek_id,
        payload_data={
            "frek_id": frek_id,
            "email_hash": email_hash,
            "stage": FrekStage.GENESIS.value,
            "source": request.source,
            "event": request.event,
            "created_at": now,
        },
        metadata={"client_id": client["client_id"]},
        event_id=request.event,
    )

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

    expires_at = identity.get("expires_at")
    expired = False
    if expires_at:
        try:
            from datetime import datetime as _dt, timezone as _tz
            exp_dt = _dt.fromisoformat(expires_at.replace("Z", "+00:00"))
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=_tz.utc)
            expired = exp_dt < _dt.now(_tz.utc)
        except Exception:
            expired = False

    return StatusResponse(
        frek_id=frek_id,
        active=identity["active"],
        current_stage=identity["current_stage"],
        stages_completed=stages_completed,
        progression=round(progression, 1),
        created_at=identity["created_at"],
        revoked=bool(identity.get("revoked", False)),
        revoked_at=identity.get("revoked_at"),
        revoke_reason=identity.get("revoke_reason"),
        expires_at=expires_at,
        expired=expired,
    )


@identity_router.post("/{frek_id}/revoke")
async def revoke_identity(
    frek_id: str,
    request: RevokeRequest,
    client: dict = Depends(require_permission("emit")),
):
    """Revocation immutable d'une identite FREK. La preuve historique reste lisible.
    Block 'revocation' ajoute a la FREK-Chain (CRL-like, pas de delete)."""
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]},
        {"_id": 0},
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")
    if identity.get("revoked"):
        return {
            "frek_id": frek_id,
            "revoked": True,
            "revoked_at": identity.get("revoked_at"),
            "message": "Deja revoque (idempotent)",
        }

    now = now_iso()
    await db.frek_identities.update_one(
        {"frek_id": frek_id},
        {"$set": {
            "revoked": True,
            "revoked_at": now,
            "revoked_by": client["client_id"],
            "revoke_reason": request.reason,
        }},
    )

    await notarize_event(
        payload_type="revocation",
        payload_id=frek_id,
        payload_data={
            "frek_id": frek_id,
            "revoked_at": now,
            "revoked_by": client["client_id"],
            "reason": request.reason,
        },
        metadata={"client_id": client["client_id"]},
        event_id=identity.get("event"),
    )

    logger.info(f"FREK-ID {frek_id} revoque par {client['client_id']} - raison: {request.reason}")
    return {
        "frek_id": frek_id,
        "revoked": True,
        "revoked_at": now,
        "reason": request.reason,
        "message": "Identite revoquee. Preuve historique conservee sur FREK-Chain.",
    }


@identity_router.post("/{frek_id}/renew")
async def renew_identity(
    frek_id: str,
    request: RenewRequest,
    client: dict = Depends(require_permission("emit")),
):
    """Renouvellement d'une identite FREK. Met a jour expires_at + ancre un block 'renewal'."""
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]},
        {"_id": 0},
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")
    if identity.get("revoked"):
        raise HTTPException(status_code=400, detail="Identite revoquee, renouvellement impossible")

    # Validation : expires_at doit etre dans le futur (si fourni)
    if request.expires_at:
        try:
            from datetime import datetime as _dt, timezone as _tz
            new_exp = _dt.fromisoformat(request.expires_at.replace("Z", "+00:00"))
            if new_exp.tzinfo is None:
                new_exp = new_exp.replace(tzinfo=_tz.utc)
            if new_exp <= _dt.now(_tz.utc):
                raise HTTPException(
                    status_code=400,
                    detail=f"expires_at doit etre dans le futur (recu: {request.expires_at})",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail=f"expires_at invalide (ISO 8601 attendu): {request.expires_at}")

    now = now_iso()
    previous = identity.get("expires_at")
    await db.frek_identities.update_one(
        {"frek_id": frek_id},
        {"$set": {"expires_at": request.expires_at, "renewed_at": now}},
    )

    await notarize_event(
        payload_type="renewal",
        payload_id=frek_id,
        payload_data={
            "frek_id": frek_id,
            "renewed_at": now,
            "previous_expires_at": previous,
            "new_expires_at": request.expires_at,
            "reason": request.reason,
        },
        metadata={"client_id": client["client_id"]},
        event_id=identity.get("event"),
    )

    logger.info(f"FREK-ID {frek_id} renouvele par {client['client_id']}")
    return {
        "frek_id": frek_id,
        "renewed_at": now,
        "expires_at": request.expires_at,
        "previous_expires_at": previous,
        "message": "Identite renouvelee.",
    }


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


@identity_router.get("/{frek_id}/qr.png")
async def get_identity_qr(frek_id: str):
    """Genere un QR code PNG pour une identite FREK"""
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id}, {"_id": 0, "frek_id": 1}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(f"{os.environ.get('APP_URL', 'https://frekcore.com')}/verify/{frek_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a0a0a", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")


@identity_router.post("/batch-emit")
async def batch_emit(
    emails: list[str],
    event: str = "CC2026",
    source: str = "batch",
    client: dict = Depends(require_permission("emit")),
):
    """
    Emission par lot — production CC2026
    Max 500 par requete
    """
    if len(emails) > 500:
        raise HTTPException(status_code=400, detail="Max 500 emails par batch")

    results = []
    created_count = 0

    for email in emails:
        email_hash = hash_email(email)
        existing = await db.frek_identities.find_one(
            {"email_hash": email_hash, "client_id": client["client_id"]},
            {"_id": 0, "frek_id": 1}
        )

        if existing:
            results.append({"email_index": emails.index(email), "frek_id": existing["frek_id"], "created": False})
            continue

        frek_id = generate_frek_id()
        qr_token = generate_qr_token(frek_id)
        now = now_iso()

        await db.frek_identities.insert_one({
            "frek_id": frek_id,
            "email_hash": email_hash,
            "client_id": client["client_id"],
            "source": source,
            "event": event,
            "current_stage": FrekStage.GENESIS.value,
            "stages_completed": [FrekStage.GENESIS.value],
            "active": False,
            "qr_token": qr_token,
            "created_at": now,
            "activated_at": None,
            "metadata": {},
        })

        await db.frek_stages.insert_one({
            "frek_id": frek_id,
            "stage": FrekStage.GENESIS.value,
            "fingerprint": email_hash[:64],
            "metadata_hash": None,
            "timestamp": now,
            "source": source,
            "sequence": 1,
            "client_id": client["client_id"],
        })

        results.append({"email_index": emails.index(email), "frek_id": frek_id, "created": True})
        created_count += 1

    logger.info(f"Batch emit: {created_count} created, {len(emails) - created_count} existing")

    return {
        "total": len(emails),
        "created": created_count,
        "existing": len(emails) - created_count,
        "results": results,
    }
