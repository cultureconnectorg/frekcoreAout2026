"""FREK Security — endpoints d'audit interne (admin only)"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from frek_v1.admin import verify_admin_key

logger = logging.getLogger("frek.security.routes")
security_router = APIRouter(prefix="/admin/security", tags=["FREK Security — Audit interne"])

db = None


def set_db(database):
    global db
    db = database


@security_router.get("/events")
async def list_security_events(
    severity: Optional[str] = Query(None, description="info | warning | critical"),
    kind: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    _: bool = Depends(verify_admin_key),
):
    """Anomalies internes : rate-limit hits, lockouts, login fails, etc.
    Strictement admin (X-Admin-Key)."""
    query = {}
    if severity:
        query["severity"] = severity
    if kind:
        query["kind"] = kind
    if scope:
        query["scope"] = scope
    cursor = db.security_events.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    events = await cursor.to_list(limit)
    return {"count": len(events), "events": events}


@security_router.get("/lockouts")
async def list_active_lockouts(_: bool = Depends(verify_admin_key)):
    """Comptes staff actuellement verrouilles (brute-force)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.staff.find(
        {"locked_until": {"$gt": now}},
        {"_id": 0, "agent_id": 1, "nom": 1, "role": 1, "failed_attempts": 1, "locked_until": 1, "last_failed_at": 1},
    )
    rows = await cursor.to_list(500)
    return {"count": len(rows), "lockouts": rows}


@security_router.post("/staff/{agent_id}/unlock")
async def unlock_staff(agent_id: str, _: bool = Depends(verify_admin_key)):
    """Deverouille manuellement un compte staff."""
    res = await db.staff.update_one(
        {"agent_id": agent_id},
        {"$set": {"failed_attempts": 0, "locked_until": None}},
    )
    if res.matched_count == 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent introuvable")
    logger.info(f"Staff unlocked: {agent_id}")
    return {"agent_id": agent_id, "unlocked": True}
