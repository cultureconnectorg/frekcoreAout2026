"""FREK Core — Endpoints HTTP /api/core/*."""
import logging

from fastapi import APIRouter, Header, HTTPException

from .models import IngestEvent
from . import service
from .scoring import get_rules
from .sources import resolve_source_from_bearer

logger = logging.getLogger("frek.core.routes")

# Prefixe /core (sans /v1) — namespace dedie a la couche evenementielle souveraine
core_router = APIRouter(prefix="/core", tags=["FREK Core — Couche evenementielle CC2026"])

db = None


def set_db(database):
    global db
    db = database
    service.set_db(database)


def _extract_bearer(authorization: str) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=403, detail="missing_bearer_token")
    return authorization[7:].strip()


@core_router.post("/ingest")
async def ingest(payload: IngestEvent, authorization: str = Header(default="")):
    """Receveur souverain d'evenements culturels.

    Idempotent par sha256(frek_id|event_id|action|timestamp).
    Aucun score n'est code en dur — toutes les valeurs viennent de frek_scoring_rules.
    """
    bearer = _extract_bearer(authorization)
    identified = resolve_source_from_bearer(bearer)
    if not identified:
        raise HTTPException(status_code=403, detail="unauthorized_source")
    # Defense-in-depth : la source declaree dans le body doit matcher le bearer
    if payload.source != identified:
        raise HTTPException(status_code=403, detail="source_mismatch")

    # Validation du badge_type : doit exister dans les regles si fourni
    if payload.badge_type:
        rules = await get_rules()
        if payload.badge_type not in rules["by_badge"]:
            raise HTTPException(status_code=422, detail=f"unknown_badge_type:{payload.badge_type}")

    result = await service.ingest_event(
        frek_id=payload.frek_id,
        event_id=payload.event_id,
        action=payload.action,
        badge_type=payload.badge_type,
        timestamp=payload.timestamp,
        source=identified,
    )
    return result


@core_router.get("/frek/{frek_id}")
async def get_frek_profile(frek_id: str):
    profile = await service.get_frek_profile(frek_id)
    if not profile:
        raise HTTPException(status_code=404, detail="frek_id_not_found")
    return profile


@core_router.get("/event/{event_id}/stats")
async def event_stats(event_id: str):
    return await service.event_stats(event_id)


@core_router.get("/ecosystem/pulse")
async def ecosystem_pulse():
    return await service.ecosystem_pulse()


@core_router.post("/admin/reload-rules")
async def reload_rules(x_admin_key: str = Header(default="")):
    """Force le rechargement du cache des regles de scoring.

    Protege par X-Admin-Key (meme secret que les autres endpoints admin).
    Utile apres une modification directe Mongo de frek_scoring_rules.
    """
    import os
    admin_key = os.environ.get("SECRET_KEY")
    if not admin_key or x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="invalid_admin_key")
    from .scoring import invalidate_cache, get_rules
    invalidate_cache()
    fresh = await get_rules(force_refresh=True)
    return {
        "reloaded": True,
        "rules_count": {
            "event_types": len(fresh["by_event"]),
            "badge_types": len(fresh["by_badge"]),
        },
    }
