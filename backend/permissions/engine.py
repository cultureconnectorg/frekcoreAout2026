"""Permission decision engine — pure function, no I/O, no database.

`decide()` is deterministic: same DecisionRequest in, same Decision out.
Callers own persistence of RoleGrants and are expected to feed
Decision objects into backend/audit_trail/ (Priority 4) — this module does
not import audit_trail itself, keeping the two independently testable and
avoiding forcing a decision-logging dependency onto any future caller that
does not want it.
"""

from __future__ import annotations

from .models import Action, Decision, DecisionRequest, Role, Scope, ScopeType

# What each role can attempt AT ALL, before scope is checked. This is the
# "role" step of subject -> role -> scope -> resource -> action -> decision.
ROLE_CAPABILITIES: dict[Role, frozenset[Action]] = {
    Role.FOUNDER: frozenset(Action),
    Role.EXECUTIVE: frozenset(
        {
            Action.READ,
            Action.CREATE,
            Action.UPDATE,
            Action.DELETE,
            Action.VERIFY,
            Action.ISSUE,
            Action.REVOKE,
            Action.ADMINISTER,
        }
    ),
    Role.ADMIN_LABEL: frozenset(
        {Action.READ, Action.CREATE, Action.UPDATE, Action.VERIFY, Action.ISSUE}
    ),
    Role.TEACHER: frozenset({Action.READ, Action.CREATE, Action.ISSUE, Action.VERIFY}),
    Role.ARTIST: frozenset({Action.READ, Action.CREATE, Action.UPDATE, Action.VERIFY}),
    Role.STUDENT: frozenset({Action.READ}),
    Role.AGENT: frozenset({Action.READ, Action.VERIFY}),
}


def _scope_covers(scope: Scope, resource, subject_frek_id: str) -> bool:
    if scope.type == ScopeType.GLOBAL:
        return True
    if scope.type == ScopeType.ORGANIZATION:
        return (
            resource.organization_id is not None
            and resource.organization_id == scope.id
        )
    if scope.type == ScopeType.ENTITY:
        return resource.resource_id is not None and resource.resource_id == scope.id
    if scope.type == ScopeType.OBJECT:
        # "Ses oeuvres uniquement": an OBJECT-scope grant covers only
        # resources this exact subject owns, regardless of scope.id.
        return resource.owner_id is not None and resource.owner_id == subject_frek_id
    return False  # pragma: no cover - exhaustive over ScopeType


def decide(request: DecisionRequest) -> Decision:
    """Evaluate every role grant the subject holds; allow on first match.

    Grants are checked in the order they appear on the subject — callers
    that want a specific precedence (e.g. most-specific-scope-first) should
    sort `subject.roles` before calling this, since this function makes no
    ordering assumption of its own.
    """
    for grant in request.subject.roles:
        if request.action not in ROLE_CAPABILITIES.get(grant.role, frozenset()):
            continue
        if _scope_covers(grant.scope, request.resource, request.subject.frek_id):
            return Decision(
                allowed=True,
                reason=(
                    f"role={grant.role.value} scope={grant.scope.type.value} "
                    f"action={request.action.value} matched"
                ),
                matched_role=grant.role,
                matched_scope=grant.scope,
            )
    return Decision(
        allowed=False,
        reason="no role grant on this subject covers this action for this resource",
    )
