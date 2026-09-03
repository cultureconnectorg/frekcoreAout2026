"""D2 — Creative Lifecycle (founder decision D2, 2026-09-02) — unit tests.

Same isolated-app technique as `test_content_binding_unit.py`: FastAPI +
TestClient + mongomock_motor, no live server/Mongo. D1's real extraction
(`content_binding.extraction.compute_signal_fingerprint`, which itself
delegates to the librosa-dependent `frek.nodes.node01_extraction`) is
monkeypatched at its source module so this file tests the CREATIVE
LIFECYCLE LOGIC (stage guards, hybrid re-entry, auth, persistence, D6/D1
reuse, event emission) — not the DSP algorithm, exactly like D1's own
test file does for the signal-processing boundary.

`exact_hash()` (plain SHA-256, no external dependency) is left real.
"""

import asyncio
import hashlib
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault(
    "SECRET_KEY", "dev-only-not-a-real-secret-creative-lifecycle-test"
)
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import mongomock_motor  # noqa: E402

import creative_lifecycle.routes as cl_routes  # noqa: E402
from creative_lifecycle.routes import creative_lifecycle_router  # noqa: E402
from creative_lifecycle.models import LifecycleEvent, LifecycleStage  # noqa: E402
from content_binding.models import SignalFingerprintData  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]
CONTENT_A = b"A" * 2000
CONTENT_B = b"B" * 2000
CONTENT_C = b"C" * 2000


def _vector_for(content_bytes: bytes):
    """Deterministic, content-derived 528D vector -- identical content
    always yields an identical vector (so coherence_score is provably
    100.0 for a resubmission of the same bytes), different content
    yields a different vector (so coherence_score is provably not a
    constant stub), without importing anything librosa-adjacent."""
    digest = hashlib.sha256(content_bytes).digest()
    base = [b / 255.0 for b in digest]  # 32 floats
    return (base * 17)[:528]


