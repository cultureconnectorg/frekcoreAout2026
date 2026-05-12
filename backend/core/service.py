"""FREK Core — Logique metier ingest + queries."""
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from .models import INITIAL_ENRICHMENT
from . import scoring

logger = logging.getLogger("frek.core.service")

db = None


def set_db(database):
    global db
    db = database
    scoring.set_db(database)


async def ensure_indexes():
    """Index conformes a la directive — ne touche aux indexes existants."""
    await db.frek_subjects.create_index("frek_id", unique=True)
    await db.frek_subjects.create_index("status")
    await db.frek_events.create_index("idempotency_key", unique=True)
    await db.frek_events.create_index([("frek_id", 1), ("timestamp", -1)])
    await db.frek_events.create_index([("event_id", 1), ("timestamp", -1)])
    await db.frek_events.create_index([("source", 1), ("timestamp", -1)])
    await db.frek_scoring_rules.create_index("event_type", sparse=True)
    await db.frek_scoring_rules.create_index("badge_type", sparse=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_idempotency_key(frek_id: str, event_id: str, action: str, timestamp: str) -> str:
    payload = f"{frek_id}|{event_id}|{action}|{timestamp}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def ingest_event(
    frek_id: str,
    event_id: str,
    action: str,
    badge_type: Optional[str],
    timestamp: str,
    source: str,
) -> dict:
    """Ingere un evenement. Idempotent par (frek_id, event_id, action, timestamp).

    Retourne {received, frek_id, cultural_impact_score, idempotent, ...}.
    Ne retourne JAMAIS de _id Mongo.
    """
    idempotency_key = compute_idempotency_key(frek_id, event_id, action, timestamp)

    existing = await db.frek_events.find_one(
        {"idempotency_key": idempotency_key}, {"_id": 0}
    )
    if existing:
        subject = await db.frek_subjects.find_one({"frek_id": frek_id}, {"_id": 0})
        score = subject["cultural_impact_score"] if subject else existing.get("score_delta", 0)
        return {
            "received": True,
            "idempotent": True,
            "frek_id": frek_id,
            "cultural_impact_score": score,
            "event_recorded_at": existing.get("ingested_at"),
        }

    # Score depuis les regles MongoDB (jamais en dur)
    score_delta = await scoring.compute_score_delta(action, event_id, badge_type)

    ingested_at = now_iso()
    event_doc = {
        "frek_id": frek_id,
        "event_id": event_id,
        "action": action,
        "badge_type": badge_type,
        "source": source,
        "timestamp": timestamp,
        "score_delta": score_delta,
        "ingested_at": ingested_at,
        "idempotency_key": idempotency_key,
    }

    # Upsert subject AVANT insert event (sinon une race condition pourrait laisser
    # un event orphelin ; l'idempotency_key unique nous protege du double insert).
    subject_update = await db.frek_subjects.find_one_and_update(
        {"frek_id": frek_id},
        {
            "$setOnInsert": {
                "frek_id": frek_id,
                "status": "ACTIVE",
                "first_seen": ingested_at,
                "enrichment": dict(INITIAL_ENRICHMENT),
            },
            "$inc": {"cultural_impact_score": score_delta, "event_count": 1},
            "$set": {"last_event": ingested_at},
        },
        upsert=True,
        return_document=True,  # pymongo 4.x : True = AFTER (apres update)
        projection={"_id": 0},
    )

    try:
        await db.frek_events.insert_one(dict(event_doc))
    except Exception as e:
        # Race condition sur l'unique idempotency_key : un autre worker a deja
        # insere l'evenement entre nos deux requetes. On compense le double scoring.
        msg = str(e)
        if "duplicate key" in msg.lower() or "E11000" in msg:
            await db.frek_subjects.update_one(
                {"frek_id": frek_id},
                {"$inc": {"cultural_impact_score": -score_delta, "event_count": -1}},
            )
            subject_update = await db.frek_subjects.find_one({"frek_id": frek_id}, {"_id": 0})
            return {
                "received": True,
                "idempotent": True,
                "frek_id": frek_id,
                "cultural_impact_score": subject_update["cultural_impact_score"] if subject_update else 0,
            }
        raise

    return {
        "received": True,
        "idempotent": False,
        "frek_id": frek_id,
        "cultural_impact_score": subject_update["cultural_impact_score"],
        "score_delta": score_delta,
    }


