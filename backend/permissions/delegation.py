"""STATE_7 — Delegated Authority: pure containment check.

`delegation_permits()` answers exactly one question: does this
`DelegationGrant` cover this requested action, on this resource, right
now? It is a pure function over already-loaded objects (no persistence,
no route) — same discipline as `permissions.engine.decide()`.

The one invariant this module exists to enforce structurally, not just
in prose: **a delegate can never be granted more than the grant's own
scope/actions/resource/validity window already contains.** This function
only ever narrows a decision, never widens one — it cannot itself
manufacture authority the grant does not already state. Whether the
*delegator* actually held that authority in the first place (i.e. does
`delegator_frek_id` really have a `RoleGrant` covering `scope`?) is a
separate, deliberate omission: this function takes the `DelegationGrant`
as given, exactly like `permissions.engine.decide()` takes
`subject.roles` as given — validating that the delegator's own
`RoleGrant`s actually justify the grant they extended is the caller's
job (reusing `permissions.engine.decide()` for that check), not
reinvented here as a second, competing authority resolution.
"""

from __future__ import annotations

from .engine import _scope_covers
from .models import Action, DelegationGrant, ResourceRef


def delegation_permits(
    grant: DelegationGrant,
    *,
    delegate_frek_id: str,
    action: Action,
    resource: ResourceRef,
    now_iso: str,
) -> bool:
    """True only if `grant` is currently valid, addressed to
    `delegate_frek_id`, covers `action`, and covers `resource` under its
    own `scope` (and, if set, its own narrower `resource` boundary)."""
    if grant.delegate_frek_id != delegate_frek_id:
        return False
    if grant.revoked_at is not None:
        return False
    if now_iso < grant.valid_from:
        return False
    if grant.valid_until is not None and now_iso > grant.valid_until:
        return False
    if action not in grant.actions:
        return False
    if not _scope_covers(grant.scope, resource, grant.delegator_frek_id):
        return False
    if grant.resource is not None:
        if grant.resource.resource_type != resource.resource_type:
            return False
        if (
            grant.resource.resource_id is not None
            and grant.resource.resource_id != resource.resource_id
        ):
            return False
    return True
