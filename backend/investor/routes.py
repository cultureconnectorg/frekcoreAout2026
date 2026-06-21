"""FREK Investor — Routes /api/v1/investor/*."""
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter

from notary.routes import get_chain

logger = logging.getLogger("frek.investor.routes")

investor_router = APIRouter(prefix="/investor", tags=["FREK Investor — Due diligence cryptographique"])

db = None


def set_db(database):
    global db
    db = database


CVLN_SOURCE_IDS = [
    "kiltikonet", "kora", "fms", "cfa_mans", "cook_food",
    "good_mood", "cvl_agro", "cip_foundation", "laurent_ia",
]


async def _avg_impact_score() -> float:
    pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$cultural_impact_score"}}}]
    async for d in db.frek_count_subjects.aggregate(pipeline):
        return round(d.get("avg") or 0.0, 2)
    return 0.0


async def _chain_summary() -> dict:
    """Recupere hauteur + hash courant via FrekChain (source de verite)."""
    try:
        chain = get_chain()
        state = await chain._get_state()
        pending = await chain.blocks.count_documents({"ots_submitted": True, "btc_anchored": False})
        confirmed = state.get("total_btc_confirmed", 0)
        # Dernier block BTC ancre
        last_btc = await chain.blocks.find_one(
            {"btc_anchored": True},
            {"_id": 0, "height": 1, "block_hash": 1, "btc_block_height": 1, "btc_block_hash": 1, "anchored_at": 1},
            sort=[("height", -1)],
        )
        return {
            "height": state.get("height", 0),
            "head_hash": state.get("last_block_hash"),
            "genesis_at": state.get("genesis_at"),
            "blocks_total": state.get("total_anchored", 0),
            "blocks_bitcoin_anchored": confirmed,
            "pending_ots": pending,
            "latest_bitcoin_anchored": last_btc,
        }
    except Exception as e:
        logger.warning(f"chain_summary_failed: {e}")
        return {"height": 0, "head_hash": None, "blocks_total": 0, "blocks_bitcoin_anchored": 0, "pending_ots": 0, "latest_bitcoin_anchored": None}


@investor_router.get("/pulse")
async def investor_pulse():
    """Preuve cryptographique en temps reel — due diligence ready."""
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(hours=24)).isoformat()

    # FREK-IDs : on agrege les 2 sources de subjects (core + counter)
    core_subjects = await db.frek_subjects.count_documents({})
    counter_subjects = await db.frek_count_subjects.count_documents({})
    total_frek_ids = core_subjects + counter_subjects

    # Events totaux
    core_events = await db.frek_events.count_documents({})
    counter_events = await db.frek_count_events.count_documents({})
    total_events = core_events + counter_events

    # Sources actives (24h) — depuis counter (multi-sources CVLN)
    sources_active = await db.frek_count_events.distinct(
        "source", {"counted_at": {"$gte": yesterday}}
    )

    avg_impact = await _avg_impact_score()
    chain = await _chain_summary()

    return {
        "timestamp": now.isoformat(),
        "due_diligence": {
            "claim": "Preuve cryptographique en temps reel — pas une slide PowerPoint.",
            "verifiable_at": ["/api/v1/notary/chain/status", "/api/v1/notary/blocks", "/api/v1/notary/proof/{payload_id}"],
        },
        "ecosystem": {
            "total_frek_ids": total_frek_ids,
            "total_events": total_events,
            "sources_active": sources_active,
            "cvln_sources_declared": CVLN_SOURCE_IDS,
            "average_cultural_impact_score": avg_impact,
            "events_last_24h": await db.frek_count_events.count_documents({"counted_at": {"$gte": yesterday}}),
        },
        "frek_chain": {
            "height": chain["height"],
            "head_hash": chain["head_hash"],
            "genesis_at": chain.get("genesis_at"),
            "blocks_total": chain["blocks_total"],
            "blocks_bitcoin_anchored": chain["blocks_bitcoin_anchored"],
            "pending_ots": chain.get("pending_ots", 0),
            "latest_bitcoin_anchored": chain["latest_bitcoin_anchored"],
        },
        "audit_links": {
            "explorer": "/explorer",
            "atlas": "/atlas",
            "openapi": "/docs",
        },
    }


@investor_router.get("/sources-stats")
async def sources_stats():
    """Detail par source CVLN — chiffres bruts par entite."""
    pipeline = [
        {"$group": {
            "_id": "$source",
            "events": {"$sum": 1},
            "score_total": {"$sum": "$score_delta"},
            "first_seen": {"$min": "$counted_at"},
            "last_seen": {"$max": "$counted_at"},
            "subjects": {"$addToSet": "$frek_id"},
        }},
        {"$project": {
            "events": 1, "score_total": 1,
            "first_seen": 1, "last_seen": 1,
            "subjects_count": {"$size": "$subjects"},
        }},
        {"$sort": {"events": -1}},
    ]
    sources = {}
    async for d in db.frek_count_events.aggregate(pipeline):
        sources[d["_id"]] = {
            "events": d["events"],
            "score_total": d["score_total"],
            "subjects": d["subjects_count"],
            "first_seen": d["first_seen"],
            "last_seen": d["last_seen"],
        }
    # Inclut sources declarees mais inactives
    for sid in CVLN_SOURCE_IDS:
        if sid not in sources:
            sources[sid] = {"events": 0, "score_total": 0, "subjects": 0, "first_seen": None, "last_seen": None}
    return {"sources": sources}
