"""
FREK v1 — Endpoints Stats
"""
from fastapi import APIRouter, HTTPException, Depends

from .auth import require_permission
from .models import FrekStage

stats_router = APIRouter(prefix="/stats", tags=["FREK v1 Stats"])

db = None


def set_db(database):
    global db
    db = database


@stats_router.get("/cc2026")
async def stats_cc2026(client: dict = Depends(require_permission("stats"))):
    total = await db.frek_identities.count_documents({"event": "CC2026"})
    active = await db.frek_identities.count_documents({"event": "CC2026", "active": True})

    # Stages breakdown
    pipeline_agg = [
        {"$match": {"event": "CC2026"}},
        {"$group": {"_id": "$current_stage", "count": {"$sum": 1}}},
    ]
    breakdown_cursor = db.frek_identities.aggregate(pipeline_agg)
    breakdown = {}
    async for doc in breakdown_cursor:
        breakdown[doc["_id"]] = doc["count"]

    # Recent activity (last 10)
    recent = await db.frek_stages.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)

    return {
        "event": "CC2026",
        "objective": 40000,
        "total_identities": total,
        "active_identities": active,
        "progression_percent": round((total / 40000) * 100, 2) if total else 0,
        "stages_breakdown": breakdown,
        "recent_activity": recent,
    }


@stats_router.get("/{client_id}")
async def stats_by_client(
    client_id: str,
    client: dict = Depends(require_permission("stats")),
):
    total = await db.frek_identities.count_documents({"client_id": client_id})
    active = await db.frek_identities.count_documents({"client_id": client_id, "active": True})

    pipeline_agg = [
        {"$match": {"client_id": client_id}},
        {"$group": {"_id": "$current_stage", "count": {"$sum": 1}}},
    ]
    breakdown_cursor = db.frek_identities.aggregate(pipeline_agg)
    breakdown = {}
    async for doc in breakdown_cursor:
        breakdown[doc["_id"]] = doc["count"]

    recent = await db.frek_stages.find(
        {"client_id": client_id}, {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)

    return {
        "client_id": client_id,
        "total_identities": total,
        "active_identities": active,
        "stages_breakdown": breakdown,
        "recent_activity": recent,
    }