async def get_frek_profile(frek_id: str) -> Optional[dict]:
    subject = await db.frek_subjects.find_one({"frek_id": frek_id}, {"_id": 0})
    if not subject:
        return None
    events_cursor = db.frek_events.find(
        {"frek_id": frek_id},
        {"_id": 0, "idempotency_key": 0, "ingested_at": 0, "source": 0, "frek_id": 0},
    ).sort("timestamp", -1).limit(100)
    events = await events_cursor.to_list(length=100)
    return {**subject, "events": events}


async def event_stats(event_id: str) -> dict:
    """Stats agregees pour un event_id donne."""
    # All frek_ids ever touched by this event
    pipeline_by_subject = [
        {"$match": {"event_id": event_id}},
        {"$group": {"_id": "$frek_id", "score": {"$sum": "$score_delta"}}},
    ]
    by_subject = await db.frek_events.aggregate(pipeline_by_subject).to_list(length=None)
    total_frek_ids = len(by_subject)
    avg_score = (sum(s["score"] for s in by_subject) / total_frek_ids) if total_frek_ids else 0.0

    # Statuses
    frek_ids = [s["_id"] for s in by_subject]
    status_counts = {"ACTIVE": 0, "PENDING": 0, "REVOKED": 0}
    if frek_ids:
        async for doc in db.frek_subjects.aggregate([
            {"$match": {"frek_id": {"$in": frek_ids}}},
            {"$group": {"_id": "$status", "n": {"$sum": 1}}},
        ]):
            status_counts[doc["_id"]] = doc["n"]

    # By badge_type
    by_badge = {}
    async for doc in db.frek_events.aggregate([
        {"$match": {"event_id": event_id, "badge_type": {"$ne": None}}},
        {"$group": {"_id": "$badge_type", "n": {"$addToSet": "$frek_id"}}},
    ]):
        by_badge[doc["_id"]] = len(doc["n"])

    # By source
    by_source = {}
    async for doc in db.frek_events.aggregate([
        {"$match": {"event_id": event_id}},
        {"$group": {"_id": "$source", "n": {"$addToSet": "$frek_id"}}},
    ]):
        by_source[doc["_id"]] = len(doc["n"])

    # First/last activation
    first = await db.frek_events.find_one(
        {"event_id": event_id, "action": "ACTIVATION"},
        {"_id": 0, "timestamp": 1}, sort=[("timestamp", 1)],
    )
    last = await db.frek_events.find_one(
        {"event_id": event_id, "action": "ACTIVATION"},
        {"_id": 0, "timestamp": 1}, sort=[("timestamp", -1)],
    )

    return {
        "event_id": event_id,
        "total_frek_ids": total_frek_ids,
        "active": status_counts["ACTIVE"],
        "pending": status_counts["PENDING"],
        "by_badge_type": by_badge,
        "by_source": by_source,
        "average_cultural_impact_score": round(avg_score, 2),
        "first_activation": first.get("timestamp") if first else None,
        "last_activation": last.get("timestamp") if last else None,
    }


async def ecosystem_pulse() -> dict:
    total = await db.frek_subjects.count_documents({})
    active = await db.frek_subjects.count_documents({"status": "ACTIVE"})
    total_events = await db.frek_events.count_documents({})
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    events_24h = await db.frek_events.count_documents({"ingested_at": {"$gte": yesterday}})

    # Top event_id (par nombre d'evenements)
    top_event = None
    async for doc in db.frek_events.aggregate([
        {"$group": {"_id": "$event_id", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
        {"$limit": 1},
    ]):
        top_event = doc["_id"]

    # Sources actives dans les dernieres 24h
    sources_active = []
    async for doc in db.frek_events.aggregate([
        {"$match": {"ingested_at": {"$gte": yesterday}}},
        {"$group": {"_id": "$source"}},
    ]):
        if doc["_id"]:
            sources_active.append(doc["_id"])

    # Avg cultural_impact_score
    avg = 0.0
    async for doc in db.frek_subjects.aggregate([
        {"$group": {"_id": None, "avg": {"$avg": "$cultural_impact_score"}}},
    ]):
        avg = doc.get("avg") or 0.0

    return {
        "timestamp": now_iso(),
        "total_frek_ids": total,
        "active_frek_ids": active,
        "total_events": total_events,
        "events_last_24h": events_24h,
        "top_event": top_event,
        "sources_active": sources_active,
        "average_cultural_impact_score": round(avg, 2),
        "ecosystem_status": "ALIVE" if total > 0 else "DORMANT",
    }
