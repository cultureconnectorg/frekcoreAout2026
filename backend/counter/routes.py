"""FREK Counter — Routes /api/core/count*."""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import service

logger = logging.getLogger("frek.counter.routes")

counter_router = APIRouter(prefix="/count", tags=["FREK Counter — Compteur souverain universel"])


def set_db(database):
    service.set_db(database)


def _admin_or_403(x_admin_key: str):
    """Same pattern as fingerprint/routes.py's helper of the same name.
    docs/decisions/0001-founder-decisions-2026-08-31.md."""
    expected = os.environ.get("SECRET_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="invalid_admin_key")


class CountEntry(BaseModel):
    external_ref: str = Field(..., min_length=1, max_length=256,
                              description="Identifiant unique source (hashe cote backend)")
    action: str = Field(..., min_length=3, max_length=64)
    context: str = Field("*", min_length=1, max_length=64)
    source: str = Field(..., description="kiltikonet | kora | fms | cfa_mans | cook_food | good_mood | cvl_agro | cip_foundation | laurent_ia")
    timestamp: Optional[str] = None
    idempotency_key: Optional[str] = None


class CountBatchRequest(BaseModel):
    entries: list[CountEntry] = Field(..., min_length=1, max_length=1000)


@counter_router.post("")
async def count_batch(req: CountBatchRequest, x_admin_key: str = Header(default="")):
    """Ingest batch — comptage souverain pour tout flux humain CVLN.

    Pas de badge_type obligatoire. Genere FREK-ID stable a partir
    de external_ref (hash deterministe). Idempotent.

    P0 fix (docs/decisions/0001-...): previously reachable with no credential
    at all — anyone could submit batches falsely attributed to any of the 9
    CVLN_SOURCES, polluting the cultural-impact scoring this feeds. Callers
    are other backend/partner systems (not end-user devices), so an admin-key
    gate does not break a legitimate high-frequency client the way it would
    for fingerprint/geo's device-originated /observe routes. Per-source API
    keys (rather than one shared key for all 9 sources) would be the more
    precise fix; tracked in reports/FREKCORE_COMPLETION_BACKLOG.md as this
    review did not find an existing per-source credential store to build on.
    """
    _admin_or_403(x_admin_key)
    res = await service.ingest_batch([e.model_dump() for e in req.entries])
    return res


@counter_router.get("/sources")
async def list_sources():
    """Liste les 9 sources CVLN reconnues."""
    return {
        "sources": [
            {"id": k, "description": v} for k, v in service.CVLN_SOURCES.items()
        ],
        "total_sources": len(service.CVLN_SOURCES),
    }


@counter_router.get("/rules")
async def list_rules():
    """Liste les regles de scoring souveraines."""
    cursor = service.db.frek_count_rules.find({}, {"_id": 0}).sort("base_score", -1)
    return {"rules": await cursor.to_list(length=100)}


@counter_router.get("/stats")
async def get_stats():
    by_source = await service.stats_by_source()
    avg = await service.average_cultural_impact_score()
    total_subjects = await service.db.frek_count_subjects.count_documents({})
    total_events = await service.db.frek_count_events.count_documents({})
    return {
        "total_subjects": total_subjects,
        "total_events": total_events,
        "average_cultural_impact_score": avg,
        "by_source": by_source,
        "sources_active": [s for s in by_source.keys() if by_source[s]["events"] > 0],
    }


@counter_router.get("/subject/{frek_id}")
async def get_subject(frek_id: str):
    """Lecture d'un subject (sans PII jamais)."""
    s = await service.db.frek_count_subjects.find_one({"frek_id": frek_id}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="not_found")
    return s
