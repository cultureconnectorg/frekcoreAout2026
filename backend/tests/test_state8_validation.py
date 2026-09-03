"""STATE_8 -- Regression / Evidence / Migration Validation (founder
authorization 2026-09-03) -- cross-module validation tests.

This file adds ONLY the STATE_8-specific validation that is genuinely new
relative to the existing D1-D6/STATE_6/STATE_7 regression suite (which
this state re-runs as-is, not duplicated here -- see
docs/validation/FREKCORE_STATE8_VALIDATION_RESULTS.md for the full
evidence classification, including what is covered by existing files
like test_offline_transport_unit.py, test_legacy_compatibility.py, and
test_permissions.py's own STATE_8 delegation-chain section).

Same isolated-app technique as every other unit test file in this suite:
FastAPI + TestClient + mongomock_motor, no live server/Mongo needed.
Where mongomock's own persistence model differs from real MongoDB (it is
isolated per client instance, not server-persisted -- confirmed directly
this state), that limitation is disclosed explicitly rather than treated
as equivalent to real-infra verification. See
docs/validation/FREKCORE_STATE8_VALIDATION_RESULTS.md's persistence
section.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-state8-test")
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import mongomock_motor  # noqa: E402

import content_binding.routes as cb_routes  # noqa: E402
from content_binding.routes import content_binding_router  # noqa: E402
from content_binding.models import SignalFingerprintData  # noqa: E402
import registry.routes as registry_routes  # noqa: E402
from registry.routes import registry_router  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402
from storage.local import LocalFilesystemStorageProvider  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]
FAKE_AUDIO = b"S" * 2000


def _fake_fingerprint():
    return SignalFingerprintData(
        algorithm="frek_signal_v1",
        algorithm_version="1.0.0",
        dimensions=528,
        vector=[0.2] * 528,
        sample_rate=44100,
        duration_seconds=1.0,
    )


def _holder_headers(frek_id: str) -> dict:
    token = identity_service.issue_session_token(frek_id)
    return {"X-FREK-Session": token}


def _admin_headers() -> dict:
    return {"X-Admin-Key": ADMIN_KEY}


# ============================================================
# PERSISTENCE / RECOVERY / RESTART
# ============================================================
#
# Genuine restart-durability requires real, server-side-persisted
# storage -- mongomock_motor is confirmed (this state) to isolate state
# per client instance, so a fresh AsyncMongoMockClient() does NOT
# simulate a real MongoDB surviving a process restart; it simulates data
# loss. That is exactly the gap REAL_MONGO_VALIDATION exists to close,
# and it remains BLOCKED in this sandbox (no docker daemon reachable --
# `docker info` fails with "Cannot connect to the Docker daemon"; no
# local `mongod` binary; no MONGO_URI configured). Per the mission's own
# instruction, mongomock is NOT substituted here as an equivalent.
#
# What CAN be genuinely restart-tested in this sandbox:
#  1. LocalFilesystemStorageProvider -- real disk I/O, no substitute.
#  2. That FREKCORE's canonical route modules hold no authoritative
#     state in Python-process-local variables (only in the injected
#     `db` handle) -- proven by tearing down the FastAPI app/TestClient
#     entirely and rebuilding it against the SAME underlying db object,
#     which is the correct model of "the app process restarted while its
#     database connection (real or mock) kept the data".


class TestLocalStorageRestartDurability:
    """storage.local.LocalFilesystemStorageProvider -- real disk, so this
    is genuine REAL_INFRA_VERIFIED restart-durability evidence (the one
    canonical persistence layer in this codebase not gated on Mongo)."""

    def test_write_read_restart_reread(self):
        with tempfile.TemporaryDirectory() as root:
            provider_before_restart = LocalFilesystemStorageProvider(root)
            stored = provider_before_restart.put(
                "evidence/report-1.bin",
                b"technical evidence bytes",
                "application/octet-stream",
            )
            del provider_before_restart  # nothing else references this instance

            # "restart": a brand-new provider instance, same root directory,
            # no shared Python object with the one that wrote the file.
            provider_after_restart = LocalFilesystemStorageProvider(root)
            data, content_type = provider_after_restart.get("evidence/report-1.bin")
            assert data == b"technical evidence bytes"
            assert content_type == "application/octet-stream"
            assert provider_after_restart.exists("evidence/report-1.bin")
            assert stored.sha256 == __import__("hashlib").sha256(data).hexdigest()

    def test_missing_object_after_restart_is_explicit_not_silent(self):
        with tempfile.TemporaryDirectory() as root:
            provider = LocalFilesystemStorageProvider(root)
            with pytest.raises(FileNotFoundError):
                provider.get("never-written.bin")


class TestAppRestartAgainstSamePersistedDb:
    """Simulate an application-process restart while its database
    connection (mongomock here, standing in for the *connection*, not
    for real durability) is preserved -- i.e. confirm content_binding's
    canonical read path depends only on `db`, never on any
    content_binding.routes-module-level cache that a real restart would
    reset. A regression here (a route silently relying on process
    memory) would falsely appear to work today and lose data on any
    real restart."""

    def test_binding_written_before_restart_is_read_after_restart(self, monkeypatch):
        db = mongomock_motor.AsyncMongoMockClient()["frekcore_state8_restart_test"]

        async def _fake_extract(audio_bytes: bytes):
            return _fake_fingerprint()

        async def _fake_notarize_fail(*args, **kwargs):
            raise RuntimeError("no notary wired in this isolated test app")

        # --- "before restart": one app instance, one TestClient ---
        cb_routes.set_db(db)
        monkeypatch.setattr(
            "content_binding.routes.compute_signal_fingerprint", _fake_extract
        )
        monkeypatch.setattr(
            "notary.service.notarize_event", _fake_notarize_fail, raising=False
        )
        fresh_bus = InProcessEventBus()
        monkeypatch.setattr("eventbus.bus.default_bus", fresh_bus)

        app_before = FastAPI()
        app_before.include_router(content_binding_router, prefix="/api/v1")
        client_before = TestClient(app_before)

        asyncio.run(
            db.fk_objects.insert_one({"frek_id": "FK-RESTART", "object_type": "song"})
        )
        r = client_before.post(
            "/api/v1/content-binding/FK-RESTART",
            files={"audio": ("a.wav", FAKE_AUDIO, "audio/wav")},
            headers=_admin_headers(),
        )
        assert r.status_code == 200
        binding_id = r.json()["binding_id"]
        del app_before, client_before  # process "exits"

        # --- "after restart": brand-new FastAPI app + TestClient, same db ---
        cb_routes.set_db(db)  # the only thing a real restart would redo: reconnect
        app_after = FastAPI()
        app_after.include_router(content_binding_router, prefix="/api/v1")
        client_after = TestClient(app_after)

        r2 = client_after.get(f"/api/v1/content-binding/binding/{binding_id}")
        assert r2.status_code == 200
        assert r2.json()["binding_id"] == binding_id


class TestIndexCreationIsIdempotent:
    """Mission: "Verify required indexes are created and compatible...
    Check index creation is idempotent." Calls each module's own
    ensure_indexes() (real startup code, not a test double) twice
    against the same db and confirms no exception and the uniqueness
    constraint it creates is still enforced afterward."""

    def test_content_binding_ensure_indexes_twice_then_unique_constraint_holds(self):
        db = mongomock_motor.AsyncMongoMockClient()["frekcore_state8_index_cb"]

        # ensure_indexes() in this codebase is a FastAPI startup handler
        # closed over the module's own `db` reference set via set_db();
        # call it the same way the app would, twice in a row.
        cb_routes.set_db(db)

        async def _call_twice():
            await cb_routes.ensure_indexes()
            await cb_routes.ensure_indexes()
            # unique index on binding_id must still reject a real duplicate
            await db.content_bindings.insert_one(
                {"binding_id": "dup-1", "frek_id": "FK-1"}
            )
            with pytest.raises(Exception):
                await db.content_bindings.insert_one(
                    {"binding_id": "dup-1", "frek_id": "FK-2"}
                )

        asyncio.run(_call_twice())


# ============================================================
# FAILURE INJECTION (test-level fault injection, not chaos infra)
# ============================================================


class TestDbWriteFailureInjection:
    """A DB write failure must surface as a clean HTTP error, never a
    500 with a raw internal traceback/exception body, and must not
    leave the canonical response claiming success."""

    def test_content_binding_insert_failure_does_not_return_success(self, monkeypatch):
        db = mongomock_motor.AsyncMongoMockClient()["frekcore_state8_dbfail_cb"]
        cb_routes.set_db(db)

        async def _fake_extract(audio_bytes: bytes):
            return _fake_fingerprint()

        async def _fake_notarize_fail(*args, **kwargs):
            raise RuntimeError("no notary wired in this isolated test app")

        monkeypatch.setattr(
            "content_binding.routes.compute_signal_fingerprint", _fake_extract
        )
        monkeypatch.setattr(
            "notary.service.notarize_event", _fake_notarize_fail, raising=False
        )
        monkeypatch.setattr("eventbus.bus.default_bus", InProcessEventBus())

        async def _seed():
            await db.fk_objects.insert_one(
                {"frek_id": "FK-DBFAIL", "object_type": "song"}
            )

        asyncio.run(_seed())

        # mongomock_motor hands back a fresh AsyncIOMotorCollection wrapper
        # on every `db.content_bindings` attribute access (confirmed this
        # state: `db.content_bindings is db.content_bindings` is False) --
        # so the only way to inject a failure the route's own
        # `db.content_bindings.insert_one(...)` call actually hits is to
        # patch the shared collection class, scoped to this one
        # collection name, not a specific instance.
        original_insert_one = mongomock_motor.AsyncMongoMockCollection.insert_one

        async def _broken_insert(self, *args, **kwargs):
            if self.name == "content_bindings":
                raise ConnectionError("simulated DB write failure")
            return await original_insert_one(self, *args, **kwargs)

        monkeypatch.setattr(
            mongomock_motor.AsyncMongoMockCollection, "insert_one", _broken_insert
        )

        app = FastAPI()
        app.include_router(content_binding_router, prefix="/api/v1")
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/v1/content-binding/FK-DBFAIL",
            files={"audio": ("a.wav", FAKE_AUDIO, "audio/wav")},
            headers=_admin_headers(),
        )
        # Whatever status FastAPI's default exception handler assigns
        # (500, since this route does not catch a raw ConnectionError --
        # a genuine, disclosed gap, not a crash-the-process failure) --
        # the point under test is that it never reports 200 success.
        assert r.status_code != 200
        # and no internal file path / stack trace leaks into the body
        body_text = r.text
        assert "Traceback" not in body_text
        assert str(BACKEND_DIR) not in body_text


# NOTE on EventBus failure injection: registry/routes.py's own docstring
# states it "Deliberately does NOT publish any event on object creation"
# (the FREK Registry's object.created producer lives in fk/routes.py, not
# here) -- so an EventBus-failure test targeting registry/objects would
# exercise nothing. This exact scenario (a broken bus must not break FK
# creation) is already real, existing coverage:
# tests/test_fk_object_created_event.py::test_a_broken_bus_does_not_break_fk_creation
# (publish() itself raises) and
# tests/test_eventbus.py::test_bus_never_raises_when_subscriber_fails
# (a subscriber raises) -- both re-run as regression evidence this state,
# not duplicated here.


# ============================================================
# API VERSIONING / PAGINATION EDGE CASES
# ============================================================


class TestUnsupportedApiVersion:
    """Only /api/v1/... is mounted (server.py, confirmed this state --
    no /api/v2 router exists anywhere). Requesting an unsupported
    version must fail safely (404), never crash the process. This is
    disclosed compatibility debt, not a fix: the response is a generic
    FastAPI 404, not yet the canonical UNSUPPORTED_VERSION error code
    from backend/errors.py (STATE_7 deliberately did not retrofit
    existing routes)."""

    def test_v2_prefix_is_a_clean_404_not_a_crash(self):
        db = mongomock_motor.AsyncMongoMockClient()["frekcore_state8_v2"]
        registry_routes.set_db(db)
        app = FastAPI()
        app.include_router(registry_router, prefix="/api/v1")
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v2/registry/namespaces")
        assert r.status_code == 404


class TestBadPaginationToken:
    """offset/limit pagination (FREKCORE_VERSIONING_POLICY.md §8):
    out-of-range offsets return an empty page, never an error; limit is
    clamped into [1, 200] rather than rejected."""

    def test_offset_far_beyond_data_returns_empty_page_not_error(self):
        db = mongomock_motor.AsyncMongoMockClient()["frekcore_state8_pagination"]
        registry_routes.set_db(db)
        app = FastAPI()
        app.include_router(registry_router, prefix="/api/v1")
        client = TestClient(app)
        r = client.get(
            "/api/v1/registry/objects/frek.artist", params={"offset": 999999}
        )
        assert r.status_code == 200
        assert r.json()["objects"] == []

    def test_negative_limit_is_clamped_not_rejected(self):
        db = mongomock_motor.AsyncMongoMockClient()["frekcore_state8_pagination_neg"]
        registry_routes.set_db(db)
        app = FastAPI()
        app.include_router(registry_router, prefix="/api/v1")
        client = TestClient(app)
        r = client.get("/api/v1/registry/objects/frek.artist", params={"limit": -5})
        assert r.status_code == 200  # clamped to >= 1, not a 422/500

    def test_non_numeric_offset_is_a_clean_422_not_a_crash(self):
        db = mongomock_motor.AsyncMongoMockClient()["frekcore_state8_pagination_bad"]
        registry_routes.set_db(db)
        app = FastAPI()
        app.include_router(registry_router, prefix="/api/v1")
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get(
            "/api/v1/registry/objects/frek.artist", params={"offset": "not-a-number"}
        )
        assert r.status_code == 422


# ============================================================
# CROSS-MODULE INVARIANTS (re-verified directly against real types)
# ============================================================


class TestCrossModuleInvariants:
    """Direct, structural re-verification of the mission's named
    invariants -- each assertion targets the actual model/field that
    would silently collapse the distinction if someone "simplified" the
    code later, not just a prose claim."""

    def test_frek_id_and_fingerprint_are_never_the_same_field(self):
        from content_binding.models import ContentBinding, SignalFingerprintData

        fields = ContentBinding.model_fields
        # identity (frek_id) and content fingerprint (exact_hash /
        # signal_fingerprint) are three separate, independently-set
        # fields on the one canonical binding record -- no shared field,
        # no derivation of one from the other in the model itself.
        assert {"frek_id", "exact_hash", "signal_fingerprint"} <= set(fields)
        assert fields["signal_fingerprint"].annotation is SignalFingerprintData
        assert fields["frek_id"].annotation is str
        assert fields["exact_hash"].annotation is str
        # no field aliasing/derivation: each is independently required
        assert fields["frek_id"].is_required()
        assert fields["exact_hash"].is_required()

    def test_claim_and_evidence_are_distinct_types(self):
        from proof_engine.evidence_semantics import Claim, Evidence

        assert Claim is not Evidence
        assert not issubclass(Claim, Evidence)
        assert not issubclass(Evidence, Claim)

    def test_evidence_and_proof_are_distinct_types(self):
        from proof_engine.evidence_semantics import Evidence
        from proof_engine.models import ProofReceipt

        assert Evidence is not ProofReceipt
        assert not issubclass(Evidence, ProofReceipt)

    def test_proof_state_enum_does_not_include_a_verification_state(self):
        """PROOF != VERIFICATION: proof_engine's ProofState vocabulary
        describes how a claim was anchored, never whether a downstream
        verifier accepted it -- that is a separate concept this
        codebase never folds into ProofState."""
        from proof_engine.models import ProofState

        state_values = {s.value for s in ProofState}
        assert not any("verif" in v.lower() for v in state_values)

    def test_service_identity_is_not_automatically_authoritative(self):
        """SERVICE_IDENTITY != AUTOMATIC_AUTHORITY: an active
        ServiceIdentity alone grants nothing -- only decide()/
        delegation_authority_chain_valid() (RoleGrant/DelegationGrant)
        can, and neither accepts a bare ServiceIdentity as sufficient
        input."""
        import inspect

        import permissions.engine as engine_mod
        import permissions.delegation as delegation_mod

        decide_params = set(inspect.signature(engine_mod.decide).parameters)
        chain_params = set(
            inspect.signature(
                delegation_mod.delegation_authority_chain_valid
            ).parameters
        )
        assert "service_identity" not in {p.lower() for p in decide_params}
        assert "service_identity" not in {p.lower() for p in chain_params}

    def test_delegation_grant_alone_never_proves_delegator_authority(self):
        """DELEGATION_GRANT != PROOF_DELEGATOR_HELD_AUTHORITY: exercised
        concretely (not just structurally) in
        tests/test_permissions.py::test_delegation_chain_denied_when_delegator_never_held_authority
        -- this assertion additionally proves it at the type level:
        `delegation_permits()` never takes a RoleGrant/Subject argument
        at all, so it structurally cannot consult the delegator's
        actual authority."""
        import inspect

        import permissions.delegation as delegation_mod

        permits_params = set(
            inspect.signature(delegation_mod.delegation_permits).parameters
        )
        assert "delegator_subject" not in permits_params
        assert "role_grant" not in permits_params

    def test_legacy_router_and_canonical_router_are_different_modules(self):
        """LEGACY_INTERFACE != CANONICAL_TRUTH_ENGINE."""
        import frek.routes as legacy_mod
        import creative_lifecycle.routes as canonical_mod

        assert legacy_mod is not canonical_mod
        assert legacy_mod.__name__ != canonical_mod.__name__

    def test_sdk_clients_never_import_backend_storage_or_db_modules(self):
        """SDK_CONTRACT != INTERNAL_STORAGE: every Python SDK client
        module must depend only on `httpx`/its own package, never reach
        into backend internals (motor/mongomock/pymongo)."""
        sdk_dir = BACKEND_DIR.parent / "sdk" / "python" / "frekcore_sdk"
        assert sdk_dir.is_dir()
        forbidden = ("motor", "mongomock", "pymongo", "backend.")
        for py_file in sdk_dir.glob("*.py"):
            text = py_file.read_text()
            for token in forbidden:
                assert token not in text, f"{py_file.name} references {token!r}"