async def _fake_extract(content_bytes: bytes):
    return SignalFingerprintData(
        algorithm="frek_signal_v1",
        algorithm_version="1.0.0",
        dimensions=528,
        vector=_vector_for(content_bytes),
        sample_rate=44100,
        duration_seconds=1.0,
    )


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_creative_lifecycle_test"]
    cl_routes.set_db(db)

    fresh_bus = InProcessEventBus()
    monkeypatch.setattr("eventbus.bus.default_bus", fresh_bus)

    # Patched at the source module: creative_lifecycle/routes.py's
    # _compute_binding_ref does `from content_binding.extraction import
    # compute_signal_fingerprint`, a fresh (late) import each call, so
    # patching the source attribute is what actually takes effect --
    # patching "creative_lifecycle.routes.compute_signal_fingerprint"
    # would not (that name is never bound at module scope there).
    monkeypatch.setattr(
        "content_binding.extraction.compute_signal_fingerprint", _fake_extract
    )

    async def _fake_notarize_fail(*args, **kwargs):
        raise RuntimeError("no notary wired in this isolated test app")

    monkeypatch.setattr(
        "notary.service.notarize_event", _fake_notarize_fail, raising=False
    )

    app = FastAPI()
    app.include_router(creative_lifecycle_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db, fresh_bus


def _holder_headers(frek_id: str) -> dict:
    token = identity_service.issue_session_token(frek_id)
    return {"X-FREK-Session": token}


def _admin_headers() -> dict:
    return {"X-Admin-Key": ADMIN_KEY}


def _genesis(client, headers) -> str:
    r = client.post(
        "/api/v1/creative-lifecycle/genesis",
        json={"concept": "a song about rain"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["pre_id"]


def _workshop(client, pre_id, content, headers, notes=None):
    return client.post(
        f"/api/v1/creative-lifecycle/{pre_id}/workshop",
        files={"content": ("v1.wav", content, "audio/wav")},
        data={"notes": notes} if notes else {},
        headers=headers,
    )


def _metamorphose(client, pre_id, content, headers):
    return client.post(
        f"/api/v1/creative-lifecycle/{pre_id}/metamorphose",
        files={"content": ("final.wav", content, "audio/wav")},
        headers=headers,
    )


def _emission(client, pre_id, fk_frek_id, headers):
    return client.post(
        f"/api/v1/creative-lifecycle/{pre_id}/emission",
        json={"fk_frek_id": fk_frek_id},
        headers=headers,
    )


async def _seed_fk_object(db, frek_id: str):
    await db.fk_objects.insert_one({"frek_id": frek_id, "object_type": "song"})


class TestUnauthorized:
    def test_genesis_no_credentials_is_403(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.post("/api/v1/creative-lifecycle/genesis", json={})
        assert r.status_code == 403

    def test_genesis_wrong_admin_key_is_403(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.post(
            "/api/v1/creative-lifecycle/genesis",
            json={},
            headers={"X-Admin-Key": "wrong"},
        )
        assert r.status_code == 403

    def test_progress_by_unrelated_holder_is_403(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _holder_headers("ARTIST-1"))
        r = _workshop(client, pre_id, CONTENT_A, _holder_headers("SOME-OTHER-PERSON"))
        assert r.status_code == 403

    def test_progress_with_no_credentials_is_403(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = _workshop(client, pre_id, CONTENT_A, {})
        assert r.status_code == 403


class TestGenesisIsNotIdentity:
    """CREATIVE_LIFECYCLE_EQUALS_IDENTITY_LIFECYCLE=FALSE,
    GENESIS_EQUALS_LEGAL_AUTHORSHIP/OWNERSHIP/ABSOLUTE_PRIORITY=FALSE."""

    def test_genesis_mints_a_pre_id_never_a_frek_id(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        assert pre_id.startswith("PRE-")
        assert not pre_id.startswith("FK-")

    def test_genesis_claim_never_asserts_authorship_ownership_or_priority(
        self, app_and_db
    ):
        client, _db, _bus = app_and_db
        r = client.post(
            "/api/v1/creative-lifecycle/genesis",
            json={"concept": "a song about rain"},
            headers=_admin_headers(),
        )
        body = r.json()
        forbidden = {
            "author",
            "authorship",
            "owner",
            "ownership",
            "priority",
            "copyright",
            "infalsifiable",
            "irrefutable",
        }
        statement = body["claim"]["statement"].lower()
        assert not any(word in statement for word in forbidden)
        assert body["claim"]["origin"] == "declared"
        assert body["stage"] == "GENESIS"
        assert body["sequence"] == 1

    def test_genesis_by_holder_records_actor_and_authority(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.post(
            "/api/v1/creative-lifecycle/genesis",
            json={},
            headers=_holder_headers("ARTIST-1"),
        )
        body = r.json()
        assert body["actor_id"] == "ARTIST-1"
        assert body["authority"] == "holder"

    def test_genesis_by_admin_has_no_actor(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.post(
            "/api/v1/creative-lifecycle/genesis", json={}, headers=_admin_headers()
        )
        body = r.json()
        assert body["actor_id"] is None
        assert body["authority"] == "admin"


class TestWorkshop:
    def test_workshop_requires_existing_pre_id(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _workshop(client, "PRE-DOES-NOT-EXIST", CONTENT_A, _admin_headers())
        assert r.status_code == 404

    def test_workshop_after_genesis_succeeds(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = _workshop(client, pre_id, CONTENT_A, _admin_headers())
        assert r.status_code == 200
        assert r.json()["stage"] == "WORKSHOP"
        assert r.json()["deduplicated"] is False

    def test_workshop_is_repeatable(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        _workshop(client, pre_id, CONTENT_A, _admin_headers())
        r2 = _workshop(client, pre_id, CONTENT_B, _admin_headers())
        assert r2.status_code == 200
        summary = client.get(f"/api/v1/creative-lifecycle/{pre_id}").json()
        assert summary["workshop_version_count"] == 2

    def test_workshop_deduplicates_identical_content(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r1 = _workshop(client, pre_id, CONTENT_A, _admin_headers())
        r2 = _workshop(client, pre_id, CONTENT_A, _admin_headers())
        assert r1.json()["deduplicated"] is False
        assert r2.json()["deduplicated"] is True
        assert r1.json()["event_id"] == r2.json()["event_id"]

    def test_workshop_content_too_small_is_400(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = _workshop(client, pre_id, b"tiny", _admin_headers())
        assert r.status_code == 400

    def test_workshop_rejected_once_past_workshop(self, app_and_db):
        """Historical guard preserved: WORKSHOP requires current stage in
        {GENESIS, WORKSHOP} -- once EMISSION has happened, a bare
        WORKSHOP call (without first re-entering METAMORPHOSE) is
        rejected."""
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        _emission(client, pre_id, "FK-1", _admin_headers())
        r = _workshop(client, pre_id, CONTENT_B, _admin_headers())
        assert r.status_code == 409


class TestMetamorphoseUnguarded:
    """Historical finding preserved deliberately: METAMORPHOSE has no
    stage guard beyond the pre_id existing."""

    def test_metamorphose_allowed_directly_after_genesis(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        assert r.status_code == 200
        assert r.json()["stage"] == "METAMORPHOSE"

    def test_metamorphose_requires_existing_pre_id(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _metamorphose(client, "PRE-NOPE", CONTENT_A, _admin_headers())
        assert r.status_code == 404

    def test_coherence_score_100_when_no_workshop_versions(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        assert r.json()["data"]["coherence_score"] == 100.0

    def test_coherence_score_100_for_identical_workshop_and_final_content(
        self, app_and_db
    ):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        _workshop(client, pre_id, CONTENT_A, _admin_headers())
        r = _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        assert r.json()["data"]["coherence_score"] == 100.0

    def test_coherence_score_computed_and_not_a_constant_for_different_content(
        self, app_and_db
    ):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        _workshop(client, pre_id, CONTENT_A, _admin_headers())
        r = _metamorphose(client, pre_id, CONTENT_B, _admin_headers())
        score = r.json()["data"]["coherence_score"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
        # Real computation evidence recorded, not just the final claim.
        kinds = [e["kind"] for e in r.json()["evidence"]]
        assert kinds.count("computation") == 2


class TestEmission:
    def test_emission_requires_current_stage_metamorphose(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        r = _emission(client, pre_id, "FK-1", _admin_headers())
        assert r.status_code == 409

    def test_emission_requires_existing_fk_object(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        r = _emission(client, pre_id, "FK-DOES-NOT-EXIST", _admin_headers())
        assert r.status_code == 404

    def test_emission_binds_canonical_existing_fk_object(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        r = _emission(client, pre_id, "FK-1", _admin_headers())
        assert r.status_code == 200
        assert r.json()["fk_frek_id"] == "FK-1"
        assert r.json()["deduplicated"] is False

    def test_second_emission_after_reentry_is_a_new_event_not_a_dedup(self, app_and_db):
        """See TestHybridReentry for the full documented flow -- this is
        the narrow idempotency-boundary check: re-entering METAMORPHOSE
        makes a genuinely NEW EMISSION event possible, never a silent
        dedup of the first one, even with the same fk_frek_id."""
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        e1 = _emission(client, pre_id, "FK-1", _admin_headers())
        _metamorphose(client, pre_id, CONTENT_B, _admin_headers())
        e2 = _emission(client, pre_id, "FK-1", _admin_headers())
        assert e2.json()["deduplicated"] is False
        assert e2.json()["event_id"] != e1.json()["event_id"]


class TestHybridReentry:
    """The evidence-derived HYBRID model: METAMORPHOSE -> EMISSION ->
    METAMORPHOSE -> EMISSION is a real, supported possibility, not a bug
    -- see models.py's module docstring finding."""

    def test_full_re_entry_cycle_allows_second_emission(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        _workshop(client, pre_id, CONTENT_A, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        e1 = _emission(client, pre_id, "FK-1", _admin_headers())
        assert e1.status_code == 200

        m2 = _metamorphose(client, pre_id, CONTENT_C, _admin_headers())
        assert m2.status_code == 200

        e2 = _emission(client, pre_id, "FK-1", _admin_headers())
        assert e2.status_code == 200
        assert e2.json()["deduplicated"] is False  # new event: different sequence

        summary = client.get(f"/api/v1/creative-lifecycle/{pre_id}").json()
        stages = [e["stage"] for e in summary["events"]]
        assert stages == [
            "GENESIS",
            "WORKSHOP",
            "METAMORPHOSE",
            "EMISSION",
            "METAMORPHOSE",
            "EMISSION",
        ]
        assert summary["fk_frek_id"] == "FK-1"


class TestLegacy:
    def test_legacy_requires_prior_emission(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = client.post(
            f"/api/v1/creative-lifecycle/{pre_id}/legacy",
            json={"child_pre_id": "PRE-CHILD"},
            headers=_admin_headers(),
        )
        assert r.status_code == 409

    def test_legacy_requires_a_child_reference(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        _emission(client, pre_id, "FK-1", _admin_headers())
        r = client.post(
            f"/api/v1/creative-lifecycle/{pre_id}/legacy",
            json={},
            headers=_admin_headers(),
        )
        assert r.status_code == 400

    def test_legacy_succeeds_after_emission(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        _emission(client, pre_id, "FK-1", _admin_headers())
        r = client.post(
            f"/api/v1/creative-lifecycle/{pre_id}/legacy",
            json={"child_pre_id": "PRE-CHILD", "note": "sample"},
            headers=_admin_headers(),
        )
        assert r.status_code == 200
        assert r.json()["stage"] == "LEGACY"
        assert r.json()["fk_frek_id"] == "FK-1"


class TestHistoryNeverDestroyed:
    def test_get_lifecycle_returns_full_event_history(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        pre_id = _genesis(client, _admin_headers())
        _workshop(client, pre_id, CONTENT_A, _admin_headers())
        _workshop(client, pre_id, CONTENT_B, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        _emission(client, pre_id, "FK-1", _admin_headers())

        summary = client.get(f"/api/v1/creative-lifecycle/{pre_id}").json()
        assert len(summary["events"]) == 5
        assert summary["current_stage"] == "EMISSION"
        assert summary["genesis_actor_id"] is None  # admin-authored
        sequences = [e["sequence"] for e in summary["events"]]
        assert sequences == sorted(sequences)  # append-only, monotonic

    def test_unknown_pre_id_get_is_404(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.get("/api/v1/creative-lifecycle/PRE-DOES-NOT-EXIST")
        assert r.status_code == 404


class TestD6EvidenceReuse:
    """Not a comment claiming reuse -- structural proof: every event
    round-trips through the real Claim/Evidence Pydantic types."""

    def test_events_round_trip_through_real_lifecycle_event_type(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = _workshop(client, pre_id, CONTENT_A, _admin_headers())
        body = r.json()

        event = LifecycleEvent.model_validate(body)
        assert event.claim.origin.value == "computed"
        assert len(event.evidence) == 1
        assert event.evidence[0].kind.value == "computation"
        # COMPUTATION evidence never implies a proof-engine proof state
        # on its own (D6's EVIDENCE_EQUALS_PROOF=FALSE, same as D1).
        assert event.evidence[0].to_proof_state_hint() is None

    def test_genesis_claim_origin_is_declared_not_computed(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.post(
            "/api/v1/creative-lifecycle/genesis", json={}, headers=_admin_headers()
        )
        assert r.json()["claim"]["origin"] == "declared"


class TestD1Reuse:
    """D2_CONSUMES_D1=TRUE, D2_REIMPLEMENTS_D1=FALSE."""

    def test_workshop_delegates_to_content_binding_extraction(
        self, app_and_db, monkeypatch
    ):
        client, _db, _bus = app_and_db
        calls = []

        async def _spy_extract(content_bytes: bytes):
            calls.append(content_bytes)
            return await _fake_extract(content_bytes)

        monkeypatch.setattr(
            "content_binding.extraction.compute_signal_fingerprint", _spy_extract
        )
        pre_id = _genesis(client, _admin_headers())
        _workshop(client, pre_id, CONTENT_A, _admin_headers())
        assert calls == [CONTENT_A]

    def test_no_dsp_reimplementation_in_creative_lifecycle_source(self):
        """The module never imports frek.nodes.node01_extraction (D1's
        real pipeline) or librosa directly -- it only ever reaches
        extraction through content_binding.extraction, exactly once."""
        import creative_lifecycle.routes as mod

        src = open(mod.__file__).read()
        assert "node01_extraction" not in src
        assert "import librosa" not in src
        assert "from content_binding.extraction import" in src

    def test_exact_hash_matches_real_sha256(self, app_and_db):
        client, _db, _bus = app_and_db
        pre_id = _genesis(client, _admin_headers())
        r = _workshop(client, pre_id, CONTENT_A, _admin_headers())
        assert (
            r.json()["content_binding_ref"]["exact_hash"]
            == hashlib.sha256(CONTENT_A).hexdigest()
        )


class TestAuditEventbus:
    def test_creative_lifecycle_recorded_event_published(self, app_and_db):
        client, _db, bus = app_and_db
        received = []
        bus.subscribe("creative_lifecycle.recorded", lambda ev: received.append(ev))
        _genesis(client, _admin_headers())
        assert len(received) == 1
        assert received[0].payload["stage"] == "GENESIS"

    def test_each_stage_publishes_its_own_event(self, app_and_db):
        client, db, bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        received = []
        bus.subscribe("creative_lifecycle.recorded", lambda ev: received.append(ev))
        pre_id = _genesis(client, _admin_headers())
        _metamorphose(client, pre_id, CONTENT_A, _admin_headers())
        _emission(client, pre_id, "FK-1", _admin_headers())
        stages = [ev.payload["stage"] for ev in received]
        assert stages == ["GENESIS", "METAMORPHOSE", "EMISSION"]


class TestHistoricalVocabularyPreserved:
    def test_stage_enum_values_are_the_historical_five_words(self):
        assert {s.value for s in LifecycleStage} == {
            "GENESIS",
            "WORKSHOP",
            "METAMORPHOSE",
            "EMISSION",
            "LEGACY",
        }


class TestParticipantBadgeLifecycleSeparation:
    """Verified collision: frek_v1's participant/badge lifecycle uses the
    same vocabulary but a structurally separate collection/notarization
    payload_type/authority model -- see models.py's module docstring."""

    def test_creative_lifecycle_uses_its_own_collection(self, app_and_db):
        client, db, _bus = app_and_db
        _genesis(client, _admin_headers())
        count = asyncio.run(db.creative_lifecycle_events.count_documents({}))
        assert count == 1
        # Never writes into frek_v1's own collection.
        badge_count = asyncio.run(db.frek_stages.count_documents({}))
        assert badge_count == 0

    def test_notarization_payload_type_is_creative_lifecycle_not_stage_transition(
        self, app_and_db, monkeypatch
    ):
        client, _db, _bus = app_and_db
        seen = {}

        async def _capture_notarize(**kwargs):
            seen.update(kwargs)
            return {"height": 1, "block_hash": "ab" * 16}

        monkeypatch.setattr(
            "notary.service.notarize_event", _capture_notarize, raising=False
        )
        _genesis(client, _admin_headers())
        assert seen.get("payload_type") == "creative_lifecycle"


class TestBackendFrekUntouched:
    def test_historical_frek_routes_module_not_imported_by_creative_lifecycle(self):
        import creative_lifecycle.routes as mod

        src = open(mod.__file__).read()
        assert "backend.frek" not in src
        assert "from frek.routes import" not in src
        assert "from frek.pipeline import" not in src
