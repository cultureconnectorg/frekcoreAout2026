"""D4 -- Offline Proof Transport / Synchronization (founder decision D4,
2026-09-02) -- unit tests.

Same isolated-app technique as test_content_binding_unit.py /
test_creative_lifecycle_unit.py / test_relationship_graph_unit.py:
FastAPI + TestClient + mongomock_motor, no live server/Mongo needed.

Ed25519 signing goes through the real `passport.keys` module (same
signer as `.fk`'s own `ProofLayer.signature`) -- `FREK_PASSPORT_KEY_PATH`
is set to a scratch path before first import, following the exact
established convention in `test_fk_object_created_event.py`. FAP device
attestation goes through the real `frek_v3/reference_verifier/` (via
`offline_transport.fap_adapter`) -- genuine ECDSA proofs are generated
with `frek_device_sim.SimulatedFrekDevice`, never a hand-rolled stub.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-offline-transport-test")
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"
os.environ.setdefault(
    "FREK_PASSPORT_KEY_PATH", "/tmp/frekcore_test_offline_transport_passport_key.pem"
)

import mongomock_motor  # noqa: E402

import offline_transport.routes as ot_routes  # noqa: E402
from offline_transport.routes import offline_transport_router  # noqa: E402
from offline_transport.adapters import encode_envelope, decode_envelope  # noqa: E402
from offline_transport.canonical import (  # noqa: E402
    canonical_json,
    compute_content_hash,
    signable_bytes,
    signable_core,
)
from offline_transport.fap_adapter import generate_test_proof  # noqa: E402
from offline_transport.models import TransportEnvelope, TransportProtocol  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402
from passport import keys as passport_keys  # noqa: E402
from proof_engine.evidence_semantics import Claim, ClaimOrigin  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_offline_transport_test"]
    ot_routes.set_db(db)

    fresh_bus = InProcessEventBus()
    monkeypatch.setattr("eventbus.bus.default_bus", fresh_bus)

    async def _fake_notarize_fail(*args, **kwargs):
        raise RuntimeError("no notary wired in this isolated test app")

    monkeypatch.setattr(
        "notary.service.notarize_event", _fake_notarize_fail, raising=False
    )

    app = FastAPI()
    app.include_router(offline_transport_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db, fresh_bus


def _holder_headers(frek_id: str) -> dict:
    token = identity_service.issue_session_token(frek_id)
    return {"X-FREK-Session": token}


def _admin_headers() -> dict:
    return {"X-Admin-Key": ADMIN_KEY}


def _create(client, headers, **overrides):
    body = {
        "subject_ref": "OBJ-1",
        "subject_type": None,
        "origin": "declared",
        "statement": "actor declares an offline event",
        "data": {},
    }
    body.update(overrides)
    return client.post("/api/v1/offline/envelopes", json=body, headers=headers)


async def _seed_fk_object(db, frek_id: str):
    await db.fk_objects.insert_one({"frek_id": frek_id, "object_type": "song"})


async def _seed_lifecycle_event(db, event_id: str, pre_id: str):
    await db.creative_lifecycle_events.insert_one(
        {"event_id": event_id, "pre_id": pre_id, "stage": "METAMORPHOSE", "sequence": 3}
    )


async def _seed_relationship(db, relationship_id: str):
    await db.relationships.insert_one(
        {"relationship_id": relationship_id, "layer": "trust"}
    )


class TestTransportIndependence:
    """#1: transport envelope is transport-independent. #27: a
    transport adapter cannot override the canonical verification
    result."""

    def test_same_signable_core_regardless_of_adapter_protocol(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope = TransportEnvelope.model_validate(r.json())

        ble_bytes = encode_envelope(envelope, protocol=TransportProtocol.QR)
        wifi_bytes = encode_envelope(envelope, protocol=TransportProtocol.WIFI_LOCAL)

        ble_decoded = decode_envelope(ble_bytes)
        wifi_decoded = decode_envelope(wifi_bytes)

        assert signable_core(ble_decoded) == signable_core(wifi_decoded)
        assert ble_decoded.signature == wifi_decoded.signature
        # Only the adapter-attached metadata differs.
        assert ble_decoded.transport_metadata["protocol"] == "qr"
        assert wifi_decoded.transport_metadata["protocol"] == "wifi_local"


class TestCanonicalSerialization:
    """#2: canonical serialization deterministic."""

    def test_canonical_json_is_key_order_independent(self):
        a = canonical_json({"b": 1, "a": 2, "c": {"z": 1, "y": 2}})
        b = canonical_json({"a": 2, "c": {"y": 2, "z": 1}, "b": 1})
        assert a == b


