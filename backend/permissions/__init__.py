"""FREK Permission Engine — model only (Phase 2, Priorite 3).

This package defines the CVLN-wide permission vocabulary the mission asked
for (subject -> role -> scope -> resource -> action -> decision) as a typed,
pure, unit-testable module. It is deliberately NOT wired into any existing
route in this phase — see reports/12_PHASE2_IMPLEMENTATION.md for the
explicit reasoning: backend/frek_v1/auth.py's flat-permission-string model
(reports/05_SECURITY_REPORT.md) is what every existing route actually
depends on today, and replacing it live, without a way to run the 335
integration tests in this sandbox (reports/10_TEST_INFRASTRUCTURE.md), would
risk locking out real API clients with no way to verify the blast radius.
This module is the foundation the next phase wires in, not a live cutover.

P2 (2026-08-31): `protocol_roles.py` adds `ProtocolRole` (Issuer/Holder/
Verifier, the W3C VC Data Model's roles) plus its documented mapping to
this module's own `Role` vocabulary — connecting a gap named in
`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s Credentials section.
See that file's own docstring for why this is a typed reference point,
not new enforceable `Role` values.
"""

from .models import (
    Action,
    Decision,
    DecisionRequest,
    DelegationGrant,
    ResourceRef,
    Role,
    RoleGrant,
    Scope,
    ScopeType,
    ServiceIdentity,
    Subject,
)
from .engine import ROLE_CAPABILITIES, decide
from .delegation import delegation_permits
from .protocol_roles import (
    PROTOCOL_ROLE_TO_CVLN_ROLE,
    ProtocolRole,
    cvln_role_for_protocol_role,
)

__all__ = [
    "Action",
    "Decision",
    "DecisionRequest",
    "DelegationGrant",
    "ResourceRef",
    "Role",
    "RoleGrant",
    "Scope",
    "ScopeType",
    "ServiceIdentity",
    "Subject",
    "ROLE_CAPABILITIES",
    "decide",
    "delegation_permits",
    "ProtocolRole",
    "PROTOCOL_ROLE_TO_CVLN_ROLE",
    "cvln_role_for_protocol_role",
]
