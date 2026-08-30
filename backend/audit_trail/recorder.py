"""AuditRecorder — the append-only write surface.

`InMemoryAuditRecorder` is the only implementation in this phase (process
memory, cleared on restart) — a MongoDB-backed one (append-only collection,
no update/delete route ever exposed) is the natural next step once this is
wired into real routes, but that requires the database access this module
deliberately does not have (kept unit-testable without MongoDB, matching
backend/registry/ and backend/eventbus/).

Append-only is enforced by the *shape* of this class, not by a runtime
check: there is no `update`, `delete`, or `clear` method anywhere on
`AuditRecorder` or `InMemoryAuditRecorder`, and `all_events()` returns an
immutable `tuple`. A standard caller — including a future route handler —
has no method available to alter or remove a past entry.
"""

from __future__ import annotations

from typing import List, Protocol

from .models import AuditEvent


class AuditRecorder(Protocol):
    def record(self, event: AuditEvent) -> AuditEvent: ...

    def all_events(self) -> tuple[AuditEvent, ...]: ...


class InMemoryAuditRecorder:
    """Append-only: record() adds, all_events() reads. Nothing removes or edits."""

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def record(self, event: AuditEvent) -> AuditEvent:
        self._events.append(event)
        return event

    def all_events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)