class TestIntegrityAndSignature:
    """#3: tampering breaks integrity/signature validation."""

    def test_create_produces_valid_signature(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        assert r.status_code == 200
        assert r.json()["signature"]

    def test_receive_detects_tampering(self, app_and_db):
        client, db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]

        envelope = TransportEnvelope.model_validate(r.json())
        envelope.claim.statement = "TAMPERED"
        tampered_bytes = encode_envelope(envelope, protocol=TransportProtocol.QR)

        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={
                "protocol": "qr",
                "envelope_bytes_b64": base64.b64encode(tampered_bytes).decode(),
            },
            headers=_admin_headers(),
        )
        assert recv.status_code == 200
        assert recv.json()["local_validation"] == "invalid"
        assert recv.json()["sync_status"] == "rejected"


class TestAuthorityFreshness:
    """#4: valid signature does not imply current authority. #5: stale
    cached authority is distinguishable from fresh state."""

    def test_default_freshness_caps_at_stale(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={"protocol": "bluetooth_ble"},
            headers=_admin_headers(),
        )
        assert recv.json()["local_validation"] == "crypto_valid_but_status_stale"
        assert recv.json()["sync_status"] == "needs_revalidation"

    def test_explicit_fresh_authority_reaches_locally_acceptable(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={
                "protocol": "bluetooth_ble",
                "freshness": {
                    "status": "current",
                    "checked_at": "2026-09-02T00:00:00+00:00",
                    "source": "test",
                    "ttl_seconds": 999999999,
                },
            },
            headers=_admin_headers(),
        )
        assert recv.json()["local_validation"] == "locally_acceptable"
        assert recv.json()["sync_status"] == "pending"


