"""FREK Geo — Service metier (consent, observation, heatmap)."""
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from . import encoder, nominatim

logger = logging.getLogger("frek.geo.service")

db = None

# Niveaux de consentement
CONSENT_LEVELS = ("none", "country", "city", "precise")


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.frek_geo_consent.create_index("frek_id", unique=True)
    await db.frek_geo_observations.create_index("idempotency_key", unique=True)
    await db.frek_geo_observations.create_index([("frek_id", 1), ("observed_at", -1)])
    await db.frek_geo_observations.create_index("h3_9")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Consent ----------
async def get_consent(frek_id: str) -> dict:
    doc = await db.frek_geo_consent.find_one({"frek_id": frek_id}, {"_id": 0})
    if not doc:
        return {"frek_id": frek_id, "level": "none", "granted_at": None, "revoked_at": None}
    return doc


async def set_consent(frek_id: str, level: str) -> dict:
    if level not in CONSENT_LEVELS:
        raise ValueError(f"invalid_level:{level}")
    now = now_iso()
    update = {
        "$set": {
            "frek_id": frek_id,
            "level": level,
            "granted_at": now if level != "none" else None,
            "revoked_at": now if level == "none" else None,
        }
    }
    await db.frek_geo_consent.update_one({"frek_id": frek_id}, update, upsert=True)
    # Si revocation -> purge des observations
    if level == "none":
        await db.frek_geo_observations.delete_many({"frek_id": frek_id})
    return await get_consent(frek_id)


# ---------- Observation ----------
def _truncate_for_level(enriched: dict, level: str) -> dict:
    """Retire les champs trop precis selon le consentement."""
    if level == "precise":
        return enriched
    if level == "city":
        enriched.pop("lat", None)
        enriched.pop("lon", None)
        enriched.pop("plus_code_hd", None)
        enriched.pop("h3_12", None)
        return enriched
    if level == "country":
        # garde seulement country + country_code
        return {
            "country": enriched.get("country"),
            "country_code": enriched.get("country_code"),
            "level_applied": "country",
        }
    return {}


async def observe(
    frek_id: str,
    lat: float,
    lon: float,
    accuracy_m: Optional[float] = None,
    source_event_id: Optional[str] = None,
    skip_reverse: bool = False,
) -> dict:
    """Enregistre une observation geo. Respecte le consentement.

    Retourne {recorded, level, ...enriched} ou {recorded:false, reason:consent_required}.
    Idempotent par (frek_id, h3_12, minute) — defenses replay terrain.
    """
    consent = await get_consent(frek_id)
    level = consent.get("level", "none")
    if level == "none":
        return {"recorded": False, "reason": "consent_required"}

    encoded = encoder.encode_all(lat, lon)
    reverse_data = {} if skip_reverse else await nominatim.reverse(lat, lon, encoded["h3_9"])
    enriched = {**encoded, **reverse_data}

    now = now_iso()
    minute_bucket = now[:16]  # YYYY-MM-DDTHH:MM
    idempotency_key = hashlib.sha256(
        f"{frek_id}|{encoded['h3_12']}|{minute_bucket}".encode()
    ).hexdigest()

    existing = await db.frek_geo_observations.find_one(
        {"idempotency_key": idempotency_key}, {"_id": 0}
    )
    if existing:
        return {"recorded": True, "idempotent": True, "level": level, **_truncate_for_level(enriched, level)}

    doc = {
        "frek_id": frek_id,
        "lat": encoded["lat"],
        "lon": encoded["lon"],
        "accuracy_m": float(accuracy_m) if accuracy_m is not None else None,
        "plus_code": encoded["plus_code"],
        "plus_code_hd": encoded["plus_code_hd"],
        "h3_9": encoded["h3_9"],
        "h3_12": encoded["h3_12"],
        "geohash_8": encoded["geohash_8"],
        "country": reverse_data.get("country"),
        "country_code": reverse_data.get("country_code"),
        "region": reverse_data.get("region"),
        "city": reverse_data.get("city"),
        "suburb": reverse_data.get("suburb"),
        "observed_at": now,
        "source_event_id": source_event_id,
        "idempotency_key": idempotency_key,
    }
    try:
        await db.frek_geo_observations.insert_one(dict(doc))
    except Exception as e:
        msg = str(e).lower()
        if "duplicate key" not in msg and "e11000" not in msg:
            raise

    return {"recorded": True, "idempotent": False, "level": level, **_truncate_for_level(enriched, level)}


# ---------- Reads ----------
async def get_trail(frek_id: str, limit: int = 50) -> dict:
    consent = await get_consent(frek_id)
    if consent.get("level", "none") == "none":
        return {"frek_id": frek_id, "consent_level": "none", "trail": []}
    cursor = db.frek_geo_observations.find(
        {"frek_id": frek_id},
        {"_id": 0, "idempotency_key": 0, "source_event_id": 0},
    ).sort("observed_at", -1).limit(limit)
    trail = await cursor.to_list(length=limit)
    # Applique le niveau de consentement
    trail = [_truncate_for_level(item, consent["level"]) for item in trail]
    return {
        "frek_id": frek_id,
        "consent_level": consent["level"],
        "trail": trail,
        "count": len(trail),
    }


async def heatmap(min_count: int = 1) -> dict:
    """Heatmap agregee par cellule H3 niveau 9 (~175m), anonyme.

    Aucun frek_id n'est expose — seulement {h3_9, count, country?}.
    """
    pipeline = [
        {"$group": {
            "_id": "$h3_9",
            "count": {"$sum": 1},
            "country_code": {"$first": "$country_code"},
        }},
        {"$match": {"count": {"$gte": min_count}}},
        {"$sort": {"count": -1}},
        {"$limit": 5000},
    ]
    cells = []
    async for doc in db.frek_geo_observations.aggregate(pipeline):
        cells.append({
            "h3_9": doc["_id"],
            "count": doc["count"],
            "country_code": doc.get("country_code"),
        })
    by_country = {}
    async for doc in db.frek_geo_observations.aggregate([
        {"$match": {"country_code": {"$ne": None}}},
        {"$group": {"_id": "$country_code", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]):
        by_country[doc["_id"]] = doc["count"]

    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    last_24h = await db.frek_geo_observations.count_documents({"observed_at": {"$gte": yesterday}})

    return {
        "timestamp": now_iso(),
        "cells": cells,
        "total_cells": len(cells),
        "by_country": by_country,
        "observations_last_24h": last_24h,
    }
