"""FREK Audit Trail — append-only record of sensitive operations (Phase 2, Priorite 4).

Distinct from `backend/audit/` (pre-existing, Phase 1 audit): that module is
a *read* aggregator producing a French-language human timeline over
`frek_stages`/`scans`/`transactions`/`notary_blocks` for the ops UI
(backend/audit/routes.py:1-8). This module is a *write* primitive — an
append-only, actor-attributed record of "who did what, was it allowed, and
why" — intended to sit underneath the Permission Engine's decisions
(backend/permissions/) and any other sensitive operation. The two modules
solve different problems and are kept separate rather than merged into the
existing `audit/` package, matching this codebase's own pattern of naming
distinct modules for distinct concepts (e.g. `event/` vs the new
`registry/events/`).

Not wired into any existing route in this phase — see
reports/12_PHASE2_IMPLEMENTATION.md.
"""

from .models import AuditEvent
from .recorder import AuditRecorder, InMemoryAuditRecorder

__all__ = ["AuditEvent", "AuditRecorder", "InMemoryAuditRecorder"]
