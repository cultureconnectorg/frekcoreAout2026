"""
FREK v1 — Dashboard CC2026 : Collecteur de Stats Consolide
Agrege les donnees FREK v1 + Baserow pour le monitor operationnel
"""
import os
import logging
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from .utils import get_env

dashboard_router = APIRouter(prefix="/dashboard", tags=["FREK v1 Dashboard"])
logger = logging.getLogger("frek.dashboard")

BASEROW_TOKEN = os.environ.get("BASEROW_TOKEN", "")
BASEROW_API = "https://api.baserow.io/api"

db = None


def set_db(database):
    global db
    db = database


async def _fetch_baserow_table(table_id: int, limit: int = 100) -> list:
    """Fetch rows from a Baserow table"""
    if not BASEROW_TOKEN:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BASEROW_API}/database/rows/table/{table_id}/",
                headers={"Authorization": f"Token {BASEROW_TOKEN}"},
                params={"size": limit},
            )
            if resp.status_code == 200:
                return resp.json().get("results", [])
            logger.warning(f"Baserow {table_id}: HTTP {resp.status_code}")
            return []
    except Exception as e:
        logger.warning(f"Baserow unreachable: {e}")
        return []


@dashboard_router.get("/cc2026")
async def dashboard_cc2026(x_admin_key: Optional[str] = Header(None)):
    """
    Dashboard consolide CC2026
    Retourne metriques FREK + Baserow
    Protege par X-Admin-Key si fourni (sinon metriques limitees)
    """
    is_admin = x_admin_key == os.environ.get("SECRET_KEY", "")

    # --- FREK v1 Stats (direct MongoDB) ---
    total_identities = await db.frek_identities.count_documents({"event": "CC2026"})
    active_identities = await db.frek_identities.count_documents({"event": "CC2026", "active": True})
    total_all = await db.frek_identities.count_documents({})

    # Stages breakdown
    pipeline_stages = [
        {"$match": {"event": "CC2026"}},
        {"$group": {"_id": "$current_stage", "count": {"$sum": 1}}},
    ]
    breakdown = {}
    async for doc in db.frek_identities.aggregate(pipeline_stages):
        breakdown[doc["_id"]] = doc["count"]

    # Stage progression over time (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    pipeline_timeline = [
        {"$match": {"timestamp": {"$gte": thirty_days_ago}}},
        {"$group": {
            "_id": {"$substr": ["$timestamp", 0, 10]},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    timeline = []
    async for doc in db.frek_stages.aggregate(pipeline_timeline):
        timeline.append({"date": doc["_id"], "stages_recorded": doc["count"]})

    # Recent activity
    recent_stages = await db.frek_stages.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(20).to_list(20)

    # Clients activity
    pipeline_clients = [
        {"$group": {"_id": "$client_id", "count": {"$sum": 1}}},
    ]
    clients_activity = {}
    async for doc in db.frek_identities.aggregate(pipeline_clients):
        clients_activity[doc["_id"]] = doc["count"]

    # Luciole stage funnel
    stage_order = ["GENESIS", "WORKSHOP", "METAMORPHOSE", "EMISSION", "LEGACY"]
    funnel = []
    for stage in stage_order:
        count = await db.frek_identities.count_documents({
            "event": "CC2026",
            "stages_completed": stage,
        })
        funnel.append({"stage": stage, "count": count})

    # Progression
    target = 40000
    progression = round((total_identities / target) * 100, 2) if total_identities else 0

    result = {
        "event": "CC2026",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_status": "connected",
        "frek_version": "2.0.0",
        "target": target,
        "metrics": {
            "total_identities": total_identities,
            "active_identities": active_identities,
            "total_all_clients": total_all,
            "progression_percent": progression,
        },
        "stages_breakdown": breakdown,
        "luciole_funnel": funnel,
        "timeline_30d": timeline,
        "clients_activity": clients_activity,
    }

    if is_admin:
        result["recent_activity"] = recent_stages
        result["admin_mode"] = True

    return result


@dashboard_router.get("/cc2026/live")
async def dashboard_live():
    """
    Endpoint leger pour polling live (2s)
    Retourne uniquement les metriques essentielles
    """
    total = await db.frek_identities.count_documents({"event": "CC2026"})
    active = await db.frek_identities.count_documents({"event": "CC2026", "active": True})
    target = 40000

    # Last stage recorded
    last_stage = await db.frek_stages.find_one(
        {}, {"_id": 0, "stage": 1, "timestamp": 1, "frek_id": 1},
        sort=[("timestamp", -1)]
    )

    return {
        "total": total,
        "active": active,
        "target": target,
        "percentage": round((total / target) * 100, 2) if total else 0,
        "last_activity": last_stage,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
