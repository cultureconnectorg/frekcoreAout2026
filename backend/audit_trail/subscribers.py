"""Event Bus -> Audit Trail bridge (Phase 3, Priority 5).

Turns any `EventEnvelope` published on `backend/eventbus`'s bus into an
`AuditEvent`, written through a `MongoAuditRecorder`. This is how audit
trail wiring is added *without* touching any route a second time: a
producer that already publishes an event (e.g. `identity.created`, wired
Phase 2 in `backend/identity_engine/routes.py`) gets an audit trail entry
for free once this subscriber is registered on the same bus at startup —
see `backend/server.py`'s `_wire_audit_trail_subscribers()`.

`InProcessEventBus.publish()` (backend/eventbus/bus.py) calls subscribers
synchronously and catches any exception so a broken subscriber can never
break the publisher — this subscriber schedules the actual (async) Mongo
write via `asyncio.create_task`, matching that same non-blocking contract:
a slow or failing audit write can never delay or break whatever route
published the event.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from eventbus.envelope import EventEnvelope

from .mongo_recorder import MongoAuditRecorder
from .models import AuditEvent

logger = logging.getLogger("frek.audit_trail.subscribers")


def event_envelope_to_audit_event(
    envelope: EventEnvelope, *, result: str = "success"
) -> AuditEvent:
    """Pure mapping — no I/O, unit-testable without a database or event loop."""
    payload: Dict[str, Any] = envelope.payload or {}
    return AuditEvent(
        actor_frek_id=envelope.subject,
        request_id=None,
        correlation_id=envelope.correlation_id,
        timestamp=envelope.occurred_at,
        action=envelope.event_type,
        resource_type=envelope.producer,
        resource_id=envelope.subject,
        result=result,  # type: ignore[arg-type]
        reason=None,
        metadata={"event_id": envelope.event_id, "payload": payload},
    )


def make_audit_trail_subscriber(recorder: MongoAuditRecorder):
    """Returns a sync EventSubscriber (matches backend/eventbus/bus.py's
    `EventSubscriber` protocol) that schedules an async audit write."""

    def _subscriber(envelope: EventEnvelope) -> None:
        audit_event = event_envelope_to_audit_event(envelope)

        async def _write() -> None:
            try:
                await recorder.record(audit_event)
            except Exception:
                logger.warning(
                    "audit trail write failed for event_id=%s event_type=%s (non-blocking)",
                    envelope.event_id,
                    envelope.event_type,
                    exc_info=True,
                )

        try:
            asyncio.get_running_loop().create_task(_write())
        except RuntimeError:
            # No running loop (e.g. called from a sync test) — best-effort, skip.
            logger.warning(
                "audit trail write skipped for event_id=%s: no running event loop",
                envelope.event_id,
            )

    return _subscriber
