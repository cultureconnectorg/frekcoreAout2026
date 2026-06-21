"""
FREK Sync — Baserow bi-directional
"""
import os
import hmac
import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

from services.baserow import list_rows, create_row, update_row, get_fields, TABLE_ID

logger = logging.getLogger("frek.sync")
sync_router = APIRouter(prefix="/sync", tags=["FREK Sync"])

db = None
SYNC_SERVICE = "baserow"
WEBHOOK_SECRET = os.environ.get("BASEROW_WEBHOOK_SECRET", "")
ADMIN_KEY = os.environ.get("SECRET_KEY", "")


def set_db(database):
    global db
    db = database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_admin(x_admin_key: Optional[str]):
    if not ADMIN_KEY or not x_admin_key or not hmac.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(401, "X-Admin-Key requis")


def _verify_webhook_signature(body: bytes, signature: Optional[str]) -> bool:
    if not WEBHOOK_SECRET:
        # Mode non configure : on accepte (mais on log) — l'utilisateur doit definir BASEROW_WEBHOOK_SECRET
        return True
    if not signature:
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _identity_to_baserow(identity: dict) -> dict:
    """Mapping FREK identity -> Baserow row.
    Adapte aux champs reels de la table 865847 (best-effort, ignore les champs inconnus).
    """
    return {
        "frek_id": identity.get("frek_id", ""),
        "email_hash": identity.get("email_hash", ""),
        "current_stage": identity.get("current_stage", "GENESIS"),
        "event": identity.get("event") or "",
        "source": identity.get("source") or "",
        "created_at": identity.get("created_at", ""),
        "active": bool(identity.get("active", False)),
        "revoked": bool(identity.get("revoked", False)),
        "transferred": bool(identity.get("transferred", False)),
        "client_id": identity.get("client_id") or "",
    }


# ---------- Models ----------
class WebhookPayload(BaseModel):
    event_type: str = Field(..., description="rows.created | rows.updated | rows.deleted")
    table_id: Optional[int] = None
    items: List[dict] = Field(default_factory=list)


# ---------- Endpoints ----------
@sync_router.get("/baserow/status")
async def baserow_status(x_admin_key: Optional[str] = Header(None)):
    _require_admin(x_admin_key)
    cursor = await db.frek_sync_cursor.find_one({"service": SYNC_SERVICE}, {"_id": 0}) or {}
    pushed_today = await db.frek_sync_log.count_documents({
        "service": SYNC_SERVICE,
        "direction": "push",
        "at": {"$gte": _now()[:10]},
    })
    pulled_today = await db.frek_sync_log.count_documents({
        "service": SYNC_SERVICE,
        "direction": "pull",
        "at": {"$gte": _now()[:10]},
    })
    errors_24h = await db.frek_sync_log.count_documents({
        "service": SYNC_SERVICE,
        "status": "error",
        "at": {"$gte": _now()[:10]},
    })
    fields = await get_fields()
    return {
        "service": SYNC_SERVICE,
        "table_id": TABLE_ID,
        "configured": bool(os.environ.get("BASEROW_TOKEN")),
        "webhook_secret_set": bool(WEBHOOK_SECRET),
        "cursor": cursor,
        "pushed_today": pushed_today,
        "pulled_today": pulled_today,
        "errors_today": errors_24h,
        "baserow_field_count": len(fields) if isinstance(fields, list) else 0,
    }


@sync_router.post("/baserow/push/{frek_id}")
async def push_one(frek_id: str, x_admin_key: Optional[str] = Header(None)):
    _require_admin(x_admin_key)
    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(404, f"FREK-ID {frek_id} introuvable")

    payload = _identity_to_baserow(identity)
    # Try update if we already mapped this row, else create
    mapping = await db.frek_sync_mapping.find_one(
        {"service": SYNC_SERVICE, "frek_id": frek_id}, {"_id": 0}
    )
    row_id = mapping.get("baserow_row_id") if mapping else None

    if row_id:
        res = await update_row(row_id, payload)
        action = "update"
    else:
        res = await create_row(payload)
        action = "create"
        if res and isinstance(res, dict) and res.get("id"):
            await db.frek_sync_mapping.update_one(
                {"service": SYNC_SERVICE, "frek_id": frek_id},
                {"$set": {"baserow_row_id": res["id"], "synced_at": _now()}},
                upsert=True,
            )

    status = "ok" if res else "error"
    await db.frek_sync_log.insert_one({
        "sync_id": secrets.token_urlsafe(8),
        "service": SYNC_SERVICE,
        "direction": "push",
        "action": action,
        "frek_id": frek_id,
        "status": status,
        "baserow_row_id": (res or {}).get("id") if res else row_id,
        "at": _now(),
    })

    return {
        "frek_id": frek_id,
        "action": action,
        "status": status,
        "baserow_row_id": (res or {}).get("id") if res else row_id,
    }


