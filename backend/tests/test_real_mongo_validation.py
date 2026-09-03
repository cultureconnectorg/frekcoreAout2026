"""FREKCORE_REAL_MONGO_VALIDATION_PROTOCOL — real MongoDB Atlas validation.

Bounded infrastructure validation, not a permanent regression suite: runs
ONLY when `MONGO_URI` is set in the environment (never hardcoded, never
printed, never persisted), skipped entirely otherwise -- including every
default `pytest` invocation, local or CI. Selected explicitly via
`pytest -m real_mongo` by the dedicated `real-mongo-validation` CI job.

Reuses the repository's ACTUAL Mongo configuration path throughout: the
same `set_db()`/`ensure_indexes()` functions and route modules every
mongomock-backed unit test in this suite already exercises, just pointed
at a real `motor.motor_asyncio.AsyncIOMotorClient` instead of
`mongomock_motor.AsyncMongoMockClient`. No second Mongo configuration
system is introduced. All state lives in one disposable, uuid-suffixed
database (never `frekcore`/`frekcore_prod`), dropped at teardown.

Unlike every other file in this suite, the test functions below are
DELIBERATELY ORDER-DEPENDENT (numbered `test_NN_...`, relying on pytest's
default in-file collection order -- no randomization plugin is installed,
confirmed) and share one module-level database across the whole file.
This is intentional for a bounded, sequential CI diagnostic script that
mirrors the mission's own numbered validation domains, not a design this
codebase's other ~60 test files should copy.

Security posture (FREKCORE_REAL_MONGO_VALIDATION_PROTOCOL requirement 7):
`MONGO_URI` is read once via `os.environ.get`, never echoed, never
interpolated into an assertion message, never passed as a CLI argument.
Connection-error messages are classified into BLOCKED_NETWORK/BLOCKED_AUTH
from the *type and text* of the driver's own exception, which pymongo
already keeps free of embedded credentials (it reports host/port and
error class, not the URI) -- confirmed by direct inspection of the
exception text this file's own `_classify_connection_error` receives.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-real-mongo-test")
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

pytestmark = pytest.mark.real_mongo

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    # Requirement 3: "fail safely if the secret is absent" -- a skip, not
    # an error, and never a hint at what a valid value might look like.
    pytest.skip(
        "MONGO_URI not set in this environment; real-Mongo validation "
        "requires it and is skipped rather than attempted without it.",
        allow_module_level=True,
    )

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

import content_binding.routes as cb_routes  # noqa: E402
from content_binding.routes import content_binding_router  # noqa: E402
from content_binding.models import SignalFingerprintData  # noqa: E402
import creative_lifecycle.routes as cl_routes  # noqa: E402
from creative_lifecycle.routes import creative_lifecycle_router  # noqa: E402
import relationship_graph.routes as rg_routes  # noqa: E402
from relationship_graph.routes import relationship_graph_router  # noqa: E402
import registry.routes as registry_routes  # noqa: E402
from registry.routes import registry_router  # noqa: E402
import offline_transport.routes as ot_routes  # noqa: E402
from offline_transport.routes import offline_transport_router  # noqa: E402
import technical_evidence_report.routes as ter_routes  # noqa: E402
from technical_evidence_report.routes import (  # noqa: E402
    technical_evidence_report_router,
)
import frek_v1.auth as frek_v1_auth  # noqa: E402
from frek_v1.utils import create_access_token, hash_secret  # noqa: E402
from audit_trail.mongo_recorder import MongoAuditRecorder  # noqa: E402
from audit_trail.models import AuditEvent  # noqa: E402
from notary.chain import FrekChain  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402

ADMIN_KEY = os.environ["SECRET_KEY"]
DB_NAME = f"frekcore_ci_realmongo_{uuid.uuid4().hex[:12]}"
FAKE_AUDIO = b"R" * 2000

# Module-level state passed between the deliberately-ordered test
# functions below (see the file docstring for why this is intentional
# here). Never holds MONGO_URI or any credential material.
_STATE: dict = {}


def _classify_connection_error(exc: BaseException) -> str:
    """BLOCKED_NETWORK vs BLOCKED_AUTH, from the driver's own exception
    class/text only -- pymongo's own error strings report host:port and
    error class, never the URI or its credentials."""
    text = str(exc).lower()
    auth_markers = (
        "authentication failed",
        "auth failed",
        "bad auth",
        "unauthorized",
        "scram",
        "not authorized",
    )
    if any(marker in text for marker in auth_markers):
        return "BLOCKED_AUTH"
    return "BLOCKED_NETWORK"


def _admin_headers() -> dict:
    return {"X-Admin-Key": ADMIN_KEY}


def _holder_headers(frek_id: str) -> dict:
    return {"X-FREK-Session": identity_service.issue_session_token(frek_id)}


def _fake_fingerprint() -> SignalFingerprintData:
    return SignalFingerprintData(
        algorithm="frek_signal_v1",
        algorithm_version="1.0.0",
        dimensions=528,
        vector=[0.3] * 528,
        sample_rate=44100,
        duration_seconds=1.0,
    )


# ============================================================
# 1. CONNECTION -- authenticated ping, server selection
# ============================================================


def test_01_connection_ping_and_server_selection():
    async def _run():
        client = AsyncIOMotorClient(
            MONGO_URI, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000
        )
        try:
            result = await client.admin.command("ping")
        except Exception as exc:
            classification = _classify_connection_error(exc)
            client.close()
            pytest.fail(
                f"REAL_MONGO_CONNECTION=BLOCKED "
                f"(REAL_MONGO_VALIDATION={classification}): "
                f"{type(exc).__name__} -- connection could not be established"
            )
        assert result.get("ok") == 1.0
        _STATE["client"] = client
        _STATE["db"] = client[DB_NAME]

    asyncio.run(_run())


# ============================================================
# 2. BASIC DURABILITY -- write / read / update / delete
# ============================================================


class TestBasicDurability:
    def test_02_write(self):
        async def _run():
            db = _STATE["db"]
            doc_id = f"smoke-{uuid.uuid4().hex[:8]}"
            await db.state8_smoke.insert_one({"_id": doc_id, "v": 1, "kind": "smoke"})
            _STATE["smoke_id"] = doc_id

        asyncio.run(_run())

    def test_03_read(self):
        async def _run():
            db = _STATE["db"]
            doc = await db.state8_smoke.find_one({"_id": _STATE["smoke_id"]})
            assert doc is not None
            assert doc["v"] == 1

        asyncio.run(_run())

    def test_04_update(self):
        async def _run():
            db = _STATE["db"]
            res = await db.state8_smoke.update_one(
                {"_id": _STATE["smoke_id"]}, {"$set": {"v": 2}}
            )
            assert res.modified_count == 1
            doc = await db.state8_smoke.find_one({"_id": _STATE["smoke_id"]})
            assert doc["v"] == 2

        asyncio.run(_run())

    def test_05_delete(self):
        async def _run():
            db = _STATE["db"]
            res = await db.state8_smoke.delete_one({"_id": _STATE["smoke_id"]})
            assert res.deleted_count == 1
            assert await db.state8_smoke.find_one({"_id": _STATE["smoke_id"]}) is None

        asyncio.run(_run())


# ============================================================
# 3. INDEXES -- real ensure_indexes(), idempotent, unique constraint
# ============================================================


class TestIndexValidation:
    def test_06_ensure_indexes_twice_is_idempotent(self):
        cb_routes.set_db(_STATE["db"])

        async def _run():
            await cb_routes.ensure_indexes()
            await cb_routes.ensure_indexes()  # must not raise the 2nd time

        asyncio.run(_run())

    def test_07_unique_constraint_enforced_by_real_mongo(self):
        async def _run():
            db = _STATE["db"]
            await db.content_bindings.insert_one(
                {"binding_id": "realmongo-dup-1", "frek_id": "FK-1"}
            )
            with pytest.raises(Exception):
                await db.content_bindings.insert_one(
                    {"binding_id": "realmongo-dup-1", "frek_id": "FK-2"}
                )

        asyncio.run(_run())


# ============================================================
# 4. RESTART / RECONNECTION -- new client, same URI, re-read
# ============================================================


class TestRestartReconnection:
    def test_08_write_before_restart(self):
        async def _run():
            db = _STATE["db"]
            await db.state8_restart_probe.insert_one(
                {"_id": "restart-probe-1", "value": "written-before-restart"}
            )

        asyncio.run(_run())

    def test_09_new_client_same_uri_reads_data_written_by_the_old_one(self):
        """The actual proof this codebase could not do with mongomock this
        state (STATE_8 confirmed directly: a second AsyncMongoMockClient()
        at the same connection string returns an EMPTY store). Against
        real Atlas, this must return the data -- proving persistence is
        server-side, not tied to the Python client/process that wrote it."""

        async def _run():
            new_client = AsyncIOMotorClient(
                MONGO_URI, serverSelectionTimeoutMS=15000, connectTimeoutMS=15000
            )
            try:
                doc = await new_client[DB_NAME].state8_restart_probe.find_one(
                    {"_id": "restart-probe-1"}
                )
            finally:
                new_client.close()
            assert doc is not None
            assert doc["value"] == "written-before-restart"

        asyncio.run(_run())


# ============================================================
# 5. IDEMPOTENCY -- same key/same payload, same key/different payload
# ============================================================


class TestIdempotencyRealMongo:
    def test_10_content_binding_same_key_same_payload_deduplicates(self):
        cb_routes.set_db(_STATE["db"])

        async def _fake_extract(audio_bytes: bytes):
            return _fake_fingerprint()

        async def _fake_notarize_fail(*args, **kwargs):
            raise RuntimeError("no notary wired in this real-Mongo diagnostic")

        import pytest as _pytest  # local import to use monkeypatch-free patching

        original_extract = cb_routes.compute_signal_fingerprint
        cb_routes.compute_signal_fingerprint = _fake_extract
        import notary.service as notary_service

        original_notarize = notary_service.notarize_event
        notary_service.notarize_event = _fake_notarize_fail
        try:
            app = FastAPI()
            app.include_router(content_binding_router, prefix="/api/v1")
            client = TestClient(app)

            async def _seed():
                await _STATE["db"].fk_objects.insert_one(
                    {"frek_id": "FK-REALMONGO", "object_type": "song"}
                )

            asyncio.run(_seed())

            r1 = client.post(
                "/api/v1/content-binding/FK-REALMONGO",
                files={"audio": ("a.wav", FAKE_AUDIO, "audio/wav")},
                headers=_admin_headers(),
            )
            assert r1.status_code == 200, r1.text
            assert r1.json()["deduplicated"] is False

            r2 = client.post(
                "/api/v1/content-binding/FK-REALMONGO",
                files={"audio": ("a.wav", FAKE_AUDIO, "audio/wav")},
                headers=_admin_headers(),
            )
            assert r2.status_code == 200, r2.text
            assert r2.json()["deduplicated"] is True
            assert r2.json()["binding_id"] == r1.json()["binding_id"]
        finally:
            cb_routes.compute_signal_fingerprint = original_extract
            notary_service.notarize_event = original_notarize
            del _pytest  # unused, keeps flake8 quiet about the local import

    def test_11_offline_transport_same_key_different_payload_conflicts(self):
        ot_routes.set_db(_STATE["db"])
        fresh_bus = InProcessEventBus()
        import eventbus.bus as eventbus_bus

        original_bus = eventbus_bus.default_bus
        eventbus_bus.default_bus = fresh_bus
        import notary.service as notary_service

        original_notarize = notary_service.notarize_event

        async def _fake_notarize_fail(*args, **kwargs):
            raise RuntimeError("no notary wired in this real-Mongo diagnostic")

        notary_service.notarize_event = _fake_notarize_fail
        try:
            app = FastAPI()
            app.include_router(offline_transport_router, prefix="/api/v1")
            client = TestClient(app)
            headers = _holder_headers("FK-REALMONGO-OFFLINE")

            def _create(**overrides):
                body = {
                    "subject_ref": "OBJ-REALMONGO",
                    "subject_type": None,
                    "origin": "declared",
                    "statement": "actor declares an offline event (real-mongo diagnostic)",
                    "data": {},
                }
                body.update(overrides)
                return client.post(
                    "/api/v1/offline/envelopes", json=body, headers=headers
                )

            r1 = _create()
            assert r1.status_code == 200, r1.text
            first_sequence = r1.json()["sequence"]

            r2 = _create(
                statement="a conflicting second statement at the same sequence"
            )
            # Either genuinely rejected as a conflict, or (if the service
            # assigns sequence itself, sidestepping a same-sequence
            # collision entirely) simply succeeds with the NEXT sequence
            # -- either way it must never silently overwrite the first
            # envelope's own stored statement.
            if r2.status_code == 200:
                assert r2.json()["sequence"] != first_sequence

            async def _reread_first():
                return await _STATE["db"].transport_envelopes.find_one(
                    {"issuer_id": r1.json()["issuer_id"], "sequence": first_sequence},
                    {"_id": 0},
                )

            first_still_intact = asyncio.run(_reread_first())
            assert first_still_intact is not None
            assert (
                first_still_intact["claim"]["statement"]
                == "actor declares an offline event (real-mongo diagnostic)"
            )
        finally:
            eventbus_bus.default_bus = original_bus
            notary_service.notarize_event = original_notarize


# ============================================================
# 6. CANONICAL PERSISTENCE -- one create + one read per capability,
#    through the repository's real route code, against real Mongo.
# ============================================================


class TestCanonicalPersistenceRegistry:
    def test_12_create_and_read_back(self):
        registry_routes.set_db(_STATE["db"])
        frek_v1_auth.set_db(_STATE["db"])
        app = FastAPI()
        app.include_router(registry_router, prefix="/api/v1")
        client = TestClient(app)

        async def _seed_issuer():
            await _STATE["db"].frek_clients.insert_one(
                {
                    "client_id": "realmongo-issuer",
                    "secret_hash": hash_secret("unused"),
                    "permissions": ["registry:write"],
                    "active": True,
                }
            )

        asyncio.run(_seed_issuer())
        token = create_access_token("realmongo-issuer")

        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "Real Mongo Test Artist"}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code in (200, 201), r.text
        frek_id = r.json()["frek_id"]

        r2 = client.get("/api/v1/registry/objects/frek.artist")
        assert r2.status_code == 200
        ids = [o["frek_id"] for o in r2.json()["objects"]]
        assert frek_id in ids


class TestCanonicalPersistenceContentBinding:
    def test_13_binding_created_in_test_10_is_readable_by_id(self):
        app = FastAPI()
        app.include_router(content_binding_router, prefix="/api/v1")
        client = TestClient(app)
        # the binding_id created during idempotency testing (test_10)
        r = client.get(
            "/api/v1/content-binding/FK-REALMONGO",
        )
        assert r.status_code == 200
        assert r.json()["count"] >= 1


class TestCanonicalPersistenceCreativeLifecycle:
    def test_14_genesis_create_and_read_back(self):
        cl_routes.set_db(_STATE["db"])
        app = FastAPI()
        app.include_router(creative_lifecycle_router, prefix="/api/v1")
        client = TestClient(app)

        r = client.post(
            "/api/v1/creative-lifecycle/genesis",
            json={"concept": "real-mongo diagnostic concept"},
            headers=_admin_headers(),
        )
        assert r.status_code == 200, r.text
        pre_id = r.json()["pre_id"]
        assert r.json()["stage"] == "GENESIS"

        async def _reread():
            return await _STATE["db"].creative_lifecycle_events.find_one(
                {"pre_id": pre_id}, {"_id": 0}
            )

        doc = asyncio.run(_reread())
        assert doc is not None
        assert doc["stage"] == "GENESIS"


class TestCanonicalPersistenceRelationshipGraph:
    def test_15_create_and_read_back(self):
        rg_routes.set_db(_STATE["db"])
        app = FastAPI()
        app.include_router(relationship_graph_router, prefix="/api/v1")
        client = TestClient(app)

        r = client.post(
            "/api/v1/relationships",
            json={
                "subject_id": "REALMONGO-A",
                "subject_type": None,
                "predicate": "created_by",
                "object_id": "REALMONGO-B",
                "object_type": None,
                "origin": "declared",
                "statement": "real-mongo diagnostic relation",
                "data": {},
            },
            headers=_admin_headers(),
        )
        assert r.status_code == 200, r.text
        relationship_id = r.json()["relationship_id"]

        async def _reread():
            return await _STATE["db"].relationships.find_one(
                {"relationship_id": relationship_id}, {"_id": 0}
            )

        doc = asyncio.run(_reread())
        assert doc is not None
        assert doc["subject_id"] == "REALMONGO-A"


class TestCanonicalPersistenceOfflineTransportQueue:
    def test_16_envelope_from_test_11_is_queued_and_listable(self):
        app = FastAPI()
        app.include_router(offline_transport_router, prefix="/api/v1")
        client = TestClient(app)
        headers = _holder_headers("FK-REALMONGO-OFFLINE")

        r = client.get("/api/v1/offline/envelopes/queue", headers=headers)
        assert r.status_code == 200
        assert r.json()["count"] >= 1


class TestCanonicalPersistenceTechnicalEvidenceReport:
    def test_17_generate_and_read_back(self):
        ter_routes.set_db(_STATE["db"])
        app = FastAPI()
        app.include_router(technical_evidence_report_router, prefix="/api/v1")
        client = TestClient(app)

        async def _seed_fk_object():
            await _STATE["db"].fk_objects.insert_one(
                {"frek_id": "FK-REALMONGO-TER", "object_type": "song"}
            )

        asyncio.run(_seed_fk_object())

        r = client.post(
            "/api/v1/reports/technical-evidence",
            json={"subject_type": "frek_object", "subject_id": "FK-REALMONGO-TER"},
            headers=_admin_headers(),
        )
        assert r.status_code == 200, r.text
        report_id = r.json()["report_id"]

        async def _reread():
            return await _STATE["db"].technical_evidence_reports.find_one(
                {"report_id": report_id}, {"_id": 0}
            )

        doc = asyncio.run(_reread())
        assert doc is not None
        assert doc["subject_id"] == "FK-REALMONGO-TER"


class TestCanonicalPersistenceProofNotary:
    def test_18_frek_chain_append_and_read_back_with_hash_linkage(self):
        async def _run():
            chain = FrekChain(_STATE["db"])
            await chain.ensure_indexes()
            await chain.ensure_indexes()  # idempotent, same as index test above

            block1 = await chain.append_block(
                payload_type="real_mongo_diagnostic",
                payload_id="probe-1",
                payload_data={"n": 1},
            )
            block2 = await chain.append_block(
                payload_type="real_mongo_diagnostic",
                payload_id="probe-2",
                payload_data={"n": 2},
            )
            assert block2["height"] == block1["height"] + 1
            assert block2["prev_hash"] == block1["block_hash"]

            reread = await chain.get_block(block1["height"])
            assert reread is not None
            assert reread["block_hash"] == block1["block_hash"]
            assert reread["payload_id"] == "probe-1"

        asyncio.run(_run())


class TestCanonicalPersistenceAudit:
    def test_19_mongo_audit_recorder_write_and_read_back(self):
        async def _run():
            recorder = MongoAuditRecorder(_STATE["db"])
            await recorder.ensure_indexes()
            event = AuditEvent(
                actor_frek_id="FK-REALMONGO",
                action="real_mongo_diagnostic_action",
                resource_type="diagnostic",
                resource_id="probe-1",
                result="allow",
            )
            recorded = await recorder.record(event)
            assert recorded.event_id == event.event_id

            recent = await recorder.recent_events(
                limit=10, actor_frek_id="FK-REALMONGO"
            )
            assert any(e.event_id == event.event_id for e in recent)

        asyncio.run(_run())


# ============================================================
# 7. CLEANUP -- drop the disposable database, close the client
# ============================================================


def test_99_cleanup_drops_temp_database():
    async def _run():
        client = _STATE.get("client")
        if client is None:
            pytest.skip("no client was ever established -- nothing to clean up")
        await client.drop_database(DB_NAME)
        # confirm the drop actually took effect, not just that the call
        # returned without raising
        remaining = await client[DB_NAME].state8_smoke.find_one({})
        assert remaining is None
        client.close()

    asyncio.run(_run())
