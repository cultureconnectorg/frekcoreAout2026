"""Unit tests for the Permission Engine model (Phase 2, Priorite 3).

Pure Python — no MongoDB, no live server, no wiring into any existing route
(this engine is not called from anywhere in production code yet; see
reports/12_PHASE2_IMPLEMENTATION.md for why).
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from permissions import (  # noqa: E402
    Action,
    DecisionRequest,
    ProtocolRole,
    ResourceRef,
    Role,
    RoleGrant,
    Scope,
    ScopeType,
    Subject,
    cvln_role_for_protocol_role,
    decide,
)
from permissions.audit_integration import decision_to_audit_event  # noqa: E402
from permissions.protocol_roles import PROTOCOL_ROLE_TO_CVLN_ROLE  # noqa: E402

pytestmark = pytest.mark.unit


def _grant(role: Role, scope: Scope) -> RoleGrant:
    return RoleGrant(role=role, scope=scope, granted_at="2026-08-30T00:00:00Z")


def test_founder_can_do_anything_anywhere():
    subject = Subject(
        frek_id="id-founder", roles=[_grant(Role.FOUNDER, Scope(type=ScopeType.GLOBAL))]
    )
    for action in Action:
        resource = ResourceRef(resource_type="frek.artist", resource_id="id-track-1")
        decision = decide(
            DecisionRequest(subject=subject, action=action, resource=resource)
        )
        assert decision.allowed, action


def test_artist_can_only_act_on_own_objects():
    subject = Subject(
        frek_id="id-artist-1", roles=[_grant(Role.ARTIST, Scope(type=ScopeType.OBJECT))]
    )

    own_track = ResourceRef(
        resource_type="frek.track", resource_id="id-t1", owner_id="id-artist-1"
    )
    other_track = ResourceRef(
        resource_type="frek.track", resource_id="id-t2", owner_id="id-artist-2"
    )

    allowed = decide(
        DecisionRequest(subject=subject, action=Action.UPDATE, resource=own_track)
    )
    denied = decide(
        DecisionRequest(subject=subject, action=Action.UPDATE, resource=other_track)
    )

    assert allowed.allowed is True
    assert allowed.matched_role == Role.ARTIST
    assert denied.allowed is False


def test_artist_cannot_administer_even_own_objects():
    subject = Subject(
        frek_id="id-artist-1", roles=[_grant(Role.ARTIST, Scope(type=ScopeType.OBJECT))]
    )
    own = ResourceRef(
        resource_type="frek.track", resource_id="id-t1", owner_id="id-artist-1"
    )

    decision = decide(
        DecisionRequest(subject=subject, action=Action.ADMINISTER, resource=own)
    )
    assert decision.allowed is False
    assert "no role grant" in decision.reason


def test_admin_label_scoped_to_organization():
    org_scope = Scope(type=ScopeType.ORGANIZATION, id="id-fms")
    subject = Subject(frek_id="id-admin-1", roles=[_grant(Role.ADMIN_LABEL, org_scope)])

    in_org = ResourceRef(resource_type="frek.track", organization_id="id-fms")
    other_org = ResourceRef(
        resource_type="frek.track", organization_id="id-other-label"
    )

    assert (
        decide(
            DecisionRequest(subject=subject, action=Action.ISSUE, resource=in_org)
        ).allowed
        is True
    )
    assert (
        decide(
            DecisionRequest(subject=subject, action=Action.ISSUE, resource=other_org)
        ).allowed
        is False
    )
    # ADMIN_LABEL capability set does not include DELETE (see ROLE_CAPABILITIES).
    assert (
        decide(
            DecisionRequest(subject=subject, action=Action.DELETE, resource=in_org)
        ).allowed
        is False
    )


def test_student_read_only():
    subject = Subject(
        frek_id="id-student-1",
        roles=[_grant(Role.STUDENT, Scope(type=ScopeType.GLOBAL))],
    )
    resource = ResourceRef(resource_type="frek.certificate", resource_id="id-cert-1")

    assert (
        decide(
            DecisionRequest(subject=subject, action=Action.READ, resource=resource)
        ).allowed
        is True
    )
    assert (
        decide(
            DecisionRequest(subject=subject, action=Action.ISSUE, resource=resource)
        ).allowed
        is False
    )


def test_subject_with_no_grants_is_denied():
    subject = Subject(frek_id="id-nobody", roles=[])
    resource = ResourceRef(resource_type="frek.artist")
    decision = decide(
        DecisionRequest(subject=subject, action=Action.READ, resource=resource)
    )
    assert decision.allowed is False
    assert decision.matched_role is None


def test_entity_scope_matches_resource_id_exactly():
    entity_scope = Scope(type=ScopeType.ENTITY, id="id-event-1")
    subject = Subject(
        frek_id="id-teacher-1", roles=[_grant(Role.TEACHER, entity_scope)]
    )

    matching = ResourceRef(resource_type="frek.certificate", resource_id="id-event-1")
    other = ResourceRef(resource_type="frek.certificate", resource_id="id-event-2")

    assert (
        decide(
            DecisionRequest(subject=subject, action=Action.ISSUE, resource=matching)
        ).allowed
        is True
    )
    assert (
        decide(
            DecisionRequest(subject=subject, action=Action.ISSUE, resource=other)
        ).allowed
        is False
    )


def test_decision_to_audit_event_completes_the_chain():
    subject = Subject(
        frek_id="id-artist-1", roles=[_grant(Role.ARTIST, Scope(type=ScopeType.OBJECT))]
    )
    resource = ResourceRef(
        resource_type="frek.track", resource_id="id-t1", owner_id="id-someone-else"
    )
    request = DecisionRequest(subject=subject, action=Action.DELETE, resource=resource)

    decision = decide(request)
    event = decision_to_audit_event(
        request, decision, request_id="req-1", correlation_id="corr-1"
    )

    assert event.actor_frek_id == "id-artist-1"
    assert event.action == "delete"
    assert event.resource_type == "frek.track"
    assert event.resource_id == "id-t1"
    assert event.result == "deny"
    assert event.request_id == "req-1"
    assert event.correlation_id == "corr-1"


# ------------- Protocol Role vocabulary (Issuer/Holder/Verifier, P2 2026-08-31) -------------
# Closes reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md's Credentials-section
# gap: the DID/VC/EUDI protocol roles connected to this module's own Role
# vocabulary, via a documented mapping rather than new Role enum members
# (see permissions/protocol_roles.py's own docstring for why).


def test_every_protocol_role_has_a_documented_mapping_entry():
    """Total mapping — no protocol role silently unmapped."""
    assert set(PROTOCOL_ROLE_TO_CVLN_ROLE.keys()) == set(ProtocolRole)


def test_protocol_roles_are_exactly_the_w3c_vc_three():
    assert {r.value for r in ProtocolRole} == {"issuer", "holder", "verifier"}


def test_cvln_role_for_protocol_role_matches_the_documented_mapping():
    for protocol_role in ProtocolRole:
        assert (
            cvln_role_for_protocol_role(protocol_role)
            == PROTOCOL_ROLE_TO_CVLN_ROLE[protocol_role]
        )


def test_no_protocol_role_currently_maps_to_an_enforceable_cvln_role():
    """Documents today's real answer (see protocol_roles.py's per-entry
    comments): none of Issuer/Holder/Verifier is gated by an existing Role
    grant yet, because no DID/EUDI route calls permissions.engine.decide().
    A future route wiring one of these in would need to change this test —
    that's the point: it can't silently drift unnoticed."""
    for protocol_role in ProtocolRole:
        assert cvln_role_for_protocol_role(protocol_role) is None
