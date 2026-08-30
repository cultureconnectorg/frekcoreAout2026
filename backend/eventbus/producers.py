"""Pure event-construction helpers, kept separate from route handlers.

Splitting "build the envelope" (pure, unit-testable, no I/O) from "publish
it" (a side effect) lets Phase 2's one real producer (identity.created, see
backend/identity_engine/routes.py) be verified by a unit test without a
live server or MongoDB — see backend/tests/test_eventbus.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .envelope import EventEnvelope


def build_identity_created_event(
    identity: Dict[str, Any], correlation_id: Optional[str] = None
) -> EventEnvelope:
    """Build the `identity.created` event for a freshly created FREKIdentity.

    `identity` is the same dict inserted into `db.frek_persons` by
    backend/identity_engine/routes.py:init_identity — this function does not
    touch the database itself, so it can be unit-tested with a plain dict.
    """
    return EventEnvelope(
        event_type="identity.created",
        producer="identity_engine",
        subject=identity["frek_id"],
        correlation_id=correlation_id,
        payload={
            "frek_id": identity["frek_id"],
            "identity_type": identity.get("identity_type"),
            "status": identity.get("status"),
            "created_at": identity.get("created_at"),
        },
        schema_version="1.0.0",
    )
