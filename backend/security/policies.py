"""
FREK Security — rate limiting silencieux + anomaly trail.

Principes :
- L'autorite ne se justifie pas en public. Reponse 429 sans Retry-After, sans message explicatif.
- Anomalies stockees en interne (security_events) + webhook optionnel.
- Compteurs par (client_id, action) sur fenetre glissante (MongoDB).
- Aucune dependance a un service externe (Redis, etc.).
"""
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, Depends

logger = logging.getLogger("frek.security")

db = None

# Defaults conservateurs. Configurable via env.
DEFAULT_LIMITS = {
    # action: (count, window_seconds)
    "identity_emit": (int(os.environ.get("FREK_RATE_EMIT_PER_HOUR", "100")), 3600),
    "stage_transition": (int(os.environ.get("FREK_RATE_STAGE_PER_HOUR", "500")), 3600),
    "staff_login_fail": (5, 900),  # 5 echecs / 15 min => lockout
    "scan_access": (int(os.environ.get("FREK_RATE_SCAN_PER_HOUR", "5000")), 3600),
}


def set_db(database):
    global db
    db = database


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes():
    await db.rate_limits.create_index("ts")
    await db.rate_limits.create_index([("scope", 1), ("action", 1), ("ts", 1)])
    await db.security_events.create_index("created_at")
    await db.security_events.create_index("severity")
    await db.security_events.create_index("scope")


async def record_anomaly(
    kind: str,
    scope: str,
    severity: str = "info",
    details: Optional[dict] = None,
):
    """Log silencieux d'une anomalie. Optionnellement notifie webhook."""
    try:
        doc = {
            "kind": kind,
            "scope": scope,
            "severity": severity,
            "details": details or {},
            "created_at": _now_utc().isoformat(),
        }
        await db.security_events.insert_one(doc)
        logger.warning(f"[SECURITY:{severity}] {kind} scope={scope} details={details}")
        # Webhook optionnel (silence si non configure)
        webhook = os.environ.get("FREK_SECURITY_WEBHOOK_URL")
        if webhook and severity in ("warning", "critical"):
            import httpx
            try:
                async with httpx.AsyncClient(timeout=3.0) as c:
                    await c.post(webhook, json={**doc, "_id": None})
            except Exception:
                pass  # silence
    except Exception as e:
        logger.error(f"record_anomaly failed: {e}")


async def check_rate_limit(scope: str, action: str) -> bool:
    """Returns True if allowed. False means rate-limited (caller should 429 silently).
    scope = client_id ou agent_id ou IP. action = key dans DEFAULT_LIMITS."""
    cfg = DEFAULT_LIMITS.get(action)
    if not cfg:
        return True
    limit, window_s = cfg
    now = _now_utc()
    window_start = now - timedelta(seconds=window_s)

    count = await db.rate_limits.count_documents({
        "scope": scope,
        "action": action,
        "ts": {"$gte": window_start.isoformat()},
    })
    if count >= limit:
        await record_anomaly(
            kind="rate_limit_hit",
            scope=scope,
            severity="warning",
            details={"action": action, "count": count, "limit": limit, "window_seconds": window_s},
        )
        return False
    # Record this attempt
    await db.rate_limits.insert_one({
        "scope": scope,
        "action": action,
        "ts": now.isoformat(),
    })
    return True


def rate_limit_dep(action: str, get_scope):
    """Dependance FastAPI : applique la rate-limit pour un endpoint.
    get_scope(request_or_dependency) -> str (client_id ou agent_id)
    """
    from frek_v1.auth import get_current_client

    async def _check(client: dict = Depends(get_current_client)):
        scope = client["client_id"]
        ok = await check_rate_limit(scope=scope, action=action)
        if not ok:
            # 429 silencieux, pas de Retry-After, pas de detail
            raise HTTPException(status_code=429, detail="Trop de requetes")
        return client
    return _check


# --- Brute-force PIN lockout pour staff PWA ---
PIN_FAIL_THRESHOLD = 5
PIN_LOCK_MINUTES = 15


async def is_staff_locked(agent_id: str) -> bool:
    s = await db.staff.find_one({"agent_id": agent_id}, {"_id": 0, "locked_until": 1})
    if not s:
        return False
    lu = s.get("locked_until")
    if not lu:
        return False
    try:
        lu_dt = datetime.fromisoformat(lu.replace("Z", "+00:00"))
        if lu_dt.tzinfo is None:
            lu_dt = lu_dt.replace(tzinfo=timezone.utc)
        return lu_dt > _now_utc()
    except Exception:
        return False


async def register_staff_login_attempt(agent_id: str, success: bool, source_ip: Optional[str] = None):
    """Track failed_attempts. Lock account after PIN_FAIL_THRESHOLD fails in 15min."""
    if success:
        await db.staff.update_one(
            {"agent_id": agent_id},
            {"$set": {"failed_attempts": 0, "locked_until": None, "last_login": _now_utc().isoformat()}},
        )
        return
    s = await db.staff.find_one({"agent_id": agent_id}, {"_id": 0, "failed_attempts": 1, "first_fail_at": 1})
    if s is None:
        await record_anomaly("staff_login_unknown", scope=agent_id, severity="info", details={"ip": source_ip})
        return
    fails = int(s.get("failed_attempts") or 0) + 1
    update = {"failed_attempts": fails, "last_failed_at": _now_utc().isoformat()}
    if fails == 1 or not s.get("first_fail_at"):
        update["first_fail_at"] = _now_utc().isoformat()
    if fails >= PIN_FAIL_THRESHOLD:
        update["locked_until"] = (_now_utc() + timedelta(minutes=PIN_LOCK_MINUTES)).isoformat()
        await record_anomaly(
            kind="staff_lockout",
            scope=agent_id,
            severity="warning",
            details={"failed_attempts": fails, "ip": source_ip, "lock_minutes": PIN_LOCK_MINUTES},
        )
    await db.staff.update_one({"agent_id": agent_id}, {"$set": update})
