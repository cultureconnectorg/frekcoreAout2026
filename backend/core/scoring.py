"""FREK Core — Scoring autoritaire (Cultural Impact Score).

Chargement depuis MongoDB (frek_scoring_rules). Cache 60s pour eviter de poller
a chaque ingest, sans introduire de complexite distribuee.

INVARIANT : le Cultural Impact Score est calcule exclusivement par FrekCore.
Aucune source externe ne peut imposer un score.
"""
import asyncio
import logging
import time
from typing import Optional

from .models import DEFAULT_SCORING_RULES

logger = logging.getLogger("frek.core.scoring")

CACHE_TTL = 60.0

db = None
_cache: Optional[dict] = None
_cached_at: float = 0.0
_lock = asyncio.Lock()


def set_db(database):
    global db
    db = database


async def seed_default_rules_if_empty():
    """Au premier demarrage, seed les regles par defaut si la collection est vide.

    Idempotent : si la collection contient deja des regles, ne fait rien.
    L'admin peut ensuite editer librement sans craindre un re-seed.
    """
    count = await db.frek_scoring_rules.count_documents({})
    if count > 0:
        return
    if not DEFAULT_SCORING_RULES:
        return
    await db.frek_scoring_rules.insert_many(list(DEFAULT_SCORING_RULES))
    logger.info(f"FREK Core — seeded {len(DEFAULT_SCORING_RULES)} scoring rules")


async def _load_rules() -> dict:
    """Charge toutes les regles et les indexe par (event_type, context) et badge_type."""
    rules = await db.frek_scoring_rules.find({}, {"_id": 0}).to_list(length=None)
    by_event = {}      # (event_type, context_or_None) -> base_score
    by_badge = {}      # badge_type -> bonus_score
    for r in rules:
        if "base_score" in r and r.get("event_type"):
            key = (r["event_type"], r.get("context"))
            by_event[key] = r["base_score"]
        if "bonus_score" in r and r.get("badge_type"):
            by_badge[r["badge_type"]] = r["bonus_score"]
    return {"by_event": by_event, "by_badge": by_badge}


async def get_rules(force_refresh: bool = False) -> dict:
    """Renvoie le bundle de regles, avec cache TTL."""
    global _cache, _cached_at
    now = time.monotonic()
    if not force_refresh and _cache is not None and (now - _cached_at) < CACHE_TTL:
        return _cache
    async with _lock:
        if not force_refresh and _cache is not None and (time.monotonic() - _cached_at) < CACHE_TTL:
            return _cache
        _cache = await _load_rules()
        _cached_at = time.monotonic()
        return _cache


async def compute_score_delta(action: str, event_id: Optional[str], badge_type: Optional[str]) -> int:
    """Calcule score_delta = base(action, context=event_id) + bonus(badge_type).

    Si aucune regle ne matche, score_delta = 0 (l'evenement est quand meme enregistre).
    """
    rules = await get_rules()
    # Cherche d'abord (action, event_id), puis (action, None)
    base = rules["by_event"].get((action, event_id), rules["by_event"].get((action, None), 0))
    bonus = rules["by_badge"].get(badge_type, 0) if badge_type else 0
    return int(base) + int(bonus)


def invalidate_cache():
    """Forcer le rechargement au prochain appel (utile pour tests)."""
    global _cache, _cached_at
    _cache = None
    _cached_at = 0.0
