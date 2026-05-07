"""FREK EUDI — Service flow OID4VCI pre-authorized_code.

State store : MongoDB `eudi_offers` (TTL via `expires_at` index).
"""
import logging
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("frek.eudi.service")

OFFER_TTL_SECONDS = int(os.environ.get("FREK_EUDI_OFFER_TTL", "300"))
TOKEN_TTL_SECONDS = int(os.environ.get("FREK_EUDI_TOKEN_TTL", "300"))

db = None


def set_db(database):
    global db
    db = database


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes():
    # TTL automatique : MongoDB efface les offers expirees
    await db.eudi_offers.create_index("expires_at", expireAfterSeconds=0)
    await db.eudi_offers.create_index("pre_authorized_code", unique=True)
    await db.eudi_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.eudi_tokens.create_index("access_token", unique=True)


async def create_credential_offer(frek_id: str) -> dict:
    """Genere un credential offer signe avec pre-authorized_code single-use."""
    code = secrets.token_urlsafe(32)
    expires_at = _now() + timedelta(seconds=OFFER_TTL_SECONDS)
    await db.eudi_offers.insert_one({
        "pre_authorized_code": code,
        "frek_id": frek_id,
        "consumed": False,
        "created_at": _now().isoformat(),
        "expires_at": expires_at,
    })
    return {
        "pre_authorized_code": code,
        "frek_id": frek_id,
        "expires_at": expires_at.isoformat(),
    }


async def consume_pre_authorized_code(code: str) -> Optional[dict]:
    """Echange un pre-authorized_code contre un access_token. Single-use atomique."""
    if not code:
        return None
    # Atomic find_and_modify pour single-use guarantee
    res = await db.eudi_offers.find_one_and_update(
        {"pre_authorized_code": code, "consumed": False, "expires_at": {"$gt": _now()}},
        {"$set": {"consumed": True, "consumed_at": _now().isoformat()}},
    )
    if not res:
        return None
    # Genere access_token
    access_token = secrets.token_urlsafe(32)
    token_expires = _now() + timedelta(seconds=TOKEN_TTL_SECONDS)
    await db.eudi_tokens.insert_one({
        "access_token": access_token,
        "frek_id": res["frek_id"],
        "expires_at": token_expires,
        "created_at": _now().isoformat(),
    })
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": TOKEN_TTL_SECONDS,
        "frek_id": res["frek_id"],
    }


async def resolve_token(token: str) -> Optional[str]:
    """Retourne le frek_id associe a un access_token valide, ou None."""
    if not token:
        return None
    doc = await db.eudi_tokens.find_one(
        {"access_token": token, "expires_at": {"$gt": _now()}},
        {"_id": 0, "frek_id": 1},
    )
    return doc["frek_id"] if doc else None