@sync_router.post("/baserow/push")
async def push_recent(
    limit: int = 50,
    since: Optional[str] = None,
    x_admin_key: Optional[str] = Header(None),
):
    """Push toutes les identites creees apres `since` (defaut: dernier cursor)."""
    _require_admin(x_admin_key)
    if limit > 200:
        limit = 200

    cursor = await db.frek_sync_cursor.find_one({"service": SYNC_SERVICE}, {"_id": 0}) or {}
    cutoff = since or cursor.get("last_pushed_at") or "1970-01-01T00:00:00+00:00"

    q = {"created_at": {"$gt": cutoff}}
    identities = await db.frek_identities.find(q, {"_id": 0}).sort("created_at", 1).limit(limit).to_list(limit)

    results = {"pushed": 0, "errors": 0, "skipped": 0, "items": []}
    last_at = cutoff
    for identity in identities:
        frek_id = identity.get("frek_id")
        mapping = await db.frek_sync_mapping.find_one(
            {"service": SYNC_SERVICE, "frek_id": frek_id}, {"_id": 0}
        )
        row_id = mapping.get("baserow_row_id") if mapping else None
        payload = _identity_to_baserow(identity)

        if row_id:
            res = await update_row(row_id, payload)
            action = "update"
        else:
            res = await create_row(payload)
            action = "create"
            if res and isinstance(res, dict) and res.get("id"):
                await db.frek_sync_mapping.update_one(
                    {"service": SYNC_SERVICE, "frek_id": frek_id},
                    {"$set": {"baserow_row_id": res["id"], "synced_at": _now()}},
                    upsert=True,
                )

        if res:
            results["pushed"] += 1
        else:
            results["errors"] += 1
        results["items"].append({"frek_id": frek_id, "action": action, "ok": bool(res)})
        last_at = identity.get("created_at", last_at)
        await db.frek_sync_log.insert_one({
            "sync_id": secrets.token_urlsafe(8),
            "service": SYNC_SERVICE,
            "direction": "push",
            "action": action,
            "frek_id": frek_id,
            "status": "ok" if res else "error",
            "baserow_row_id": (res or {}).get("id") if res else row_id,
            "at": _now(),
        })

    await db.frek_sync_cursor.update_one(
        {"service": SYNC_SERVICE},
        {"$set": {"last_pushed_at": last_at, "updated_at": _now()}},
        upsert=True,
    )

    return results


@sync_router.post("/baserow/pull")
async def pull_baserow(
    size: int = 100,
    x_admin_key: Optional[str] = Header(None),
):
    """Pull les rows Baserow et reconcilie avec frek_sync_mapping (lecture seule cote FREK)."""
    _require_admin(x_admin_key)
    if size > 200:
        size = 200

    data = await list_rows(size=size, page=1)
    rows = data.get("results", [])
    reconciled = 0
    for row in rows:
        frek_id = row.get("frek_id")
        if not frek_id:
            continue
        await db.frek_sync_mapping.update_one(
            {"service": SYNC_SERVICE, "frek_id": frek_id},
            {"$set": {
                "baserow_row_id": row.get("id"),
                "last_pulled_at": _now(),
                "baserow_snapshot": row,
            }},
            upsert=True,
        )
        await db.frek_sync_log.insert_one({
            "sync_id": secrets.token_urlsafe(8),
            "service": SYNC_SERVICE,
            "direction": "pull",
            "frek_id": frek_id,
            "status": "ok",
            "baserow_row_id": row.get("id"),
            "at": _now(),
        })
        reconciled += 1

    await db.frek_sync_cursor.update_one(
        {"service": SYNC_SERVICE},
        {"$set": {"last_pulled_at": _now(), "updated_at": _now()}},
        upsert=True,
    )
    return {"pulled": len(rows), "reconciled": reconciled}


@sync_router.post("/baserow/webhook")
async def baserow_webhook(
    request: Request,
    x_baserow_signature: Optional[str] = Header(None),
):
    """Reception webhook Baserow (rows created / updated / deleted).
    Signature HMAC-SHA256 verifiee si BASEROW_WEBHOOK_SECRET est defini.
    On enregistre simplement le payload : la lignee FREK est SOURCE OF TRUTH, Baserow operationnel.
    """
    body = await request.body()
    if not _verify_webhook_signature(body, x_baserow_signature):
        raise HTTPException(401, "Signature webhook invalide")

    try:
        import json
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(400, "Payload JSON invalide")

    event_type = payload.get("event_type", "unknown")
    items = payload.get("items") or []
    received = []
    for item in items:
        frek_id = item.get("frek_id") if isinstance(item, dict) else None
        log_entry = {
            "sync_id": secrets.token_urlsafe(8),
            "service": SYNC_SERVICE,
            "direction": "webhook",
            "event_type": event_type,
            "frek_id": frek_id,
            "status": "received",
            "baserow_row_id": item.get("id") if isinstance(item, dict) else None,
            "snapshot": item,
            "at": _now(),
        }
        await db.frek_sync_log.insert_one(log_entry)
        if frek_id:
            await db.frek_sync_mapping.update_one(
                {"service": SYNC_SERVICE, "frek_id": frek_id},
                {"$set": {
                    "baserow_row_id": item.get("id"),
                    "baserow_snapshot": item,
                    "last_webhook_at": _now(),
                    "last_webhook_event": event_type,
                }},
                upsert=True,
            )
        received.append(frek_id)

    logger.info(f"Baserow webhook {event_type}: {len(items)} items")
    return {"ok": True, "event_type": event_type, "received": len(items)}


@sync_router.get("/baserow/log")
async def get_sync_log(limit: int = 50, x_admin_key: Optional[str] = Header(None)):
    _require_admin(x_admin_key)
    if limit > 200:
        limit = 200
    entries = await db.frek_sync_log.find(
        {"service": SYNC_SERVICE}, {"_id": 0}
    ).sort("at", -1).limit(limit).to_list(limit)
    return {"count": len(entries), "entries": entries}
