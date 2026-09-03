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

from .engine import _scope_covers, decide
from .models import (
    Action,
    Decision,
    DecisionRequest,
    DelegationGrant,
    ResourceRef,
    Subject,
)


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


def delegation_authority_chain_valid(
    grant: DelegationGrant,
    *,
    delegator_subject: Subject,
    delegate_frek_id: str,
    action: Action,
    resource: ResourceRef,
    now_iso: str,
) -> Decision:
    """STATE_8 — the full chain check `delegation_permits()` deliberately
    leaves to the caller (see its own docstring): does `delegator_subject`
    actually hold, RIGHT NOW, the role/scope it purports to have delegated?

    Composes the two existing pure functions rather than inventing a
    third authority resolution: `delegation_permits()` (does the grant
    itself cover this delegate/action/resource/window) AND
    `permissions.engine.decide()` (does the delegator's own current
    RoleGrants justify this action on this resource). Both are required.
    `NO_PARALLEL_AUTHORITY_ENGINE=TRUE` -- this function owns no
    authority vocabulary of its own.

    Revocation-propagation policy (STATE_8, deliberate): the delegate's
    authority is bounded by the delegator's CURRENT authority, not a
    snapshot taken at grant-creation time. If the delegator's role/scope
    has since been removed or narrowed on `delegator_subject.roles` --
    including via revocation -- `decide()` naturally returns
    `allowed=False` for it, and the delegated authority is invalid too,
    even if the `DelegationGrant` record itself was never separately
    marked `revoked_at`. Canonical persistence of `Subject.roles`
    (removing/expiring a `RoleGrant` on revocation) is what makes this
    policy take effect in practice; this function only requires that the
    caller pass the delegator's current state, exactly as `decide()`
    already requires for any other authority check.
    """
    if delegator_subject.frek_id != grant.delegator_frek_id:
        return Decision(
            allowed=False,
            reason="delegator_subject does not match this grant's delegator_frek_id",
        )
    if not delegation_permits(
        grant,
        delegate_frek_id=delegate_frek_id,
        action=action,
        resource=resource,
        now_iso=now_iso,
    ):
        return Decision(
            allowed=False,
            reason="delegation grant itself does not cover this request "
            "(revoked, expired, wrong delegate, unsupported action, or "
            "outside the grant's scope/resource boundary)",
        )
    delegator_decision = decide(
        DecisionRequest(subject=delegator_subject, action=action, resource=resource)
    )
    if not delegator_decision.allowed:
        return Decision(
            allowed=False,
            reason=f"delegator lacks current originating authority: {delegator_decision.reason}",
        )
    return Decision(
        allowed=True,
        reason="delegation grant valid and delegator holds current originating authority "
        f"(role={delegator_decision.matched_role})",
        matched_role=delegator_decision.matched_role,
        matched_scope=delegator_decision.matched_scope,
    )
