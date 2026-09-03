"""STATE_6 — Historical Compatibility Reconciliation: shared hardening
helpers for `backend/frek/`'s 19 historical routes.

Founder rule (`FREKCORE_EXECUTION_PROTOCOL_V1` STATE_6, 2026-09-02):
legacy routes remain — interface and, largely, implementation — but
receive safety controls (rate limiting, audit visibility) without their
semantics being silently upgraded into canonical claims
(HARDEN, per the mission's own disposition vocabulary). This module is
the ONE shared implementation of those controls so `frek/routes.py` and
`frek/routes_advanced.py` do not each invent their own copy
(REUSE_BEFORE_BUILD=TRUE) — full record: `docs/architecture/
FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`.

Two rules this module exists to enforce structurally:

- **No separate throttling infrastructure.** `legacy_rate_limit_ok`
  goes through the exact same `security.policies.check_rate_limit`
  every canonical D-state route already uses (`legacy_frek_read`/
  `legacy_frek_write`, defined alongside every other rate-limit key in
  `security/policies.py`), never a second rate-limit mechanism.
- **No event duplication.** `publish_legacy_invocation` publishes
  `legacy_route.invoked` — a single, shared, non-business event whose
  only job is audit visibility ("this legacy route ran"). It is never
  published alongside a canonical business event for the same call: a
  legacy route that also successfully drives a canonical write (D3's
  `/reseau/node/{id}` canonical cross-reference, D4's watermark reuse)
  still publishes only the canonical module's own event where one
  exists — `publish_legacy_invocation` is called only for the legacy
  route's own historical-path execution, never duplicated for a
  canonical side-call. `detail` must never carry raw request payload
  content (audio bytes, sha256 signal, GPS coordinates, artiste_id) —
  only coarse, non-sensitive compatibility metadata (route path,
  canonical target module name, outcome) — enforced by convention at
  every call site in `routes.py`/`routes_advanced.py`, not by this
  module inspecting payloads it has no way to classify generically.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from security.policies import check_rate_limit

logger = logging.getLogger("frek.legacy_compat")


async def legacy_rate_limit_ok(*, scope: str, write: bool) -> bool:
    """Returns True if allowed. `scope` should be the most specific
    non-sensitive identifier available (a frek_id/node_id/artiste_id
    string) — matching the exact convention `fingerprint/routes.py` and
    `geo/routes.py` already use for their own unauthenticated,
    historically-zero-rate-limit routes (`scope=frek_id`), not a new
    scoping convention invented here."""
    action = "legacy_frek_write" if write else "legacy_frek_read"
    return await check_rate_limit(scope=scope, action=action)


async def publish_legacy_invocation(
    *,
    legacy_route: str,
    canonical_target: str,
    outcome: str,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """Best-effort, never-blocking — same convention as every D-state's
    own `_publish_and_notarize`: a broken event bus can never break a
    legacy route's own historical behavior."""
    try:
        from eventbus.bus import default_bus
        from eventbus.producers import build_legacy_route_invoked_event

        default_bus.publish(
            build_legacy_route_invoked_event(
                legacy_route=legacy_route,
                canonical_target=canonical_target,
                outcome=outcome,
                detail=detail or {},
            )
        )
    except Exception:
        logger.warning(
            "legacy_route.invoked publish failed (non-blocking)", exc_info=True
        )
