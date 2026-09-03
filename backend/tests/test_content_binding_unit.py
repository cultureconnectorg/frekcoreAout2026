"""D1 — Content Binding (founder decision D1, 2026-09-01) — unit tests.

Isolated FastAPI app + TestClient + mongomock_motor, no live server needed
(same technique as backend/tests/test_identity_recovery_unit.py). The real
signal-extraction pipeline (`frek.nodes.node01_extraction`, which
lazy-imports `librosa`/`soundfile`) is monkeypatched out — those libraries
are not in requirements-ci.txt (see reports/FREKCORE_D1_VALIDATION_EVIDENCE.md
for why, and for the separate, real-librosa validation pass run outside
CI) — because what this file tests is the CONTENT BINDING LOGIC (identity
separation, hashing, persistence, auth, idempotency, D6 evidence
semantics), not the DSP algorithm itself.
"""

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

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-content-binding-test")
# security.policies.check_rate_limit reads its own module-global `db`
# (set via security.policies.set_db, wired only in the real server.py
# startup) — this file exercises the rate-limit CALL SITE (it's really
# there) via the isolated app below, not the rate-limiter's own
# behavior (already covered by test_security_hardening.py), so the
# existing "deterministic CI runs" escape hatch applies here too.
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import mongomock_motor  # noqa: E402

import content_binding.routes as cb_routes  # noqa: E402
from content_binding.routes import content_binding_router  # noqa: E402
from content_binding.models import SignalFingerprintData  # noqa: E402
from proof_engine.models import ProofState  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]
FAKE_AUDIO_A = b"A" * 2000  # >= MIN_AUDIO_BYTES
FAKE_AUDIO_B = b"B" * 2000  # different content


def _fake_fingerprint(*, algorithm_version="1.0.0"):
    return SignalFingerprintData(
        algorithm="frek_signal_v1",
        algorithm_version=algorithm_version,
        dimensions=528,
        vector=[0.1] * 528,
        sample_rate=44100,
        duration_seconds=1.23,
    )


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_content_binding_test"]
    cb_routes.set_db(db)

    # Isolated event bus per test run, same technique as
    # test_identity_recovery_unit.py.
    fresh_bus = InProcessEventBus()
    monkeypatch.setattr("eventbus.bus.default_bus", fresh_bus)

    # Deterministic, librosa-free fingerprint extraction.
    async def _fake_extract(audio_bytes: bytes):
        return _fake_fingerprint()

    monkeypatch.setattr(
        "content_binding.routes.compute_signal_fingerprint", _fake_extract
    )

    # No real notary chain in this isolated app — notarization stays
    # best-effort/absent, so proof_state should stay "fingerprint".
    async def _fake_notarize_fail(*args, **kwargs):
        raise RuntimeError("no notary wired in this isolated test app")

    monkeypatch.setattr(
        "notary.service.notarize_event", _fake_notarize_fail, raising=False
    )

    app = FastAPI()
    app.include_router(content_binding_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db, fresh_bus


async def _seed_fk_object(db, frek_id: str):
    await db.fk_objects.insert_one({"frek_id": frek_id, "object_type": "song"})


def _holder_headers(frek_id: str) -> dict:
    token = identity_service.issue_session_token(frek_id)
    return {"X-FREK-Session": token}


def _admin_headers() -> dict:
    return {"X-Admin-Key": ADMIN_KEY}


class TestUnauthorized:
    def test_no_credentials_is_403(self, app_and_db):
        client, db, _bus = app_and_db
        import asyncio

        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
        )
        assert r.status_code == 403

    def test_wrong_admin_key_is_403(self, app_and_db):
        client, db, _bus = app_and_db
        import asyncio

        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers={"X-Admin-Key": "wrong"},
        )
        assert r.status_code == 403


class TestObjectMustExist:
    def test_unknown_frek_id_is_404(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.post(
            "/api/v1/content-binding/DOES-NOT-EXIST",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r.status_code == 404


class TestCreateBinding:
    @pytest.fixture(autouse=True)
    def _seed(self, app_and_db):
        import asyncio

        client, db, bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        self.client, self.db, self.bus = client, db, bus

    def test_create_as_admin_succeeds(self):
        r = self.client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["frek_id"] == "FK-1"
        assert body["produced_by"] == "admin"
        assert body["deduplicated"] is False

    def test_create_as_holder_succeeds(self):
        # Holder session IS the frek_id being bound to.
        r = self.client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_holder_headers("FK-1"),
        )
        assert r.status_code == 200
        assert r.json()["produced_by"] == "holder"

    def test_create_as_linked_holder_succeeds(self):
        import asyncio

        asyncio.run(
            self.db.frek_persons.insert_one(
                {"frek_id": "PERSON-1", "linked_objects": ["FK-1"]}
            )
        )
        r = self.client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_holder_headers("PERSON-1"),
        )
        assert r.status_code == 200
        assert r.json()["produced_by"] == "holder"

    def test_unrelated_session_is_403(self):
        r = self.client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_holder_headers("SOME-OTHER-PERSON"),
        )
        assert r.status_code == 403

    def test_audio_too_small_is_400(self):
        r = self.client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", b"tiny", "audio/wav")},
            headers=_admin_headers(),
        )
        assert r.status_code == 400

    def test_audio_too_large_is_400(self, monkeypatch):
        monkeypatch.setattr("content_binding.routes.MAX_AUDIO_BYTES", 100)
        r = self.client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r.status_code == 400


