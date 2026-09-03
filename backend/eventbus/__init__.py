"""FREK Event Bus abstraction (Bloc 7 / Phase 2 Priorite 5).

Deliberately NOT Kafka/RabbitMQ/a distributed broker. This is a small,
typed, in-process publish/subscribe abstraction that a future external
broker adapter can implement against the same `EventPublisher` protocol
without changing any producer's code — see `bus.py`'s docstring.

Nothing in this package is wired into any existing route by default. See
`backend/eventbus/producers.py` for the one real producer wired in this
phase (identity.created) and reports/12_PHASE2_IMPLEMENTATION.md for why
only that one was connected.
"""

from .envelope import EventEnvelope
from .bus import EventPublisher, EventSubscriber, InProcessEventBus, default_bus

__all__ = [
    "EventEnvelope",
    "EventPublisher",
    "EventSubscriber",
    "InProcessEventBus",
    "default_bus",
]
