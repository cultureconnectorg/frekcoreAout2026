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
"""

from .models import (
    Action,
    Decision,
    DecisionRequest,
    ResourceRef,
    Role,
    RoleGrant,
    Scope,
    ScopeType,
    Subject,
)
from .engine import ROLE_CAPABILITIES, decide

__all__ = [
    "Action",
    "Decision",
    "DecisionRequest",
    "ResourceRef",
    "Role",
    "RoleGrant",
    "Scope",
    "ScopeType",
    "Subject",
    "ROLE_CAPABILITIES",
    "decide",
]
