"""FREK CFL — Couches social, anomaly, coupling, linguistic."""
import statistics
from datetime import datetime, timezone
from typing import Optional

db = None


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.frek_coupling_observations.create_index([("frek_id", 1), ("nfc_scan_id", 1)], unique=True)
    await db.frek_coupling_observations.create_index([("frek_id", 1), ("observed_at", -1)])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============ SOCIAL ============
async def compute_social(frek_id: str) -> dict:
    """Graphe de co-presence : combien d'autres FREK ont participe aux memes events."""
    # 1. event_ids du FREK
    event_ids = await db.frek_events.distinct("event_id", {"frek_id": frek_id})
    if not event_ids:
        return {"available": False, "co_presence_count": 0}

    # 2. autres frek_ids dans ces events (co-presence)
    pipeline = [
        {"$match": {"event_id": {"$in": event_ids}, "frek_id": {"$ne": frek_id}}},
        {"$group": {"_id": "$frek_id", "shared_events": {"$addToSet": "$event_id"}}},
    ]
    co_presence = {}
    async for doc in db.frek_events.aggregate(pipeline):
        co_presence[doc["_id"]] = len(doc["shared_events"])

    if not co_presence:
        return {
            "available": True,
            "co_presence_count": 0,
            "events_attended": len(event_ids),
            "top_peers": [],
        }

    # Top peers (FREK avec lesquels on a le plus d'events partages)
    top_peers = sorted(co_presence.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "available": True,
        "co_presence_count": len(co_presence),
        "events_attended": len(event_ids),
        "top_peers": [{"frek_id": p[0], "shared_events": p[1]} for p in top_peers],
        "centrality_score": round(sum(co_presence.values()) / len(co_presence), 2),
    }


# ============ ANOMALY ============
async def compute_anomaly(frek_id: str) -> dict:
    """Detection bot/replay : z-score sur la cadence + collisions device."""
    # 1. cadence z-score : si tous les inter_events sont trop reguliers (faible variance) => bot
    cursor = db.frek_events.find({"frek_id": frek_id}, {"_id": 0, "ingested_at": 1}).sort("ingested_at", 1)
    events = await cursor.to_list(length=1000)
    if len(events) < 3:
        return {"available": False, "anomaly_score": 0.0}

    times = []
    for e in events:
        try:
            times.append(datetime.fromisoformat((e["ingested_at"] or "").replace("Z", "+00:00")))
        except Exception:
            continue
    if len(times) < 3:
        return {"available": False, "anomaly_score": 0.0}
    inter = [(times[i] - times[i - 1]).total_seconds() for i in range(1, len(times))]
    mean = statistics.fmean(inter)
    stdev = statistics.pstdev(inter)
    # CV = coefficient of variation. Bot = CV proche de 0 (cadence trop reguliere)
    cv = (stdev / mean) if mean > 0 else 1.0
    bot_signal = max(0.0, 1.0 - cv) if mean < 60 and len(inter) >= 5 else 0.0  # event toutes les < 60s

    # 2. collisions device (autre FREK avec le meme device_hash)
    shared = 0
    async for d in db.frek_device_observations.find({"frek_id": frek_id}, {"device_hash": 1}):
        c = await db.frek_device_observations.count_documents(
            {"device_hash": d["device_hash"], "frek_id": {"$ne": frek_id}}
        )
        shared += c

    device_signal = min(1.0, shared / 10.0)  # 10+ collisions = score max

    # Score composite [0..1]
    score = round(0.6 * bot_signal + 0.4 * device_signal, 4)
    return {
        "available": True,
        "anomaly_score": score,
        "bot_signal": round(bot_signal, 4),
        "device_collision_signal": round(device_signal, 4),
        "cadence_cv": round(cv, 4),
        "thresholds": {"alert_at": 0.5, "block_at": 0.85},
    }


# ============ COUPLING (online <-> offline) ============
async def record_nfc_scan(frek_id: str, nfc_scan_id: str, surface: str = "scan") -> dict:
    """Enregistre un scan NFC physique. Couple ensuite avec verification web."""
    if not nfc_scan_id:
        return {"recorded": False}
    await db.frek_coupling_observations.update_one(
        {"frek_id": frek_id, "nfc_scan_id": nfc_scan_id},
        {
            "$setOnInsert": {
                "frek_id": frek_id,
                "nfc_scan_id": nfc_scan_id,
                "observed_at": _now(),
                "kind": "nfc_scan",
                "surface": surface,
                "web_verified": False,
            }
        },
        upsert=True,
    )
    return {"recorded": True}


async def record_web_verify(frek_id: str, nfc_scan_id: Optional[str] = None) -> dict:
    """Enregistre une verification web. Couple le scan NFC le plus recent si fourni."""
    if nfc_scan_id:
        # Match explicite
        res = await db.frek_coupling_observations.update_one(
            {"frek_id": frek_id, "nfc_scan_id": nfc_scan_id, "web_verified": False},
            {"$set": {"web_verified": True, "web_verified_at": _now()}},
        )
        return {"coupled": bool(res.matched_count)}
    # Match implicite : prend le plus recent NFC non couple
    res = await db.frek_coupling_observations.find_one_and_update(
        {"frek_id": frek_id, "web_verified": False},
        {"$set": {"web_verified": True, "web_verified_at": _now()}},
        sort=[("observed_at", -1)],
    )
    return {"coupled": res is not None}


async def compute_coupling(frek_id: str) -> dict:
    total = await db.frek_coupling_observations.count_documents({"frek_id": frek_id})
    verified = await db.frek_coupling_observations.count_documents(
        {"frek_id": frek_id, "web_verified": True}
    )
    rate = round((verified / total) * 100, 1) if total else 0.0
    return {
        "available": total > 0,
        "nfc_scans": total,
        "coupled_with_web": verified,
        "coupling_rate_pct": rate,
    }


# ============ LINGUISTIC (stub) ============
async def compute_linguistic(frek_id: str) -> dict:
    """Stub : aucune source textuelle dans FREKCORE pour le moment.

    Activable dans la couche kiltikonet/kora une fois que les commentaires/atelier
    text inputs existent. Ici on retourne un placeholder.
    """
    return {
        "available": False,
        "reason": "no_text_corpus_yet",
        "would_compute": ["avg_sentence_length", "lexical_diversity", "writing_velocity"],
    }
