"""Permission Engine — typed vocabulary (Bloc 6, Phase 2 Priorite 3).

subject -> role -> scope -> resource -> action -> decision, exactly as
specified in the mission brief. Roles, scopes and actions are the closed
vocabularies the brief names; nothing here encodes Wallet, KORA or Academy
business rules — `ResourceRef.resource_type` is a free-form string so those
systems can describe their own resources without FREKCORE knowing about
them.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    """CVLN-wide roles, per the mission brief's table."""

    FOUNDER = "founder"  # Tous les systemes
    EXECUTIVE = "executive"  # Entite specifique
    ARTIST = "artist"  # Ses oeuvres uniquement
    STUDENT = "student"  # Academy
    TEACHER = "teacher"  # Academy + Certificates
    ADMIN_LABEL = "admin_label"  # LabelOS
    AGENT = "agent"  # Permissions limitees


class ScopeType(str, Enum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    ENTITY = "entity"
    OBJECT = "object"


class Action(str, Enum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VERIFY = "verify"
    ISSUE = "issue"
    REVOKE = "revoke"
    ADMINISTER = "administer"


class Scope(BaseModel):
    """What a role grant covers.

    `id` is required for every scope type except GLOBAL: an ORGANIZATION
    scope's `id` is an organization FREK-ID, an ENTITY scope's `id` is that
    entity's FREK-ID, and an OBJECT scope has no `id` at all — it instead
    means "resources this subject owns" (see engine.py — this is how
    `Role.ARTIST`'s "ses oeuvres uniquement" is expressed).
    """

    type: ScopeType
    id: Optional[str] = None


class RoleGrant(BaseModel):
    role: Role
    scope: Scope
    granted_at: str
    granted_by: Optional[str] = None


class Subject(BaseModel):
    """The identity a decision is being made about — always a FREK-ID."""

    frek_id: str
    roles: list[RoleGrant] = Field(default_factory=list)


class ResourceRef(BaseModel):
    """The thing an action is being attempted against.

    `resource_type` is intentionally a free-form string (e.g. a FREK
    Registry namespace like 'frek.artist', or any other system's own
    resource name) rather than a closed enum — this engine does not need to
    know what KORA or Academy resources look like to decide access to them.
    """

    resource_type: str
    resource_id: Optional[str] = None
    organization_id: Optional[str] = None
    owner_id: Optional[str] = None


class DecisionRequest(BaseModel):
    subject: Subject
    action: Action
    resource: ResourceRef


class Decision(BaseModel):
    allowed: bool
    reason: str
    matched_role: Optional[Role] = None
    matched_scope: Optional[Scope] = None


# ---------------------------------------------------------------------------
# STATE_7 (API/SDK Contract Stabilization, 2026-09-03) — Service Identity &
# Delegated Authority contract (`docs/architecture/
# FREKCORE_VERSIONING_POLICY.md` §9). Pure data + pure logic only: no
# persistence, no route, not wired into any live endpoint this state
# (matching `RoleGrant`'s own long-standing status — zero live callers
# anywhere in this codebase, confirmed repeatedly through D3/STATE_6).
# Reuses `Scope`/`Action`/`ResourceRef` directly, never a lookalike
# vocabulary (`NO_PARALLEL_AUTHORITY_ENGINE=TRUE`) — this is the
# "implement only what is required to make the integration contract
# coherent if missing" piece the founder's own STATE_7 mission asked for,
# not a new IAM product: a `ServiceIdentity` credential is an opaque
# reference (`credential_ref`), never key material itself, matching every
# other credential-adjacent model in this codebase (`DeviceAttestation`,
# `Credential`).
# ---------------------------------------------------------------------------


class ServiceIdentity(BaseModel):
    """A non-human caller (a CVLN system, an agent) — the "service_id /
    organization owner / credential / allowed scopes / expiry /
    revocation" list the STATE_7 mission names, expressed with existing
    `Scope` types rather than a new vocabulary."""

    service_id: str
    owner: ResourceRef = Field(
        ..., description="The organization/entity this service identity belongs to."
    )
    credential_ref: Optional[str] = Field(
        None,
        description=(
            "Opaque reference to whatever credential backs this identity "
            "(e.g. a passport/DID key id) -- never the key material itself."
        ),
    )
    allowed_scopes: list[Scope] = Field(default_factory=list)
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None

    def is_active(self, *, now_iso: str) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and now_iso >= self.expires_at:
            return False
        return True


class DelegationGrant(BaseModel):
    """One entity authorizing another (a service identity or another
    subject) to act on its behalf, within a bounded scope/action/resource
    window -- e.g. "KORA may submit an event for this creator only", "the
    Agent Factory may invoke FREKCORE only within these delegated
    scopes". `delegate` can never be granted more than this grant's own
    scope/actions/resource/window state -- enforced by
    `permissions.delegation.delegation_permits()`, not by this model
    alone. That check alone does not prove `delegator` ever actually
    held the authority it delegated; STATE_8 added
    `permissions.delegation.delegation_authority_chain_valid()`, which
    composes `delegation_permits()` with `permissions.engine.decide()`
    against the delegator's own current RoleGrants for that (a model
    cannot see the delegator's actual RoleGrants; the pure functions
    do, given both)."""

    grant_id: str
    delegator_frek_id: str = Field(
        ...,
        description="The Subject.frek_id or ServiceIdentity.service_id delegating authority.",
    )
    delegate_frek_id: str = Field(
        ...,
        description="The Subject.frek_id or ServiceIdentity.service_id receiving it.",
    )
    scope: Scope
    actions: list[Action] = Field(default_factory=list)
    resource: Optional[ResourceRef] = Field(
        None,
        description="Optional boundary narrower than `scope` -- e.g. one specific object, not the whole scope.",
    )
    valid_from: str
    valid_until: Optional[str] = None
    revoked_at: Optional[str] = None
    proof_reference: Optional[str] = Field(
        None,
        description=(
            "Opaque reference to whatever backs this grant "
            "(credential_id/envelope_id/...), never the proof material itself."
        ),
    )