class TestFrekIdSeparatedFromFingerprint:
    """Req #1, #2: FREK-ID and fingerprint must never be conflated, and
    object identity must not depend on the fingerprint algorithm/version."""

    def test_frek_id_is_the_object_id_not_derived_from_content(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-STABLE"))
        r1 = client.post(
            "/api/v1/content-binding/FK-STABLE",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        r2 = client.post(
            "/api/v1/content-binding/FK-STABLE",
            files={"audio": ("b.wav", FAKE_AUDIO_B, "audio/wav")},
            headers=_admin_headers(),
        )
        b1, b2 = r1.json(), r2.json()
        # Same FREK Object, different content -> same frek_id, different
        # binding_id/exact_hash. frek_id is stable identity; the binding
        # is per-content evidence, not the identity itself.
        assert b1["frek_id"] == b2["frek_id"] == "FK-STABLE"
        assert b1["binding_id"] != b2["binding_id"]
        assert b1["exact_hash"] != b2["exact_hash"]

    def test_object_identity_stable_across_algorithm_version(
        self, app_and_db, monkeypatch
    ):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-VER"))

        async def _fp_v1(audio_bytes: bytes):
            return _fake_fingerprint(algorithm_version="1.0.0")

        monkeypatch.setattr("content_binding.routes.compute_signal_fingerprint", _fp_v1)
        r1 = client.post(
            "/api/v1/content-binding/FK-VER",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )

        async def _fp_v2(audio_bytes: bytes):
            return _fake_fingerprint(algorithm_version="2.0.0")

        monkeypatch.setattr("content_binding.routes.compute_signal_fingerprint", _fp_v2)
        r2 = client.post(
            "/api/v1/content-binding/FK-VER",
            files={"audio": ("b.wav", FAKE_AUDIO_B, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r1.json()["frek_id"] == r2.json()["frek_id"] == "FK-VER"
        assert r1.json()["signal_fingerprint"]["algorithm_version"] == "1.0.0"
        assert r2.json()["signal_fingerprint"]["algorithm_version"] == "2.0.0"


class TestCryptoHashSeparatedFromSignalFingerprint:
    def test_exact_hash_and_fingerprint_are_distinct_fields(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        body = r.json()
        assert body["exact_hash"] == hashlib.sha256(FAKE_AUDIO_A).hexdigest()
        assert body["exact_hash_algorithm"] == "sha256"
        assert isinstance(body["signal_fingerprint"], dict)
        assert body["signal_fingerprint"]["algorithm"] == "frek_signal_v1"
        assert body["exact_hash"] != body["signal_fingerprint"]["algorithm"]
        # Never merged into one opaque value.
        assert set(body.keys()) >= {"exact_hash", "signal_fingerprint"}


class TestAlgorithmVersioned:
    def test_algorithm_and_version_present(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        fp = r.json()["signal_fingerprint"]
        assert fp["algorithm"] and fp["algorithm_version"]
        assert fp["dimensions"] == 528


class TestIdempotency:
    """Req #6/#11: resubmitting identical content is a dedup, not a new
    binding — closes the historical gap named in the reconciliation
    report (point 24: same audio submitted twice used to mint two
    different identifiers)."""

    def test_identical_content_deduplicates(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r1 = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        r2 = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a-again.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r1.json()["deduplicated"] is False
        assert r2.json()["deduplicated"] is True
        assert r1.json()["binding_id"] == r2.json()["binding_id"]

    def test_different_content_does_not_deduplicate(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r1 = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        r2 = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("b.wav", FAKE_AUDIO_B, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r1.json()["binding_id"] != r2.json()["binding_id"]
        assert r2.json()["deduplicated"] is False


class TestEvidenceSemantics:
    """Req #12/#13/#16: a binding is evidence (proof_engine.ProofState),
    never a silently-promoted VERIFIED claim, and D1 reuses the existing
    ProofState vocabulary unmodified rather than inventing a new one."""

    def test_proof_state_matches_proof_engine_vocabulary(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        body = r.json()
        # Notarization is stubbed to fail in this isolated app (no real
        # notary chain wired) -> proof_state stays at the weakest rung.
        assert body["proof_state"] == ProofState.FINGERPRINT.value == "fingerprint"

    def test_binding_is_actually_composed_of_d6_claim_and_evidence(self, app_and_db):
        """Not a comment claiming reuse -- structural proof: the response
        carries a real Claim (origin=COMPUTED) and two real Evidence
        records (kind=COMPUTATION), built by
        content_binding.models.build_claim_and_evidence(), which itself
        imports proof_engine.evidence_semantics.Claim/Evidence rather
        than defining lookalike types."""
        import asyncio
        from content_binding.models import ContentBinding

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        body = r.json()

        assert body["claim"]["origin"] == "computed"
        assert body["claim"]["subject_id"] == "FK-1"
        assert len(body["evidence"]) == 2
        assert all(e["kind"] == "computation" for e in body["evidence"])

        # Round-trip through the real Pydantic types confirms the shape
        # is genuinely compatible, not just superficially similar.
        binding = ContentBinding.model_validate(body)
        assert binding.claim.origin.value == "computed"
        for ev in binding.evidence:
            # COMPUTATION has no unambiguous proof-engine equivalent by
            # design -- the evidence's mere existence never implies a
            # proof state on its own (D6's EVIDENCE_EQUALS_PROOF=FALSE).
            assert ev.to_proof_state_hint() is None

    def test_no_field_ever_claims_verified_fact(self, app_and_db):
        """Structural proof of D6's #13: nothing in a content binding's
        response shape asserts a verified real-world fact. D1's 3 routes
        (certify/certify-upload/verify) have no comparison/match endpoint
        at all (that is D3/resonance, out of this state's scope) -- there
        is no 'match' result here that could be mis-promoted to VERIFIED
        in the first place."""
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        body = r.json()
        forbidden_keys = {"verified", "is_verified", "verified_fact", "authorship"}
        assert forbidden_keys.isdisjoint(body.keys())

    def test_notarization_upgrades_proof_state(self, app_and_db, monkeypatch):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))

        async def _fake_notarize_ok(**kwargs):
            return {"height": 42, "block_hash": "deadbeef" * 4}

        monkeypatch.setattr(
            "notary.service.notarize_event", _fake_notarize_ok, raising=False
        )
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        body = r.json()
        assert body["proof_state"] == ProofState.LOCAL_PROOF.value == "local_proof"
        assert body["block_height"] == 42


class TestPersistenceAndReads:
    def test_binding_retrievable_by_id_after_creation(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        created = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        ).json()
        r = client.get(f"/api/v1/content-binding/binding/{created['binding_id']}")
        assert r.status_code == 200
        assert r.json()["binding_id"] == created["binding_id"]

    def test_unknown_binding_id_is_404(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.get("/api/v1/content-binding/binding/DOES-NOT-EXIST")
        assert r.status_code == 404

    def test_list_bindings_for_object(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("b.wav", FAKE_AUDIO_B, "audio/wav")},
            headers=_admin_headers(),
        )
        r = client.get("/api/v1/content-binding/FK-1")
        assert r.status_code == 200
        body = r.json()
        assert body["frek_id"] == "FK-1"
        assert body["count"] == 2

    def test_binding_route_not_shadowed_by_dynamic_frek_id_route(self, app_and_db):
        """The exact class of route-shadowing bug this session already
        found and fixed once for identity_engine's /revocation rename:
        '/binding/{id}' must resolve as the static route, never be
        swallowed by '/{frek_id}' matching the literal string 'binding'."""
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "binding"))
        created = client.post(
            (
                "/api/v1/content-binding/FK-1"
                if False
                else "/api/v1/content-binding/binding"
            ),
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        # Creating a binding for an object literally named "binding" must
        # still work (dynamic route), and reading a specific binding_id
        # via the static route must not collide with it.
        assert created.status_code == 200
        by_id = client.get(
            f"/api/v1/content-binding/binding/{created.json()['binding_id']}"
        )
        assert by_id.status_code == 200
        assert by_id.json()["frek_id"] == "binding"


class TestLegacyIdentifierCompatibility:
    """Req #15: the historical backend/frek/ module's own identifier is
    preserved as a compatibility reference, never silently dropped, never
    treated as this binding's or the object's canonical frek_id."""

    def test_legacy_identifier_round_trips_without_becoming_frek_id(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            data={"legacy_identifier": "FREK-2026-0001-abcd1234-ef012345"},
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        body = r.json()
        assert body["legacy_identifier"] == "FREK-2026-0001-abcd1234-ef012345"
        assert body["frek_id"] == "FK-1"  # unchanged, not overwritten by the legacy id

    def test_legacy_identifier_omitted_by_default(self, app_and_db):
        import asyncio

        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = client.post(
            "/api/v1/content-binding/FK-1",
            files={"audio": ("a.wav", FAKE_AUDIO_A, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r.json()["legacy_identifier"] is None


class TestBackendFrekUntouched:
    """Req: historical D1 routes remain unchanged this state."""

    def test_historical_frek_routes_module_not_imported_by_content_binding(self):
        import content_binding.routes as mod

        src = open(mod.__file__).read()
        assert "backend.frek" not in src
        assert "from frek.routes import" not in src
        assert "from frek.pipeline import" not in src