class TestIdempotencyReplayOrdering:
    """#6: duplicate delivery idempotent. #7: replay detected. #8:
    nonce/sequence work. #9: out-of-order handled. #22: queue
    persists. #23: sync retry safe."""

    def test_receive_twice_is_idempotent(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]
        r1 = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={"protocol": "bluetooth_ble"},
            headers=_admin_headers(),
        )
        r2 = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={"protocol": "bluetooth_ble"},
            headers=_admin_headers(),
        )
        assert r1.json()["sync_status"] == r2.json()["sync_status"]

    def test_sequence_increments_per_issuer(self, app_and_db):
        client, _db, _bus = app_and_db
        r1 = _create(client, _admin_headers())
        r2 = _create(client, _admin_headers())
        assert r2.json()["sequence"] == r1.json()["sequence"] + 1

    def test_nonce_present_and_distinct(self, app_and_db):
        client, _db, _bus = app_and_db
        r1 = _create(client, _admin_headers())
        r2 = _create(client, _admin_headers())
        assert r1.json()["nonce"] and r2.json()["nonce"]
        assert r1.json()["nonce"] != r2.json()["nonce"]

    def _fresh_receive(self, client, envelope_id):
        return client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={
                "protocol": "bluetooth_ble",
                "freshness": {
                    "status": "current",
                    "checked_at": "2026-09-02T00:00:00+00:00",
                    "source": "test",
                    "ttl_seconds": 999999999,
                },
            },
            headers=_admin_headers(),
        )

    def test_out_of_order_event_is_queued_not_reconciled(self, app_and_db):
        client, _db, _bus = app_and_db
        e1 = _create(client, _admin_headers()).json()
        e2 = _create(client, _admin_headers()).json()
        self._fresh_receive(client, e1["envelope_id"])
        self._fresh_receive(client, e2["envelope_id"])

        # EVENT_2 (sequence 2) arrives/syncs before EVENT_1 (sequence 1).
        sync2_first = client.post(
            f"/api/v1/offline/envelopes/{e2['envelope_id']}/sync",
            headers=_admin_headers(),
        )
        assert sync2_first.json()["sync_status"] == "needs_revalidation"
        assert (
            sync2_first.json()["rejection_reason"] == "waiting_for_predecessor_sequence"
        )

        sync1 = client.post(
            f"/api/v1/offline/envelopes/{e1['envelope_id']}/sync",
            headers=_admin_headers(),
        )
        assert sync1.json()["sync_status"] == "synced"

        sync2_second = client.post(
            f"/api/v1/offline/envelopes/{e2['envelope_id']}/sync",
            headers=_admin_headers(),
        )
        assert sync2_second.json()["sync_status"] == "synced"

    def test_replay_of_an_already_reconciled_sequence_is_rejected(self, app_and_db):
        client, db, _bus = app_and_db
        e1 = _create(client, _admin_headers()).json()
        self._fresh_receive(client, e1["envelope_id"])
        synced = client.post(
            f"/api/v1/offline/envelopes/{e1['envelope_id']}/sync",
            headers=_admin_headers(),
        )
        assert synced.json()["sync_status"] == "synced"

        # A second, distinct envelope independently claims the SAME
        # (issuer, sequence) slot -- e.g. two offline devices picking
        # the same local sequence number. Inserted directly, since the
        # API always mints a fresh monotonic sequence itself.
        duplicate_doc = dict(synced.json())
        duplicate_doc["envelope_id"] = "replayed-envelope"
        duplicate_doc["sync_status"] = "pending"
        asyncio.run(db.transport_envelopes.insert_one(dict(duplicate_doc)))

        replay_sync = client.post(
            "/api/v1/offline/envelopes/replayed-envelope/sync", headers=_admin_headers()
        )
        assert replay_sync.json()["sync_status"] == "rejected"
        assert replay_sync.json()["rejection_reason"] == "replay"

    def test_queue_persists_and_lists_pending(self, app_and_db):
        client, db, _bus = app_and_db
        _create(client, _admin_headers())
        queue = client.get("/api/v1/offline/envelopes/queue", headers=_admin_headers())
        assert queue.json()["count"] == 1

        # A second app instance sharing the SAME db sees the same queue
        # -- proving persistence is not tied to in-process app state.
        app2 = FastAPI()
        app2.include_router(offline_transport_router, prefix="/api/v1")
        client2 = TestClient(app2)
        queue2 = client2.get(
            "/api/v1/offline/envelopes/queue", headers=_admin_headers()
        )
        assert queue2.json()["count"] == 1

    def test_sync_retry_on_already_synced_is_safe(self, app_and_db):
        client, _db, bus = app_and_db
        e1 = _create(client, _admin_headers()).json()
        self._fresh_receive(client, e1["envelope_id"])
        client.post(
            f"/api/v1/offline/envelopes/{e1['envelope_id']}/sync",
            headers=_admin_headers(),
        )

        received_events = []
        bus.subscribe(
            "offline_transport.envelope_recorded", lambda ev: received_events.append(ev)
        )
        again = client.post(
            f"/api/v1/offline/envelopes/{e1['envelope_id']}/sync",
            headers=_admin_headers(),
        )
        assert again.json()["sync_status"] == "synced"
        # No new event published for a no-op retry.
        assert received_events == []


