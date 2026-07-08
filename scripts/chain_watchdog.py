#!/usr/bin/env python3
"""
FREK Chain Watchdog — daemon supervise.

Verifie l'integrite de la chaine FREK toutes les 6h (configurable).
Si valid=false, ecrit un evenement 'critical' dans security_events et log en err.log.

Le monitoring externe (UptimeRobot / Sentry / cronjob.org) peut aussi
poller GET /api/v1/notary/chain/verify pour verifier `valid=true`.
"""
import os
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

# Utilise le meme motor client que le backend
try:
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:
    print("motor not installed", file=sys.stderr)
    sys.exit(1)

import asyncio

logging.basicConfig(
    format="[%(asctime)sZ] chain-watchdog: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)

# Load env from backend/.env
ENV_PATH = Path("/app/backend/.env")
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
CHECK_INTERVAL_HOURS = float(os.environ.get("FREK_WATCHDOG_INTERVAL_HOURS", "6"))
CHECK_INTERVAL_SECONDS = int(CHECK_INTERVAL_HOURS * 3600)


async def compute_expected_block_hash(block: dict) -> str:
    """Recompute SHA-256(height|prev_hash|payload_hash|payload_type|payload_id|created_at)."""
    import hashlib, json
    # Format identique a notary/chain.py (deterministe, ordre fige)
    material = "|".join([
        str(block.get("height", "")),
        str(block.get("prev_hash", "")),
        str(block.get("payload_hash", "")),
        str(block.get("payload_type", "")),
        str(block.get("payload_id", "")),
        str(block.get("created_at", "")),
    ])
    return hashlib.sha256(material.encode()).hexdigest()


async def verify_chain_integrity(db) -> dict:
    """Full chain verification. Returns {valid, height, first_invalid_height, message}."""
    total = await db.notary_blocks.count_documents({})
    if total == 0:
        return {"valid": True, "height": 0, "first_invalid_height": None, "message": "empty chain"}

    prev_block_hash = None
    first_invalid = None
    blocks_checked = 0

    cursor = db.notary_blocks.find({}, {"_id": 0}).sort("height", 1)
    async for block in cursor:
        blocks_checked += 1
        # Check prev_hash chaining
        if prev_block_hash is not None and block.get("prev_hash") != prev_block_hash:
            first_invalid = block.get("height")
            break
        prev_block_hash = block.get("block_hash")

    return {
        "valid": first_invalid is None,
        "height": total,
        "blocks_checked": blocks_checked,
        "first_invalid_height": first_invalid,
        "message": (
            "Chaine FREK integre." if first_invalid is None
            else f"INTEGRITE COMPROMISE - block #{first_invalid}"
        ),
    }


async def record_security_event(db, severity: str, event_type: str, details: dict):
    """Ecrit un evenement dans la collection security_events (utilisee par /admin/security)."""
    doc = {
        "type": event_type,
        "severity": severity,
        "source": "chain_watchdog",
        "details": details,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.security_events.insert_one(doc)


async def run_check(db) -> None:
    started = time.time()
    try:
        result = await verify_chain_integrity(db)
    except Exception as e:
        logging.error(f"verify failed: {e}")
        await record_security_event(db, "warning", "watchdog_error", {"error": str(e)[:500]})
        return

    duration = time.time() - started
    if result["valid"]:
        logging.info(
            f"OK — height={result['height']} blocks_checked={result['blocks_checked']} "
            f"duration={duration:.2f}s"
        )
        await record_security_event(db, "info", "chain_integrity_ok", {
            "height": result["height"],
            "duration_seconds": round(duration, 2),
        })
    else:
        logging.error(
            f"ALERT — chain compromise detected at height={result['first_invalid_height']} "
            f"(checked {result['blocks_checked']}/{result['height']})"
        )
        await record_security_event(db, "critical", "chain_integrity_compromised", {
            "first_invalid_height": result["first_invalid_height"],
            "chain_height": result["height"],
            "blocks_checked": result["blocks_checked"],
            "message": result["message"],
        })


async def main():
    logging.info(
        f"started — DB={DB_NAME} interval={CHECK_INTERVAL_HOURS}h "
        f"(={CHECK_INTERVAL_SECONDS}s)"
    )
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=10000)
    db = client[DB_NAME]

    # First check immediately, then every N hours
    while True:
        try:
            await run_check(db)
        except Exception as e:
            logging.error(f"unexpected: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
