"""FREK Counter — Service de comptage universel."""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("frek.counter.service")

db = None


def set_db(database):
    global db
    db = database


# 9 sources CVLN reconnues
CVLN_SOURCES = {
    "kiltikonet":     "Presences evenements, badges, votes gouvernance",
    "kora":           "Ecoutes, streams, engagement artistes",
    "fms":            "Oeuvres publiees, droits, distributions",
    "cfa_mans":       "Formations suivies, certifications obtenues",
    "cook_food":      "Presences Gala, scores VIP, sponsors",
    "good_mood":      "Flux festivaliers, comptage souverain",
    "cvl_agro":       "Tracabilite produits, filiere certifiee",
    "cip_foundation": "Archives culturelles, memoire civilisationnelle",
    "laurent_ia":     "Interactions IA souveraines, donnees entrainement",
}

# Actions souveraines — chaque source peut emettre une ou plusieurs
DEFAULT_COUNT_RULES = [
    {"action": "PRESENCE_PASSIVE",   "base_score": 1,  "description": "comptage pur, flux passif"},
    {"action": "PRESENCE_ACTIVE",    "base_score": 5,  "description": "engagement actif verifie"},
    {"action": "PRESENCE_DIGITAL",   "base_score": 2,  "description": "presence digitale trackee"},
    {"action": "PRESENCE_KORA",      "base_score": 3,  "description": "stream KORA lance"},
    {"action": "PRESENCE_FORMATION", "base_score": 8,  "description": "formation CFA MANS demarree"},
    {"action": "PRESENCE_VOTE",      "base_score": 10, "description": "vote gouvernance CVLN"},
    {"action": "PRESENCE_OEUVRE",    "base_score": 12, "description": "oeuvre publiee/distribuee"},
    {"action": "PRESENCE_PRODUIT",   "base_score": 4,  "description": "produit CVL Agro trace"},
    {"action": "PRESENCE_ARCHIVE",   "base_score": 6,  "description": "contribution CIP Foundation"},
    {"action": "PRESENCE_IA",        "base_score": 2,  "description": "interaction Laurent.ia"},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_frek_id_from_external_ref(external_ref: str, source: str) -> str:
    """Genere un FREK-ID stable a partir d'une ref externe (kiltikonet user_id,
    KORA listener hash, etc). Reproductible — meme input -> meme FREK-ID.

    Format : FREK-{sha256(source|external_ref)[:24]}
    """
    h = hashlib.sha256(f"{source}|{external_ref}".encode()).hexdigest()
    return f"FREK-{h[:24].upper()}"


async def ensure_indexes():
    await db.frek_count_events.create_index("idempotency_key", unique=True)
    await db.frek_count_events.create_index([("frek_id", 1), ("counted_at", -1)])
    await db.frek_count_events.create_index([("source", 1), ("counted_at", -1)])
    await db.frek_count_events.create_index("action")
    await db.frek_count_subjects.create_index("frek_id", unique=True)
    await db.frek_count_rules.create_index("action", unique=True)


async def seed_rules_if_empty():
    """Seed les regles si la collection est vide. Idempotent."""
    n = await db.frek_count_rules.count_documents({})
    if n > 0:
        return 0
    seeded = 0
    for rule in DEFAULT_COUNT_RULES:
        rule = {**rule, "seeded_at": now_iso()}
        try:
            await db.frek_count_rules.insert_one(rule)
            seeded += 1
        except Exception:
            pass
    return seeded


async def get_rule(action: str) -> Optional[dict]:
    return await db.frek_count_rules.find_one({"action": action}, {"_id": 0})


async def ingest_one(
    *,
    external_ref: str,
    action: str,
    context: str,
    source: str,
    timestamp: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    if source not in CVLN_SOURCES:
        return {"recorded": False, "reason": "unknown_source"}
    rule = await get_rule(action)
    if not rule:
        return {"recorded": False, "reason": "unknown_action"}

    frek_id = stable_frek_id_from_external_ref(external_ref, source)
    counted_at = timestamp or now_iso()
    score_delta = rule["base_score"]
    key = idempotency_key or hashlib.sha256(
        f"{frek_id}|{action}|{context}|{counted_at[:13]}".encode()
    ).hexdigest()

    # Subject upsert + increment
    existing = await db.frek_count_subjects.find_one({"frek_id": frek_id}, {"_id": 0})
    created = existing is None

    # Event idempotent
    try:
        await db.frek_count_events.insert_one({
            "frek_id": frek_id,
            "action": action,
            "context": context,
            "source": source,
            "score_delta": score_delta,
            "counted_at": counted_at,
            "external_ref_hash": hashlib.sha256(external_ref.encode()).hexdigest()[:32],
            "idempotency_key": key,
        })
    except Exception as e:
        msg = str(e).lower()
        if "duplicate key" in msg or "e11000" in msg:
            return {"recorded": True, "idempotent": True, "frek_id": frek_id, "score_delta": 0}
        raise

    await db.frek_count_subjects.update_one(
        {"frek_id": frek_id},
        {
            "$setOnInsert": {"created_at": counted_at, "first_source": source},
            "$inc": {"cultural_impact_score": score_delta, "event_count": 1},
            "$set": {"last_seen": counted_at, "last_source": source},
            "$addToSet": {"sources": source, "contexts": context, "actions": action},
        },
        upsert=True,
    )

    return {
        "recorded": True,
        "idempotent": False,
        "frek_id": frek_id,
        "score_delta": score_delta,
        "created": created,
    }


async def ingest_batch(entries: list[dict]) -> dict:
    processed = 0
    created = 0
    incremented = 0
    skipped = 0
    errors = 0
    for e in entries:
        try:
            res = await ingest_one(
                external_ref=e["external_ref"],
                action=e["action"],
                context=e.get("context", "*"),
                source=e["source"],
                timestamp=e.get("timestamp"),
                idempotency_key=e.get("idempotency_key"),
            )
            processed += 1
            if not res["recorded"]:
                skipped += 1
            elif res.get("idempotent"):
                skipped += 1
            elif res.get("created"):
                created += 1
            else:
                incremented += 1
        except Exception as ex:
            logger.exception(f"counter_ingest_error: {ex}")
            errors += 1
    return {
        "processed": processed,
        "created": created,
        "incremented": incremented,
        "skipped": skipped,
        "errors": errors,
    }


async def stats_by_source() -> dict:
    """Stats agregees par source CVLN."""
    pipeline = [
        {"$group": {
            "_id": "$source",
            "events": {"$sum": 1},
            "score_total": {"$sum": "$score_delta"},
            "subjects": {"$addToSet": "$frek_id"},
        }},
        {"$project": {
            "events": 1,
            "score_total": 1,
            "subjects_count": {"$size": "$subjects"},
        }},
        {"$sort": {"events": -1}},
    ]
    out = {}
    async for d in db.frek_count_events.aggregate(pipeline):
        out[d["_id"]] = {
            "events": d["events"],
            "score_total": d["score_total"],
            "subjects": d["subjects_count"],
        }
    return out


async def average_cultural_impact_score() -> float:
    pipeline = [
        {"$group": {"_id": None, "avg": {"$avg": "$cultural_impact_score"}}},
    ]
    async for d in db.frek_count_subjects.aggregate(pipeline):
        return round(d.get("avg") or 0.0, 2)
    return 0.0
