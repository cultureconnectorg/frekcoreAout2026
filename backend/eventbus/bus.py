"""EventPublisher / EventSubscriber protocols + an in-process implementation.

Design intent (Phase 2 Priorite 5): the *interface* is the deliverable, not
the transport. `InProcessEventBus` is the only implementation today because
FREKCORE is a single-process FastAPI monolith (see reports/03_ARCHITECTURE_MAP.md)
— there is no other process to route events to yet. A future Kafka/RabbitMQ/
SNS adapter can implement `EventPublisher` with the exact same method
signature and every existing producer keeps working unchanged.

Subscribers are called synchronously, in registration order, inside
`publish()`. A subscriber that raises is caught and logged, never allowed to
break the producer's request — publishing an event must never be able to
fail the operation that triggered it (the same defensive posture already
used for notarization in backend/frek_v1/stages.py:10-14).
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Protocol

from .envelope import EventEnvelope

logger = logging.getLogger("frek.eventbus")


class EventSubscriber(Protocol):
    """Anything callable with an EventEnvelope is a valid subscriber."""

    def __call__(self, envelope: EventEnvelope) -> None: ...


class EventPublisher(Protocol):
    """The contract a broker adapter must implement to replace InProcessEventBus."""

    def publish(self, envelope: EventEnvelope) -> None: ...

    def subscribe(self, event_type: str, subscriber: EventSubscriber) -> None: ...


class InProcessEventBus:
    """The only EventPublisher implementation shipped in this phase."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[EventEnvelope], None]]] = {}
        self._published: List[EventEnvelope] = []

    def subscribe(self, event_type: str, subscriber: EventSubscriber) -> None:
        self._subscribers.setdefault(event_type, []).append(subscriber)

    def publish(self, envelope: EventEnvelope) -> None:
        self._published.append(envelope)
        for subscriber in self._subscribers.get(envelope.event_type, []):
            try:
                subscriber(envelope)
            except Exception:
                logger.exception(
                    "event subscriber failed for %s (event_id=%s) — publisher call site is unaffected",
                    envelope.event_type,
                    envelope.event_id,
                )

    def published_events(self) -> tuple[EventEnvelope, ...]:
        """Read-only history — for tests and local debugging only, not a durable log.

        This is NOT the Audit Trail (backend/audit_trail/): it holds no
        actor/decision information and is cleared on process restart. See
        backend/audit_trail/ for the append-only, actor-attributed record.
        """
        return tuple(self._published)


# Process-wide default instance. Producers import this rather than
# constructing their own bus, so all in-process subscribers see all events.
# Tests should construct their own InProcessEventBus() to stay isolated.
default_bus = InProcessEventBus()
