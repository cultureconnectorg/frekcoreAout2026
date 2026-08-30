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