class TestConflict:
    """#10: conflicts preserve history."""

    def test_conflicting_envelope_at_same_sequence_is_flagged_not_overwritten(
        self, app_and_db
    ):
        client, db, _bus = app_and_db
        e1 = _create(client, _admin_headers()).json()

        # A second, independently-signed envelope that happens to claim
        # the SAME (issuer, sequence) slot as e1 -- e.g. two offline
        # devices that each picked local sequence 1. Hand-built (not
        # via POST /envelopes, which always mints a fresh monotonic
        # sequence) and genuinely, validly signed with the real signer,
        # so it reaches the conflict check on its own cryptographic
        # merit, not because its signature was left stale.
        conflicting = TransportEnvelope(
            envelope_id="conflicting-envelope",
            authority="admin",
            subject_ref="OBJ-1",
            claim=Claim(
                subject_id="conflicting-envelope",
                origin=ClaimOrigin.DECLARED,
                statement="a different offline device's own assertion",
            ),
            content_hash="",
            sequence=e1["sequence"],
            nonce="ff" * 16,
        )
        conflicting.content_hash = compute_content_hash(conflicting)
        conflicting.signature = base64.b64encode(
            passport_keys.sign(signable_bytes(conflicting))
        ).decode("ascii")
        asyncio.run(
            db.transport_envelopes.insert_one(dict(conflicting.to_public_dict()))
        )

        # Reconcile e1 first.
        recv1 = client.post(
            f"/api/v1/offline/envelopes/{e1['envelope_id']}/receive",
            json={
                "protocol": "bluetooth_ble",
                "freshness": {
                    "status": "current",
                    "checked_at": "2026-09-02T00:00:00+00:00",
                    "source": "test",
                    "ttl_seconds": 999999999,
                },
            },
            headers=_admin_headers(),
        )
        assert recv1.status_code == 200
        client.post(
            f"/api/v1/offline/envelopes/{e1['envelope_id']}/sync",
            headers=_admin_headers(),
        )

        conflict_sync = client.post(
            "/api/v1/offline/envelopes/conflicting-envelope/sync",
            headers=_admin_headers(),
        )
        assert conflict_sync.json()["sync_status"] == "conflict"

        # Both records still exist -- neither was overwritten/deleted.
        both = asyncio.run(db.transport_envelopes.count_documents({}))
        assert both == 2


class TestClockAndReconciliation:
    """#11: device timestamp != authoritative timestamp. #12: offline
    acceptance != final reconciliation."""

    def test_device_time_distinct_from_issued_at_and_verifier_time(self, app_and_db):
        client, db, _bus = app_and_db
        proof = generate_test_proof()
        assert proof is not None
        asyncio.run(
            db.fap_devices.insert_one(
                {
                    "device_id_hex": proof["device_id_hex"],
                    "ak_pub_hex": proof["ak_pub_hex"],
                    "status": "ACTIVE",
                    "last_counter": 0,
                    "trusted_firmware_hashes_hex": [proof["firmware_hash_hex"]],
                }
            )
        )
        r = _create(
            client,
            _admin_headers(),
            device_attestation={"scheme": "fap_l2", "proof_hex": proof["proof_hex"]},
        )
        envelope_id = r.json()["envelope_id"]
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={"protocol": "bluetooth_ble"},
            headers=_admin_headers(),
        )
        result = recv.json()["device_attestation_result"]
        assert result["accepted"] is True
        # device_time (device-declared) is a distinct field from
        # issued_at (this envelope's own server-assigned issuance time)
        # and verifier_time (computed fresh by FAP's own verifier).
        assert result["device_time"] != r.json()["issued_at"]
        assert result["verifier_time"] != result["device_time"]

    def test_receive_acceptance_never_sets_sync_status_synced(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={
                "protocol": "bluetooth_ble",
                "freshness": {
                    "status": "current",
                    "checked_at": "2026-09-02T00:00:00+00:00",
                    "source": "test",
                    "ttl_seconds": 999999999,
                },
            },
            headers=_admin_headers(),
        )
        assert recv.json()["local_validation"] == "locally_acceptable"
        assert recv.json()["sync_status"] != "synced"


