"""D5 -- Technical Evidence Report (founder decision D5, 2026-09-02) --
unit tests.

Same isolated-app technique as test_content_binding_unit.py /
test_creative_lifecycle_unit.py / test_relationship_graph_unit.py /
test_offline_transport_unit.py: FastAPI + TestClient + mongomock_motor,
no live server/Mongo needed.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-ter-test")
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import mongomock_motor  # noqa: E402

import technical_evidence_report.routes as ter_routes  # noqa: E402
from technical_evidence_report.routes import (  # noqa: E402
    technical_evidence_report_router,
)
from technical_evidence_report.canonical import compute_report_hash  # noqa: E402
from technical_evidence_report.models import (  # noqa: E402
    LEGAL_DISCLAIMER,
    LegalWordingViolation,
    ReportSection,
    ReportSubjectType,
    SectionKind,
    SourceReferences,
    TechnicalEvidenceReport,
    assert_no_forbidden_language,
)
from technical_evidence_report import service as ter_service  # noqa: E402
from permissions.models import Scope, ScopeType  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_ter_test"]
    ter_routes.set_db(db)

    fresh_bus = InProcessEventBus()
    monkeypatch.setattr("eventbus.bus.default_bus", fresh_bus)

    async def _fake_notarize_fail(*args, **kwargs):
        raise RuntimeError("no notary wired in this isolated test app")

    monkeypatch.setattr(
        "notary.service.notarize_event", _fake_notarize_fail, raising=False
    )

    app = FastAPI()
    app.include_router(technical_evidence_report_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db, fresh_bus


def _holder_headers(frek_id: str) -> dict:
    token = identity_service.issue_session_token(frek_id)
    return {"X-FREK-Session": token}


def _admin_headers() -> dict:
    return {"X-Admin-Key": ADMIN_KEY}


def _generate(client, headers, subject_type: str, subject_id: str):
    return client.post(
        "/api/v1/reports/technical-evidence",
        json={"subject_type": subject_type, "subject_id": subject_id},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# 1. Historical route untouched.
# ---------------------------------------------------------------------------


class TestHistoricalRouteUntouched:
    def test_juridique_attestation_route_still_exists_unmodified(self):
        import frek.routes_advanced as routes_advanced

        assert any(
            getattr(r, "path", "") == "/advanced/juridique/attestation"
            for r in routes_advanced.advanced_router.routes
        )

    def test_technical_evidence_report_module_never_imports_frek_routes_advanced(self):
        for mod in ("models", "service", "routes", "canonical"):
            src = (BACKEND_DIR / "technical_evidence_report" / f"{mod}.py").read_text()
            assert "from frek.routes_advanced import" not in src
            assert "import frek.routes_advanced" not in src
            assert "from frek.nodes.node09_juridique import" not in src


# ---------------------------------------------------------------------------
# 2. Legal wording guard -- the "LEGAL WORDING REGRESSION TESTS" section.
# ---------------------------------------------------------------------------


class TestLegalWordingRegression:
    @pytest.mark.parametrize(
        "phrase",
        [
            "This fact is IRREFUTABLE.",
            "This report proves ownership of the work.",
            "This report proves authorship.",
            "This is an official notarial act.",
            "This is a qualified eIDAS timestamp.",
            "The originality is guaranteed original.",
            "This signature is unforgeable.",
            "This is absolute proof of the claim.",
        ],
    )
    def test_forbidden_phrases_rejected(self, phrase):
        with pytest.raises(LegalWordingViolation):
            assert_no_forbidden_language(phrase)

    def test_forbidden_phrase_blocks_section_construction(self):
        """Pydantic wraps the field validator's raised
        LegalWordingViolation (a ValueError) into its own ValidationError
        -- the guard is still what fires, it's just surfaced through
        pydantic's own error type at the model boundary."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="absolute proof"):
            ReportSection(
                kind=SectionKind.PROOF,
                title="Proof",
                statements=["This is absolute proof of ownership."],
            )

    def test_historical_node09_overclaim_phrase_is_itself_caught(self):
        """The exact phrase this state's own historical-discovery pass
        found in node09_juridique.py's to_legal_text() -- confirms the
        guard would have caught the historical defect, not just
        hypothetical phrasing."""
        with pytest.raises(LegalWordingViolation):
            assert_no_forbidden_language(
                "Ce fait est mathematiquement certain et temporellement irrefutable."
            )

    def test_clean_wording_passes(self):
        assert_no_forbidden_language(
            "A signature was verified against the stored public key at this time."
        )

    def test_legal_disclaimer_itself_passes_its_own_guard(self):
        """The fixed LEGAL_DISCLAIMER explicitly names several forbidden
        concepts in order to disclaim them ('It is NOT a notarial act...
        NOT a qualified electronic timestamp...') -- the guard must be
        negation-aware enough to allow that without becoming so loose it
        stops blocking real overclaims (see the next test)."""
        assert_no_forbidden_language(LEGAL_DISCLAIMER)

    def test_negation_awareness_does_not_defeat_the_guard(self):
        """The same phrase, asserted positively rather than negated,
        must still be rejected -- confirms the negation-aware guard is
        not simply permissive."""
        with pytest.raises(LegalWordingViolation):
            assert_no_forbidden_language("This constitutes an official notarial act.")

    def test_all_builtin_section_builders_produce_clean_wording(self):
        """Runs every section builder over representative fixture data and
        confirms none of their own generated statements trip the guard --
        the generator's own output is exercised, not just hand-picked
        strings."""
        sections = [
            ter_service.build_identity_section(None),
            ter_service.build_identity_section(
                {
                    "frek_id": "id-1",
                    "status": "protected",
                    "identity_type": "individual",
                    "created_at": "t",
                    "credentials": [],
                    "linked_objects": [],
                }
            ),
            ter_service.build_credential_section(None),
            ter_service.build_object_section(None),
            ter_service.build_object_section(
                {
                    "frek_id": "fk-1",
                    "object_type": "song",
                    "created_at": "t",
                    "root_hash": "abc",
                    "block_hash": "def",
                }
            ),
            ter_service.build_content_binding_section(None),
            ter_service.build_creative_lifecycle_section([]),
            ter_service.build_creative_lifecycle_section(
                [{"pre_id": "pre-1", "stage": "GENESIS", "sequence": 1}]
            ),
            ter_service.build_relationship_section([]),
            ter_service.build_relationship_section(
                [
                    {
                        "relationship_id": "r1",
                        "predicate": "similar_to",
                        "layer": "cultural",
                        "status": "computed",
                    }
                ]
            ),
            ter_service.build_offline_transport_section([]),
            ter_service.build_offline_transport_section(
                [
                    {
                        "envelope_id": "e1",
                        "sync_status": "synced",
                        "local_validation": "locally_acceptable",
                    }
                ]
            ),
            ter_service.build_proof_section([]),
            ter_service.overall_caveat_section(),
        ]
        # Construction itself already ran the guard (field_validator) --
        # reaching here means every section passed.
        assert len(sections) == 14


