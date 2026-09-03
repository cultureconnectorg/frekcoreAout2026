"""FREK-Chain integrity watchdog.

Historical P1 finding (memory/RESILIENCE_REPORT_v1.0.md, Sprint G, test 3
section 5.2 "Ce qui manque encore" + section 7 P1#4): `notary/chain.py`'s
`verify_chain()` detects tampering precisely (exact block height, ~200ms
over 1311 blocks) but was, at the time of that report, only ever invoked
on demand via `GET /notary/chain/status` / `/chain/verify` — a corrupted
block left no trace and raised no alert unless someone happened to call
those endpoints. The report's own words: "le verificateur n'est appele
QUE lorsqu'on hit /chain/verify. Il devrait etre execute periodiquement
(toutes les 6h par le scheduler) et pousser une alerte si valid=false" —
and named the concrete deliverable: `chain_watchdog.py` checking every 6h,
writing to `security_events` with severity `critical` on failure.

This module is the daemon that closes that gap. It adds no new proof or
verification logic of its own — `FrekChain.verify_chain()` (already
tested, already used by `/notary/chain/verify`) remains the single source
of truth for chain integrity; this module only calls it periodically and
reports the result via `security.policies.record_anomaly`, the same
anomaly-trail convention already used for rate-limit hits and staff
lockouts.
"""

import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger("frek.notary.chain_watchdog")

DEFAULT_INTERVAL_SECONDS = 6 * 3600  # "toutes les 6h" per the report


async def check_once(
    chain, record_anomaly: Callable, limit: Optional[int] = None
) -> dict:
    """Run one integrity pass over the FREK-Chain and report the result.

    Never raises: a check failure (e.g. a transient DB error) is logged
    and reported as its own anomaly rather than crashing the caller —
    the watchdog itself must never become a new availability risk to the
    rest of the system (same "never raises" convention as
    notary/service.py's notarize_event).
    """
    try:
        result = await chain.verify_chain(limit=limit)
    except Exception as e:
        logger.exception(f"chain_watchdog: verify_chain() raised: {e}")
        await record_anomaly(
            kind="chain_watchdog_check_failed",
            scope="frek_chain",
            severity="critical",
            details={"error": str(e)},
        )
        return {"valid": False, "reason": "verify_chain_exception", "error": str(e)}

    if not result.get("valid", False):
        logger.critical(
            "chain_watchdog: INTEGRITY VIOLATION detected — "
            f"first_invalid_height={result.get('first_invalid_height')} "
            f"reason={result.get('reason')}"
        )
        await record_anomaly(
            kind="chain_integrity_violation",
            scope="frek_chain",
            severity="critical",
            details=result,
        )
    else:
        logger.info(
            f"chain_watchdog: OK, blocks_checked={result.get('blocks_checked')}"
        )
    return result


async def watchdog_loop(
    chain,
    record_anomaly: Callable,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    limit: Optional[int] = None,
) -> None:
    """Periodic supervisor: `check_once` every `interval_seconds`, forever.

    Intended to be started once via `asyncio.create_task(...)` from an
    app startup hook (see server.py) and left running for the life of the
    process — it never returns on its own. A single failed iteration
    (network blip, transient Mongo error) is caught inside `check_once`
    and does not stop the loop; the next 6h cycle still runs.
    """
    logger.info(f"chain_watchdog: starting, interval={interval_seconds}s")
    while True:
        await check_once(chain, record_anomaly, limit=limit)
        await asyncio.sleep(interval_seconds)