class TestRevocation:
    """#13: revoked authority detected after sync."""

    def test_device_revoked_between_receive_and_sync_is_caught_at_sync(
        self, app_and_db
    ):
        client, db, _bus = app_and_db
        proof = generate_test_proof()
        asyncio.run(
            db.fap_devices.insert_one(
                {
                    "device_id_hex": proof["device_id_hex"],
                    "ak_pub_hex": proof["ak_pub_hex"],
                    "status": "ACTIVE",
                    "last_counter": 0,
                    "trusted_firmware_hashes_hex": [proof["firmware_hash_hex"]],
                }
            )
        )
        r = _create(
            client,
            _admin_headers(),
            device_attestation={"scheme": "fap_l2", "proof_hex": proof["proof_hex"]},
        )
        envelope_id = r.json()["envelope_id"]
        client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={
                "protocol": "bluetooth_ble",
                "freshness": {
                    "status": "current",
                    "checked_at": "2026-09-02T00:00:00+00:00",
                    "source": "test",
                    "ttl_seconds": 999999999,
                },
            },
            headers=_admin_headers(),
        )

        revoke = client.post(
            f"/api/v1/offline/devices/{proof['device_id_hex']}/revoke",
            headers=_admin_headers(),
        )
        assert revoke.status_code == 200

        sync = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/sync", headers=_admin_headers()
        )
        assert sync.json()["sync_status"] == "rejected"
        assert sync.json()["rejection_reason"] == "device_attestation_failed"
        assert sync.json()["device_attestation_result"]["code"] == "DEVICE_REVOKED"


class TestMalformedAndOversized:
    """#14: malformed envelope fails safely. #15: oversized payload
    rejected. #16: unknown issuer handled safely. #17: unsupported
    signature algorithm rejected."""

    def test_malformed_envelope_bytes_is_400(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={
                "protocol": "bluetooth_ble",
                "envelope_bytes_b64": base64.b64encode(b"not json").decode(),
            },
            headers=_admin_headers(),
        )
        assert recv.status_code == 400

    def test_oversized_envelope_bytes_is_413(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]
        huge = base64.b64encode(b"x" * (ot_routes.MAX_ENVELOPE_BYTES + 1)).decode()
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={"protocol": "bluetooth_ble", "envelope_bytes_b64": huge},
            headers=_admin_headers(),
        )
        assert recv.status_code == 413

    def test_unknown_device_is_handled_safely_not_crashed(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            device_attestation={"scheme": "fap_l2", "proof_hex": "00" * 283},
        )
        envelope_id = r.json()["envelope_id"]
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={"protocol": "bluetooth_ble"},
            headers=_admin_headers(),
        )
        assert recv.status_code == 200
        assert recv.json()["device_attestation_result"]["accepted"] is False

    def test_unsupported_signature_algorithm_rejected(self, app_and_db):
        client, db, _bus = app_and_db
        r = _create(client, _admin_headers())
        envelope_id = r.json()["envelope_id"]
        asyncio.run(
            db.transport_envelopes.update_one(
                {"envelope_id": envelope_id}, {"$set": {"signature_algo": "rsa-4096"}}
            )
        )
        recv = client.post(
            f"/api/v1/offline/envelopes/{envelope_id}/receive",
            json={"protocol": "bluetooth_ble"},
            headers=_admin_headers(),
        )
        assert recv.json()["local_validation"] == "invalid"