# ---------------------------------------------------------------------------
# 3. Bounded report subject types -- the founder's own closed list.
# ---------------------------------------------------------------------------


class TestBoundedSubjectTypes:
    def test_subject_type_is_a_closed_enum(self):
        values = {t.value for t in ReportSubjectType}
        assert values == {
            "frek_identity",
            "frek_object",
            "content_binding",
            "creative_lifecycle_history",
            "relationship_record",
            "credential",
            "evidence_record",
            "proof",
            "offline_transport_envelope",
            "combined_evidence_package",
        }

    def test_unknown_subject_type_rejected_by_request_schema(self, app_and_db):
        client, db, _ = app_and_db
        resp = _generate(client, _admin_headers(), "not_a_real_type", "x")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4. Canonical-input rule: only a resource ID reference is accepted.
# ---------------------------------------------------------------------------


class TestCanonicalInputOnly:
    def test_request_body_carries_only_subject_type_and_subject_id(self):
        fields = set(ter_routes.GenerateReportRequest.model_fields.keys())
        assert fields == {"subject_type", "subject_id"}

    def test_extra_fields_in_request_body_are_ignored_not_trusted(self, app_and_db):
        """Even if a caller stuffs arbitrary 'facts' into the body, the
        generated report never reflects them -- only the resolved
        canonical FREK Object record does."""
        client, db, _ = app_and_db
        asyncio.run(
            db.fk_objects.insert_one(
                {
                    "frek_id": "fk-real",
                    "object_type": "song",
                    "created_at": "2026-01-01T00:00:00Z",
                }
            )
        )
        resp = client.post(
            "/api/v1/reports/technical-evidence",
            json={
                "subject_type": "frek_object",
                "subject_id": "fk-real",
                "artiste_id": "someone-else",
                "sha256_signal": "fabricated",
            },
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "someone-else" not in str(body)
        assert "fabricated" not in str(body)


# ---------------------------------------------------------------------------
# 5. Fail-closed on unresolved references.
# ---------------------------------------------------------------------------


class TestFailClosed:
    def test_unresolvable_reference_returns_404_not_a_hollow_report(self, app_and_db):
        client, db, _ = app_and_db
        resp = _generate(client, _admin_headers(), "frek_object", "does-not-exist")
        assert resp.status_code == 404

    def test_unresolvable_relationship_returns_404(self, app_and_db):
        client, db, _ = app_and_db
        resp = _generate(client, _admin_headers(), "relationship_record", "nope")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 6. Authentication required to generate; public verify does not require it.
# ---------------------------------------------------------------------------


class TestAuthorization:
    def test_generate_without_session_or_admin_key_is_rejected(self, app_and_db):
        client, db, _ = app_and_db
        resp = _generate(client, {}, "frek_object", "fk-1")
        assert resp.status_code == 403

    def test_holder_session_can_generate(self, app_and_db):
        client, db, _ = app_and_db
        asyncio.run(
            db.frek_persons.insert_one(
                {
                    "frek_id": "id-holder",
                    "status": "protected",
                    "identity_type": "individual",
                    "created_at": "t",
                    "credentials": [],
                    "linked_objects": [],
                }
            )
        )
        resp = _generate(
            client, _holder_headers("id-holder"), "frek_identity", "id-holder"
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 7. D1 reuse: PARTIAL status never upgraded.
# ---------------------------------------------------------------------------


class TestD1Reuse:
    def test_content_binding_section_states_partial_validation(self):
        section = ter_service.build_content_binding_section(
            {
                "binding_id": "b1",
                "frek_id": "fk-1",
                "exact_hash": "a" * 64,
                "exact_hash_algorithm": "sha256",
                "signal_fingerprint": {
                    "algorithm": "frek_signal_v1",
                    "algorithm_version": "1.0.0",
                    "dimensions": 528,
                },
                "computed_at": "t",
                "proof_state": "fingerprint",
            }
        )
        assert section.kind == SectionKind.COMPUTED
        assert any("PARTIAL" in s for s in section.statements)


# ---------------------------------------------------------------------------
# 8. D2 reuse: GENESIS never rendered as legal authorship.
# ---------------------------------------------------------------------------


class TestD2Reuse:
    def test_creative_lifecycle_section_always_disclaims_legal_conclusion(self):
        section = ter_service.build_creative_lifecycle_section(
            [{"pre_id": "pre-1", "stage": "GENESIS", "sequence": 1, "fk_frek_id": None}]
        )
        assert any("not a legal determination" in s for s in section.statements)
        assert (
            section.kind != SectionKind.LEGAL_CONCLUSION_NOT_MADE
        )  # own kind is CLAIMED


# ---------------------------------------------------------------------------
# 9. D3 reuse: CULTURAL never rendered as verified fact.
# ---------------------------------------------------------------------------


class TestD3Reuse:
    def test_cultural_relationship_never_yields_verified_kind(self):
        section = ter_service.build_relationship_section(
            [
                {
                    "relationship_id": "r1",
                    "predicate": "similar_to",
                    "layer": "cultural",
                    "status": "verified",
                }
            ]
        )
        # Even if some upstream bug ever let a cultural relation carry
        # status="verified", the report section must not render VERIFIED.
        assert section.kind == SectionKind.INFERRED

    def test_trust_verified_relationship_yields_verified_kind(self):
        section = ter_service.build_relationship_section(
            [
                {
                    "relationship_id": "r1",
                    "predicate": "created_by",
                    "layer": "trust",
                    "status": "verified",
                }
            ]
        )
        assert section.kind == SectionKind.VERIFIED


# ---------------------------------------------------------------------------
# 10. D4 reuse: OFFLINE_ACCEPTED != FINAL_RECONCILIATION.
# ---------------------------------------------------------------------------


class TestD4Reuse:
    def test_synced_envelope_yields_verified_kind_scoped_to_transport(self):
        section = ter_service.build_offline_transport_section(
            [
                {
                    "envelope_id": "e1",
                    "sync_status": "synced",
                    "local_validation": "locally_acceptable",
                }
            ]
        )
        assert section.kind == SectionKind.VERIFIED
        assert any("transport-level" in s for s in section.statements)

    def test_locally_acceptable_but_not_synced_is_not_verified(self):
        section = ter_service.build_offline_transport_section(
            [
                {
                    "envelope_id": "e1",
                    "sync_status": "pending",
                    "local_validation": "locally_acceptable",
                }
            ]
        )
        assert section.kind != SectionKind.VERIFIED
        assert any("FINAL_RECONCILIATION" in s for s in section.statements)


# ---------------------------------------------------------------------------
# 11. Sectioning is never flattened to a single "verified" bool.
# ---------------------------------------------------------------------------


class TestSectioningNeverFlattened:
    def test_report_model_has_no_top_level_verified_boolean_field(self):
        assert "verified" not in TechnicalEvidenceReport.model_fields

    def test_report_always_carries_legal_conclusion_not_made_caveat(self):
        report = ter_service.compose_report(
            subject_type=ReportSubjectType.PROOF,
            subject_id="x",
            source_refs=SourceReferences(),
            sections=[],
        )
        kinds = [s.kind for s in report.sections]
        assert SectionKind.LEGAL_CONCLUSION_NOT_MADE in kinds


# ---------------------------------------------------------------------------
# 12. Disclosure: per-section visibility, PROOF_VISIBILITY != EVIDENCE_VISIBILITY.
# ---------------------------------------------------------------------------


class TestDisclosure:
    def test_object_scoped_section_hidden_from_stranger(self):
        report_dict = {
            "subject_id": "id-1",
            "requested_by": "id-1",
            "source_refs": {},
            "sections": [
                {
                    "kind": "observed",
                    "title": "Identity",
                    "statements": [],
                    "data": {},
                    "visibility": {"type": "object", "id": None},
                },
                {
                    "kind": "proof",
                    "title": "Proof",
                    "statements": [],
                    "data": {},
                    "visibility": {"type": "global", "id": None},
                },
            ],
        }
        redacted = ter_service.redact_for_disclosure(
            report_dict, actor_id="stranger", is_admin=False
        )
        titles = [s["title"] for s in redacted["sections"]]
        assert "Identity" not in titles
        assert "Proof" in titles

    def test_owner_sees_object_scoped_section(self):
        report_dict = {
            "subject_id": "id-1",
            "requested_by": "id-1",
            "source_refs": {},
            "sections": [
                {
                    "kind": "observed",
                    "title": "Identity",
                    "statements": [],
                    "data": {},
                    "visibility": {"type": "object", "id": None},
                },
            ],
        }
        redacted = ter_service.redact_for_disclosure(
            report_dict, actor_id="id-1", is_admin=False
        )
        assert [s["title"] for s in redacted["sections"]] == ["Identity"]

    def test_admin_sees_everything(self):
        report_dict = {
            "subject_id": "id-1",
            "requested_by": "id-1",
            "source_refs": {},
            "sections": [
                {
                    "kind": "observed",
                    "title": "Identity",
                    "statements": [],
                    "data": {},
                    "visibility": {"type": "object", "id": None},
                },
            ],
        }
        redacted = ter_service.redact_for_disclosure(
            report_dict, actor_id=None, is_admin=True
        )
        assert [s["title"] for s in redacted["sections"]] == ["Identity"]

    def test_proof_and_evidence_sections_can_carry_independent_visibility(self):
        proof = ReportSection(
            kind=SectionKind.PROOF,
            title="Proof",
            visibility=Scope(type=ScopeType.GLOBAL),
        )
        identity = ReportSection(
            kind=SectionKind.OBSERVED,
            title="Identity",
            visibility=Scope(type=ScopeType.OBJECT),
        )
        assert proof.visibility.type != identity.visibility.type


# ---------------------------------------------------------------------------
# 13. End-to-end: generate -> redacted response -> get -> public verify.
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_generate_then_get_then_verify(self, app_and_db):
        client, db, bus = app_and_db
        asyncio.run(
            db.fk_objects.insert_one(
                {
                    "frek_id": "fk-e2e",
                    "object_type": "song",
                    "created_at": "2026-01-01T00:00:00Z",
                }
            )
        )
        gen = _generate(client, _admin_headers(), "frek_object", "fk-e2e")
        assert gen.status_code == 200
        report_id = gen.json()["report_id"]
        assert gen.json()["report_hash"]

        got = client.get(
            f"/api/v1/reports/technical-evidence/{report_id}", headers=_admin_headers()
        )
        assert got.status_code == 200
        assert got.json()["report_id"] == report_id

        verify = client.get(f"/api/v1/reports/technical-evidence/{report_id}/verify")
        assert verify.status_code == 200
        vbody = verify.json()
        assert vbody["integrity_verified"] is True
        assert "statements" not in str(vbody.get("sections_summary"))
        assert vbody["legal_disclaimer"] == LEGAL_DISCLAIMER

    def test_verify_unknown_report_id_returns_404(self, app_and_db):
        client, db, _ = app_and_db
        resp = client.get("/api/v1/reports/technical-evidence/does-not-exist/verify")
        assert resp.status_code == 404

    def test_get_unknown_report_id_returns_404(self, app_and_db):
        client, db, _ = app_and_db
        resp = client.get(
            "/api/v1/reports/technical-evidence/does-not-exist",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 14. Report integrity / hash stability.
# ---------------------------------------------------------------------------


class TestReportIntegrity:
    def test_hash_is_stable_across_reserialization(self):
        report = ter_service.compose_report(
            subject_type=ReportSubjectType.PROOF,
            subject_id="x",
            source_refs=SourceReferences(),
            sections=[],
        )
        h1 = compute_report_hash(report)
        reloaded = TechnicalEvidenceReport.model_validate(report.to_public_dict())
        h2 = compute_report_hash(reloaded)
        assert h1 == h2

    def test_hash_does_not_depend_on_verification_time(self):
        report = ter_service.compose_report(
            subject_type=ReportSubjectType.PROOF,
            subject_id="x",
            source_refs=SourceReferences(),
            sections=[],
        )
        h1 = compute_report_hash(report)
        report.verification_time = "2099-01-01T00:00:00+00:00"
        h2 = compute_report_hash(report)
        assert h1 == h2

    def test_hash_changes_when_content_changes(self):
        r1 = ter_service.compose_report(
            subject_type=ReportSubjectType.PROOF,
            subject_id="x",
            source_refs=SourceReferences(),
            sections=[],
        )
        r2 = ter_service.compose_report(
            subject_type=ReportSubjectType.PROOF,
            subject_id="y",
            source_refs=SourceReferences(),
            sections=[],
        )
        assert compute_report_hash(r1) != compute_report_hash(r2)


# ---------------------------------------------------------------------------
# 15. Combined evidence package pulls across every prior D-state.
# ---------------------------------------------------------------------------


class TestCombinedEvidencePackage:
    def test_combined_package_pulls_multiple_d_states(self, app_and_db):
        client, db, _ = app_and_db

        async def seed():
            await db.fk_objects.insert_one(
                {"frek_id": "fk-combo", "object_type": "song", "created_at": "t"}
            )
            await db.content_bindings.insert_one(
                {
                    "binding_id": "b-combo",
                    "frek_id": "fk-combo",
                    "exact_hash": "a" * 64,
                    "exact_hash_algorithm": "sha256",
                    "signal_fingerprint": {
                        "algorithm": "frek_signal_v1",
                        "algorithm_version": "1.0.0",
                        "dimensions": 528,
                    },
                    "computed_at": "t",
                    "proof_state": "fingerprint",
                }
            )
            await db.relationships.insert_one(
                {
                    "relationship_id": "r-combo",
                    "subject_id": "fk-combo",
                    "object_id": "other",
                    "predicate": "created_by",
                    "layer": "trust",
                    "status": "claimed",
                }
            )

        asyncio.run(seed())
        resp = _generate(
            client, _admin_headers(), "combined_evidence_package", "fk-combo"
        )
        assert resp.status_code == 200
        titles = {s["title"] for s in resp.json()["sections"]}
        assert "FREK Object" in titles
        assert "Content Binding (D1)" in titles
        assert "Relationship / Provenance Records (D3)" in titles


# ---------------------------------------------------------------------------
# 16. Rate limiting + audit/eventbus wiring.
# ---------------------------------------------------------------------------


class TestRateLimitAndAuditWiring:
    def test_generate_action_key_registered_in_default_limits(self):
        from security.policies import DEFAULT_LIMITS

        assert "technical_evidence_report_generate" in DEFAULT_LIMITS
        assert "technical_evidence_report_verify" in DEFAULT_LIMITS

    def test_generate_publishes_event_best_effort_even_when_notary_fails(
        self, app_and_db
    ):
        client, db, bus = app_and_db
        received = []
        bus.subscribe(
            "technical_evidence_report.recorded", lambda e: received.append(e)
        )

        asyncio.run(
            db.fk_objects.insert_one(
                {"frek_id": "fk-ev", "object_type": "song", "created_at": "t"}
            )
        )
        resp = _generate(client, _admin_headers(), "frek_object", "fk-ev")
        assert resp.status_code == 200
        assert len(received) == 1
        assert received[0].payload["transition"] == "generated"
        assert "statements" not in str(received[0].payload)

    def test_event_type_registered_in_audit_trail_types(self):
        """Static check on server.py's own source (same technique as
        test_audit_trail.py's own server.py check) -- avoids booting the
        full app graph (MongoDB connection, every module's set_db) just
        to confirm a string is present."""
        server_py = (BACKEND_DIR / "server.py").read_text(encoding="utf-8")
        assert "_AUDIT_TRAIL_EVENT_TYPES" in server_py
        assert '"technical_evidence_report.recorded"' in server_py
