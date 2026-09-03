"""FREK Audit Trail — append-only record of sensitive operations.

Phase 2: `AuditEvent` model + `InMemoryAuditRecorder` (dev/test).
Phase 3 (Priority 5): `MongoAuditRecorder` (real, append-only MongoDB
collection) + `make_audit_trail_subscriber` (bridges the Event Bus,
built Phase 2, to this recorder — see `subscribers.py`'s docstring for how
this lets an already-published event become an audit entry with zero
additional route changes).

Distinct from `backend/audit/` (pre-existing, Phase 1 audit): that module
is a *read* aggregator producing a French-language human timeline over
`frek_stages`/`scans`/`transactions`/`notary_blocks` for the ops UI
(backend/audit/routes.py:1-8). This module is a *write* primitive — an
append-only, actor-attributed record of "who did what, was it allowed, and
why". The two modules solve different problems and are kept separate,
matching this codebase's own pattern of naming distinct modules for
distinct concepts.

Wired into `backend/server.py` for `identity.created` only this phase — see
`reports/19_PERMISSION_ENFORCEMENT.md` / `reports/20_EVENT_PRODUCERS.md`
for why not more.
"""

from .models import AuditEvent
from .recorder import AuditRecorder, InMemoryAuditRecorder
from .mongo_recorder import MongoAuditRecorder
from .subscribers import make_audit_trail_subscriber, event_envelope_to_audit_event

__all__ = [
    "AuditEvent",
    "AuditRecorder",
    "InMemoryAuditRecorder",
    "MongoAuditRecorder",
    "make_audit_trail_subscriber",
    "event_envelope_to_audit_event",
]