class TestD6D1D2D3Reuse:
    """#18: D6 semantics preserved. #19: D1 references reused, not
    recomputed. #20: D2 lifecycle event transportable. #21: D3
    relationship transportable."""

    def test_envelope_round_trips_through_real_claim_evidence_types(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), origin="computed", data={"x": 1})
        envelope = TransportEnvelope.model_validate(r.json())
        assert envelope.claim.origin.value == "computed"
        assert envelope.evidence[0].kind.value == "computation"

    def test_no_dsp_reimplementation_in_offline_transport_source(self):
        for name in (
            "models",
            "service",
            "routes",
            "adapters",
            "canonical",
            "fap_adapter",
        ):
            src = open(BACKEND_DIR / "offline_transport" / f"{name}.py").read()
            assert "node01_extraction" not in src
            assert "import librosa" not in src

    def test_creative_lifecycle_event_can_be_referenced(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_lifecycle_event(db, "EVT-1", "PRE-1"))
        r = _create(client, _admin_headers(), creative_lifecycle_event_id="EVT-1")
        assert r.status_code == 200
        assert r.json()["creative_lifecycle_event_id"] == "EVT-1"

    def test_unknown_creative_lifecycle_event_is_404(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), creative_lifecycle_event_id="EVT-NOPE")
        assert r.status_code == 404

    def test_relationship_can_be_referenced(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_relationship(db, "rel-1"))
        r = _create(client, _admin_headers(), relationship_id="rel-1")
        assert r.status_code == 200
        assert r.json()["relationship_id"] == "rel-1"

    def test_unknown_relationship_is_404(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), relationship_id="rel-nope")
        assert r.status_code == 404

    def test_unknown_content_binding_is_404(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), content_binding_id="CB-NOPE")
        assert r.status_code == 404


class TestAuditEventbus:
    """#24, #25: audit records transitions, Event Bus integration
    works."""

    def test_create_receive_sync_each_publish_an_event(self, app_and_db):
        client, _db, bus = app_and_db
        received = []
        bus.subscribe(
            "offline_transport.envelope_recorded", lambda ev: received.append(ev)
        )

        e = _create(client, _admin_headers()).json()
        client.post(
            f"/api/v1/offline/envelopes/{e['envelope_id']}/receive",
            json={
                "protocol": "bluetooth_ble",
                "freshness": {
                    "status": "current",
                    "checked_at": "2026-09-02T00:00:00+00:00",
                    "source": "test",
                    "ttl_seconds": 999999999,
                },
            },
            headers=_admin_headers(),
        )
        client.post(
            f"/api/v1/offline/envelopes/{e['envelope_id']}/sync",
            headers=_admin_headers(),
        )

        transitions = [ev.payload["transition"] for ev in received]
        assert transitions == ["created", "received", "synced"]


class TestHistoricalRoutesUnchanged:
    """#26: historical D4 routes remain preserved."""

    def test_offline_transport_does_not_import_backend_frek_routes(self):
        src = open(BACKEND_DIR / "offline_transport" / "routes.py").read()
        assert "from frek.routes import" not in src
        assert "from frek.routes_advanced import" not in src
        assert "import routes_advanced" not in src

    def test_historical_transmission_route_count_is_still_six(self):
        advanced_py = (BACKEND_DIR / "frek" / "routes_advanced.py").read_text(
            encoding="utf-8"
        )
        count = advanced_py.count(
            '@advanced_router.get("/transmission'
        ) + advanced_py.count('@advanced_router.post("/transmission')
        assert count == 6


class TestWatermarkNotProof:
    """#28: watermark does not become proof."""

    def test_watermark_response_explicitly_not_proof(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.post(
            "/api/v1/offline/watermark",
            params={"frek_id": "FK-1"},
            headers=_admin_headers(),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["proof"] is False
        assert body["validation_status"] == "NOT_TESTED"

    def test_watermark_module_never_imported_by_service_or_canonical(self):
        # Structural check: no *import* of watermark.py from the trust-
        # bearing modules -- the word itself legitimately appears in
        # their docstrings when explaining the WATERMARK_EQUALS_PROOF
        # invariant, which is not what this test guards against.
        for name in ("service", "canonical", "models"):
            src = open(BACKEND_DIR / "offline_transport" / f"{name}.py").read()
            assert "import watermark" not in src
            assert "from .watermark" not in src


class TestUnauthorized:
    def test_no_credentials_create_is_403(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, {})
        assert r.status_code == 403

    def test_holder_cannot_self_assert_computed_origin(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _holder_headers("ARTIST-1"), origin="computed")
        assert r.status_code == 403
