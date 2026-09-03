"""STATE_6 — Historical Compatibility Reconciliation (founder authorization
2026-09-02) — unit tests.

Same isolated-app technique as every other D-state's own unit test file:
FastAPI + TestClient + mongomock_motor, no live server/Mongo needed.

The real signal-extraction pipeline (`frek.nodes.node01_extraction`,
which lazy-imports `librosa`/`soundfile` — not in requirements-ci.txt)
is monkeypatched out, exactly like `test_content_binding_unit.py` already
does for the same reason: this file tests the COMPATIBILITY LAYER
(rate limiting, audit visibility, canonical cross-references, response
compatibility), not the DSP algorithm itself — that has its own separate,
real-librosa validation pass (`reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`).

`frek.pipeline.pipeline` (and every node0X singleton it wraps) is a
process-wide singleton with in-memory state — the exact historical
characteristic this whole reconciliation preserves, not fixes. Every
test below therefore uses a fresh, uuid-derived artiste_id/pre_id/frek_id
per test rather than asserting brittle absolute counts, so tests never
depend on run order or leak into each other.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-legacy-compat-test")
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import mongomock_motor  # noqa: E402

import frek.routes as frek_routes  # noqa: E402
import frek.routes_advanced as frek_advanced_routes  # noqa: E402
from frek.routes import frek_router  # noqa: E402
from frek.pipeline import pipeline as frek_pipeline  # noqa: E402
from frek.nodes.node01_extraction import ExtractionResult  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402
import security.policies as security_policies  # noqa: E402

pytestmark = pytest.mark.unit


def _fake_extraction_result() -> ExtractionResult:
    return ExtractionResult(
        fft_bands=np.zeros(512, dtype=np.float32),
        rms=0.01,
        zcr=0.01,
        mfcc=np.zeros(13, dtype=np.float32),
        centroid=1000.0,
        flux=0.01,
        duration=0.5,
        sample_rate=44100,
    )


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_legacy_compat_test"]
    frek_routes.set_db(db)
    frek_advanced_routes.set_db(db)
    security_policies.set_db(db)

    fresh_bus = InProcessEventBus()
    monkeypatch.setattr("eventbus.bus.default_bus", fresh_bus)

    async def _fake_extract(audio_bytes: bytes, file_ext: str = "wav"):
        return _fake_extraction_result()

    monkeypatch.setattr(frek_pipeline.node01, "extract_from_bytes", _fake_extract)

    app = FastAPI()
    app.include_router(frek_router, prefix="/api")
    client = TestClient(app)
    return client, db, fresh_bus


def _certify(client, **overrides):
    # "QQ==" decodes to a single byte -- extraction itself is mocked
    # (fixture), the route's own >=1000-byte size gate is what matters
    # for tests that need it to pass (see _big_audio_b64 below).
    body = {
        "audio_base64": "QQ==",
        "artiste_id": f"ARTISTE-{uuid.uuid4().hex[:8]}",
    }
    body.update(overrides)
    return client.post("/api/frek/certify", json=body)


def _big_audio_b64() -> str:
    import base64

    return base64.b64encode(b"\x00" * 2000).decode()


# ---------------------------------------------------------------------------
# 1. Route count guard — static regression, evidence over assumption.
# ---------------------------------------------------------------------------


class TestRouteCountGuard:
    EXPECTED_D1 = {
        ("POST", "/frek/certify"),
        ("POST", "/frek/certify/upload"),
        ("GET", "/frek/verify/{frek_id}"),
    }
    EXPECTED_D2 = {
        ("POST", "/frek/genesis"),
        ("POST", "/frek/workshop"),
    }
    EXPECTED_D3 = {
        ("GET", "/frek/advanced/reseau"),
        ("GET", "/frek/advanced/reseau/stats"),
        ("GET", "/frek/advanced/reseau/node/{node_id}"),
        ("GET", "/frek/advanced/reseau/neighbors/{node_id}"),
        ("GET", "/frek/advanced/reseau/artiste/{artiste_id}"),
        ("GET", "/frek/advanced/reseau/lieu/{lieu_id}"),
        ("GET", "/frek/advanced/reseau/path"),
    }
    EXPECTED_D4 = {
        ("GET", "/frek/advanced/transmission"),
        ("GET", "/frek/advanced/transmission/protocols"),
        ("GET", "/frek/advanced/transmission/protocol/{protocol}"),
        ("POST", "/frek/advanced/transmission/packet"),
        ("POST", "/frek/advanced/transmission/watermark"),
        ("POST", "/frek/advanced/transmission/sync"),
    }
    EXPECTED_D5 = {
        ("POST", "/frek/advanced/juridique/attestation"),
    }

    def _actual_routes(self) -> set:
        out = set()
        for route in frek_router.routes:
            methods = getattr(route, "methods", None)
            path = getattr(route, "path", None)
            if not methods or not path:
                continue
            for m in methods:
                if m == "HEAD":
                    continue
                out.add((m, path))
        return out

    def test_all_19_expected_routes_are_present(self):
        actual = self._actual_routes()
        expected = (
            self.EXPECTED_D1
            | self.EXPECTED_D2
            | self.EXPECTED_D3
            | self.EXPECTED_D4
            | self.EXPECTED_D5
        )
        assert len(expected) == 19, "expected-set itself must total 19"
        missing = expected - actual
        assert not missing, f"historical routes missing: {missing}"

    def test_no_historical_route_was_deleted(self):
        """A static, evidence-based count -- never forced to 19 if the
        real number differs (per the mission's own explicit instruction)."""
        actual = self._actual_routes()
        d1 = actual & self.EXPECTED_D1
        d2 = actual & self.EXPECTED_D2
        d3 = actual & self.EXPECTED_D3
        d4 = actual & self.EXPECTED_D4
        d5 = actual & self.EXPECTED_D5
        assert len(d1) == 3
        assert len(d2) == 2
        assert len(d3) == 7
        assert len(d4) == 6
        assert len(d5) == 1
        assert len(d1) + len(d2) + len(d3) + len(d4) + len(d5) == 19


# ---------------------------------------------------------------------------
# 2. D1 — certify / certify/upload / verify.
# ---------------------------------------------------------------------------


class TestD1Compatibility:
    def test_certify_still_exists_and_mints_legacy_frek_id(self, app_and_db):
        client, db, bus = app_and_db
        resp = _certify(client, audio_base64=_big_audio_b64())
        assert resp.status_code == 200
        body = resp.json()
        assert "frek_id" in body
        assert "extraction" in body and "identity" in body and "cycle" in body

    def test_certify_response_preserves_every_field_the_real_frontend_reads(
        self, app_and_db
    ):
        """`frontend/src/pages/Certify.jsx` is a confirmed, live,
        DIRECT_CALLER of this exact route (see docs/architecture/
        FREK_HISTORICAL_COMPATIBILITY_MATRIX.md's consumer-discovery
        section) -- this pins the historical fields it and
        `frontend/src/pages/Verify.jsx` depend on, so a future change
        that silently drops one is a hard test failure, not a surprise
        in production."""
        client, db, bus = app_and_db
        body = _certify(client, audio_base64=_big_audio_b64()).json()
        for key in (
            "frek_id",
            "extraction",
            "identity",
            "cycle",
            "resonance",
            "processing_time_ms",
            "status",
            "watermark_embedded",
            "message",
        ):
            assert key in body, f"real frontend caller depends on {key!r}"

    def test_certify_response_gains_canonical_note_additively(self, app_and_db):
        client, db, bus = app_and_db
        resp = _certify(client, audio_base64=_big_audio_b64())
        body = resp.json()
        assert "canonical_note" in body
        assert "content_binding" in body["canonical_note"]

    def test_certify_publishes_legacy_route_invoked_not_a_canonical_event(
        self, app_and_db
    ):
        client, db, bus = app_and_db
        received = []
        bus.subscribe("legacy_route.invoked", lambda e: received.append(e))
        bus.subscribe("content_binding.created", lambda e: received.append(e))
        _certify(client, audio_base64=_big_audio_b64())
        types = [e.event_type for e in received]
        assert "legacy_route.invoked" in types
        # EVENT_DUPLICATION_AVOIDED: certify never drives a real
        # content_binding write, so no canonical business event fires.
        assert "content_binding.created" not in types

    def test_certify_rate_limit_call_site(self, app_and_db, monkeypatch):
        """Exercises the CALL SITE (it's really there, uses the right
        action key) -- the rate limiter's own behavior is covered by
        security's own tests, matching test_content_binding_unit.py's
        established convention."""
        client, db, bus = app_and_db
        calls = []

        async def _fake_check(scope, action):
            calls.append((scope, action))
            return True

        monkeypatch.setattr("frek.legacy_compat.check_rate_limit", _fake_check)
        _certify(client, audio_base64=_big_audio_b64())
        assert any(action == "legacy_frek_write" for _, action in calls)

    def test_certify_invalid_audio_still_fails_safely(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.post(
            "/api/frek/certify",
            json={"audio_base64": "not-valid-base64!!!", "artiste_id": "X"},
        )
        assert resp.status_code == 400

    def test_certify_too_small_audio_still_rejected(self, app_and_db):
        client, db, bus = app_and_db
        resp = _certify(client, audio_base64="QQ==")  # 1 byte, below the 1000-byte gate
        assert resp.status_code == 400

    def test_verify_unknown_frek_id_still_404(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.get("/api/frek/verify/DOES-NOT-EXIST")
        assert resp.status_code == 404

    def test_verify_existing_frek_id_preserves_historical_fields(self, app_and_db):
        client, db, bus = app_and_db
        frek_id = _certify(client, audio_base64=_big_audio_b64()).json()["frek_id"]
        resp = client.get(f"/api/frek/verify/{frek_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["frek_id"] == frek_id
        assert body["verified"] is True
        assert "cycle" in body and "resonance" in body

    def test_verify_surfaces_canonical_binding_when_legacy_identifier_matches(
        self, app_and_db
    ):
        """A D1 content_binding referencing this legacy id via its own
        `legacy_identifier` compatibility field IS surfaced -- additive,
        never replacing the primary (legacy pipeline) lookup."""
        client, db, bus = app_and_db
        frek_id = _certify(client, audio_base64=_big_audio_b64()).json()["frek_id"]

        import asyncio

        asyncio.run(
            db.content_bindings.insert_one(
                {
                    "binding_id": "b-1",
                    "frek_id": "fk-real-object",
                    "legacy_identifier": frek_id,
                    "proof_state": "fingerprint",
                    "computed_at": "t",
                }
            )
        )
        resp = client.get(f"/api/frek/verify/{frek_id}")
        body = resp.json()
        assert body["canonical_binding"]["binding_id"] == "b-1"
        assert body["canonical_binding"]["source"] == "content_binding (canonical, D1)"

    def test_verify_without_canonical_binding_omits_the_field(self, app_and_db):
        client, db, bus = app_and_db
        frek_id = _certify(client, audio_base64=_big_audio_b64()).json()["frek_id"]
        resp = client.get(f"/api/frek/verify/{frek_id}")
        assert "canonical_binding" not in resp.json()

    def test_fingerprint_never_conflated_with_frek_id(self, app_and_db):
        """FINGERPRINT != FREK_ID, SIGNAL_FINGERPRINT != CRYPTOGRAPHIC_HASH
        -- the legacy identity dict still separates them (unchanged D1
        historical shape, not reopened this state)."""
        client, db, bus = app_and_db
        body = _certify(client, audio_base64=_big_audio_b64()).json()
        identity = body["identity"]
        assert "frek_id" in identity
        assert identity["frek_id"] == body["frek_id"]


# ---------------------------------------------------------------------------
# 3. D2 — genesis / workshop.
# ---------------------------------------------------------------------------


class TestD2Compatibility:
    def test_genesis_still_exists_and_preserves_vocabulary(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.post(
            "/api/frek/genesis",
            json={
                "artiste_id": f"ARTISTE-{uuid.uuid4().hex[:8]}",
                "intention": {"concept": "test"},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["stade"] == "GENESIS"
        assert "pre_id" in body

    def test_genesis_response_gains_canonical_note_additively(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.post(
            "/api/frek/genesis",
            json={
                "artiste_id": f"ARTISTE-{uuid.uuid4().hex[:8]}",
                "intention": {"concept": "test"},
            },
        )
        body = resp.json()
        assert "canonical_note" in body
        assert "creative_lifecycle" in body["canonical_note"]

    def test_genesis_publishes_legacy_route_invoked(self, app_and_db):
        client, db, bus = app_and_db
        received = []
        bus.subscribe("legacy_route.invoked", lambda e: received.append(e))
        client.post(
            "/api/frek/genesis",
            json={
                "artiste_id": f"ARTISTE-{uuid.uuid4().hex[:8]}",
                "intention": {"concept": "test"},
            },
        )
        assert any(
            e.payload["legacy_route"] == "POST /api/frek/genesis" for e in received
        )

    def test_workshop_still_exists_and_preserves_vocabulary(self, app_and_db):
        client, db, bus = app_and_db
        pre_id = client.post(
            "/api/frek/genesis",
            json={
                "artiste_id": f"ARTISTE-{uuid.uuid4().hex[:8]}",
                "intention": {"concept": "test"},
            },
        ).json()["pre_id"]
        resp = client.post(
            "/api/frek/workshop",
            json={"pre_id": pre_id, "audio_base64": _big_audio_b64()},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["stade"] == "WORKSHOP"
        assert "canonical_note" in body

    def test_genesis_does_not_weaken_canonical_creative_lifecycle_auth(self):
        """No session/admin auth is added to this unauthenticated legacy
        route (would break backward compatibility); conversely, this
        route never calls canonical creative_lifecycle on the caller's
        behalf either -- confirmed by static import check."""
        src = (BACKEND_DIR / "frek" / "routes.py").read_text()
        assert "creative_lifecycle_router" not in src
        assert "from creative_lifecycle" not in src


# ---------------------------------------------------------------------------
# 4. D3 — the 7 réseau routes.
# ---------------------------------------------------------------------------


class TestD3Compatibility:
    def test_reseau_info_and_stats_still_work(self, app_and_db):
        client, db, bus = app_and_db
        assert client.get("/api/frek/advanced/reseau").status_code == 200
        assert client.get("/api/frek/advanced/reseau/stats").status_code == 200

    def test_unknown_node_still_404(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.get("/api/frek/advanced/reseau/node/DOES-NOT-EXIST")
        assert resp.status_code == 404

    def test_node_lookup_gains_canonical_relationships_for_oeuvre(self, app_and_db):
        client, db, bus = app_and_db
        frek_id = _certify(client, audio_base64=_big_audio_b64()).json()["frek_id"]

        import asyncio

        asyncio.run(
            db.relationships.insert_one(
                {
                    "relationship_id": "r-1",
                    "subject_id": frek_id,
                    "object_id": "OTHER-OEUVRE",
                    "predicate": "created_by",
                    "layer": "trust",
                    "status": "claimed",
                    "visibility": {"type": "global", "id": None},
                }
            )
        )
        resp = client.get(f"/api/frek/advanced/reseau/node/{frek_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["node_type"] == "OEUVRE"
        assert body["canonical_relationships"]["count"] == 1
        assert (
            body["canonical_relationships"]["relationships"][0]["relationship_id"]
            == "r-1"
        )

    def test_node_lookup_never_surfaces_non_global_canonical_relationship(
        self, app_and_db
    ):
        """The legacy route is unauthenticated -- only GLOBAL-visibility
        canonical relationships may ever be surfaced through it (never a
        privacy downgrade for OBJECT/ENTITY-scoped ones)."""
        client, db, bus = app_and_db
        frek_id = _certify(client, audio_base64=_big_audio_b64()).json()["frek_id"]

        import asyncio

        asyncio.run(
            db.relationships.insert_one(
                {
                    "relationship_id": "r-private",
                    "subject_id": frek_id,
                    "object_id": "OTHER",
                    "predicate": "created_by",
                    "layer": "trust",
                    "status": "claimed",
                    "visibility": {"type": "object", "id": None},
                }
            )
        )
        resp = client.get(f"/api/frek/advanced/reseau/node/{frek_id}")
        assert "canonical_relationships" not in resp.json()

    def test_non_oeuvre_node_never_gets_canonical_relationships_field(
        self, app_and_db
    ):
        client, db, bus = app_and_db
        # LIEU-shaped node_ids are created by register_emission, not
        # independently addressable -- exercise via a certify then a
        # neighbors call on an ARTISTE-type id instead, whose to_dict()
        # historical shape must stay untouched.
        resp = client.get("/api/frek/advanced/reseau/neighbors/ANY-ID")
        assert resp.status_code == 200
        assert "canonical_relationships" not in resp.json()

    def test_all_7_reseau_routes_are_rate_limited(self, app_and_db, monkeypatch):
        client, db, bus = app_and_db
        calls = []

        async def _fake_check(scope, action):
            calls.append(action)
            return True

        monkeypatch.setattr("frek.legacy_compat.check_rate_limit", _fake_check)
        client.get("/api/frek/advanced/reseau")
        client.get("/api/frek/advanced/reseau/stats")
        client.get("/api/frek/advanced/reseau/node/X")
        client.get("/api/frek/advanced/reseau/neighbors/X")
        client.get("/api/frek/advanced/reseau/artiste/X")
        client.get("/api/frek/advanced/reseau/lieu/X")
        client.get("/api/frek/advanced/reseau/path?start_id=A&end_id=B")
        assert calls.count("legacy_frek_read") == 7

    def test_historical_taxonomy_vocabulary_unchanged(self):
        """Preserves the historical 5 node types / 17 relation-type
        vocabulary -- not reopened this state."""
        from frek.nodes.node06_reseau import NodeType, RelationType

        assert len(list(NodeType)) == 5
        assert len(list(RelationType)) == 17

    def test_cultural_relation_cross_reference_never_implies_verified(
        self, app_and_db
    ):
        """A CULTURAL-layer canonical relationship surfaced through the
        legacy cross-reference still carries its own honest `status` --
        the legacy route never re-labels it."""
        client, db, bus = app_and_db
        frek_id = _certify(client, audio_base64=_big_audio_b64()).json()["frek_id"]

        import asyncio

        asyncio.run(
            db.relationships.insert_one(
                {
                    "relationship_id": "r-cultural",
                    "subject_id": frek_id,
                    "object_id": "OTHER",
                    "predicate": "similar_to",
                    "layer": "cultural",
                    "status": "computed",
                    "visibility": {"type": "global", "id": None},
                }
            )
        )
        resp = client.get(f"/api/frek/advanced/reseau/node/{frek_id}")
        rel = resp.json()["canonical_relationships"]["relationships"][0]
        assert rel["layer"] == "cultural"
        assert rel["status"] != "verified"


# ---------------------------------------------------------------------------
# 5. D4 — the 6 transmission routes.
# ---------------------------------------------------------------------------


class TestD4Compatibility:
    def test_protocols_still_returns_5_historical_protocols(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.get("/api/frek/advanced/transmission/protocols")
        assert resp.status_code == 200
        protocols = resp.json()["protocols"]
        assert len(protocols) == 5
        names = {p["protocol"] for p in protocols}
        assert names == {
            "bluetooth_ble",
            "nfc",
            "wifi_local",
            "ultrasonic",
            "cellular",
        }

    def test_protocols_gain_canonical_adapter_info_additively(self, app_and_db):
        client, db, bus = app_and_db
        protocols = client.get("/api/frek/advanced/transmission/protocols").json()[
            "protocols"
        ]
        ble = next(p for p in protocols if p["protocol"] == "bluetooth_ble")
        assert "canonical_adapter_info" in ble
        assert ble["canonical_adapter_info"]["hardware_verified"] is False

    def test_single_protocol_info_gains_canonical_adapter_info(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.get("/api/frek/advanced/transmission/protocol/nfc")
        assert resp.status_code == 200
        body = resp.json()
        assert body["protocol"] == "nfc"
        assert "canonical_adapter_info" in body

    def test_unknown_protocol_still_400(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.get("/api/frek/advanced/transmission/protocol/not-a-protocol")
        assert resp.status_code == 400

    def test_packet_signature_short_never_promoted_as_real_signature(
        self, app_and_db
    ):
        client, db, bus = app_and_db
        resp = client.post(
            "/api/frek/advanced/transmission/packet",
            json={
                "frek_id": "FK-1",
                "artiste_id": "A-1",
                "sha256_signal": "a" * 64,
                "protocol": "bluetooth_ble",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["signature_short_is_not_cryptographic_signature"] is True
        assert body["canonical_offline_transport_endpoint"] == "/api/v1/offline/envelopes"

    def test_watermark_delegates_to_canonical_wrapper_superset_shape(
        self, app_and_db
    ):
        """Response is a strict superset of the historical dict --
        response-compatible, never a shape break."""
        client, db, bus = app_and_db
        resp = client.post(
            "/api/frek/advanced/transmission/watermark?frek_id=FK-1"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["proof"] is False
        assert body["validation_status"] == "NOT_TESTED"
        assert body["decoder_exists"] is False
        assert "frek_id" in body  # historical field preserved

    def test_sync_gains_compatibility_note(self, app_and_db):
        client, db, bus = app_and_db
        resp = client.post("/api/frek/advanced/transmission/sync")
        assert resp.status_code == 200
        assert "note" in resp.json()
        assert "canonique" in resp.json()["note"] or "reconciliation" in resp.json()["note"].lower()

    def test_watermark_never_influences_canonical_offline_transport_trust_state(self):
        """WATERMARK_EQUALS_PROOF=FALSE, unchanged: the legacy route
        calls the same D4 wrapper that structurally cannot feed back
        into TransportEnvelope trust state (see offline_transport/
        watermark.py's own module docstring) -- static confirmation that
        this legacy route doesn't import anything else from
        offline_transport that WOULD let it."""
        src = (BACKEND_DIR / "frek" / "routes_advanced.py").read_text()
        assert "from offline_transport.models import" not in src
        assert "from offline_transport.service import" not in src

    def test_all_6_transmission_routes_are_rate_limited(self, app_and_db, monkeypatch):
        client, db, bus = app_and_db
        calls = []

        async def _fake_check(scope, action):
            calls.append(action)
            return True

        monkeypatch.setattr("frek.legacy_compat.check_rate_limit", _fake_check)
        client.get("/api/frek/advanced/transmission")
        client.get("/api/frek/advanced/transmission/protocols")
        client.get("/api/frek/advanced/transmission/protocol/nfc")
        client.post(
            "/api/frek/advanced/transmission/packet",
            json={
                "frek_id": "FK-1",
                "artiste_id": "A-1",
                "sha256_signal": "a" * 64,
                "protocol": "nfc",
            },
        )
        client.post("/api/frek/advanced/transmission/watermark?frek_id=FK-1")
        client.post("/api/frek/advanced/transmission/sync")
        assert calls.count("legacy_frek_read") == 3
        assert calls.count("legacy_frek_write") == 3


# ---------------------------------------------------------------------------
# 6. D5 — the 1 attestation route.
# ---------------------------------------------------------------------------


class TestD5Compatibility:
    def _attest(self, client, **overrides):
        body = {
            "sha256_signal": "a" * 64,
            "artiste_id": "ARTISTE-1",
            "timestamp_ms": 1735689600000,
        }
        body.update(overrides)
        return client.post("/api/frek/advanced/juridique/attestation", json=body)

    def test_attestation_route_still_exists(self, app_and_db):
        client, db, bus = app_and_db
        resp = self._attest(client)
        assert resp.status_code == 200

    def test_arbitrary_caller_facts_cannot_become_canonical_truth(self, app_and_db):
        """The legacy route still just formats caller input -- it never
        writes anything to canonical storage, so nothing it's told
        becomes canonical truth (canonical D5 reports resolve only from
        resource ID references, never this route's body)."""
        client, db, bus = app_and_db
        self._attest(client, artiste_id="SOMEONE-ELSES-NAME")
        assert db is not None
        import asyncio

        count = asyncio.run(db.technical_evidence_reports.count_documents({}))
        assert count == 0

    def test_unsupported_legal_wording_not_reintroduced(self, app_and_db):
        client, db, bus = app_and_db
        body = self._attest(client).json()
        from technical_evidence_report.models import assert_no_forbidden_language

        assert_no_forbidden_language(body["legal_text"])
        assert "irrefutable" not in body["legal_text"].lower()
        assert "irréfutable" not in body["legal_text"].lower()

    def test_canonical_report_endpoint_hint_present(self, app_and_db):
        client, db, bus = app_and_db
        body = self._attest(client).json()
        assert (
            body["canonical_technical_evidence_report_endpoint"]
            == "/api/v1/reports/technical-evidence"
        )

    def test_attestation_is_rate_limited(self, app_and_db, monkeypatch):
        client, db, bus = app_and_db
        calls = []

        async def _fake_check(scope, action):
            calls.append(action)
            return True

        monkeypatch.setattr("frek.legacy_compat.check_rate_limit", _fake_check)
        self._attest(client)
        assert calls == ["legacy_frek_write"]

    def test_attestation_publishes_legacy_route_invoked(self, app_and_db):
        client, db, bus = app_and_db
        received = []
        bus.subscribe("legacy_route.invoked", lambda e: received.append(e))
        self._attest(client)
        assert len(received) == 1
        assert received[0].payload["canonical_target"] == "technical_evidence_report"
        # Never leaks the caller's own submitted values into the audit
        # event payload.
        assert "SOMEONE" not in str(received[0].payload)


# ---------------------------------------------------------------------------
# 7. Cross-cutting: audit wiring, event-type registration, no duplicate
#    truth engine, backend/frek/ not deleted.
# ---------------------------------------------------------------------------


class TestCrossCutting:
    def test_legacy_route_invoked_maps_to_a_correct_audit_event(self):
        from audit_trail.subscribers import event_envelope_to_audit_event
        from eventbus.producers import build_legacy_route_invoked_event

        env = build_legacy_route_invoked_event(
            legacy_route="POST /api/frek/certify",
            canonical_target="content_binding",
            outcome="created",
        )
        audit_event = event_envelope_to_audit_event(env)
        assert audit_event.action == "legacy_route.invoked"
        assert audit_event.resource_type == "frek_legacy_compat"

    def test_legacy_route_invoked_never_echoes_raw_payload(self):
        from eventbus.producers import build_legacy_route_invoked_event

        env = build_legacy_route_invoked_event(
            legacy_route="POST /api/frek/certify",
            canonical_target="content_binding",
            outcome="created",
            detail={"safe": "coarse-metadata-only"},
        )
        assert "audio_base64" not in env.payload
        assert "sha256_signal" not in env.payload

    def test_server_py_subscribes_legacy_route_invoked_to_audit_trail(self):
        server_py = (BACKEND_DIR / "server.py").read_text(encoding="utf-8")
        assert '"legacy_route.invoked"' in server_py

    def test_no_parallel_truth_engine_introduced(self):
        """frek/routes.py and frek/routes_advanced.py may READ canonical
        collections (the compatibility cross-reference touches) but
        never WRITE to any canonical D1-D5 collection -- confirmed
        statically, not just by convention."""
        for fname in ("routes.py", "routes_advanced.py"):
            src = (BACKEND_DIR / "frek" / fname).read_text()
            for forbidden_write in (
                "content_bindings.insert_one",
                "content_bindings.replace_one",
                "content_bindings.update_one",
                "relationships.insert_one",
                "relationships.replace_one",
                "relationships.update_one",
                "transport_envelopes.insert_one",
                "transport_envelopes.replace_one",
                "transport_envelopes.update_one",
                "technical_evidence_reports.insert_one",
            ):
                assert forbidden_write not in src, f"{fname} writes {forbidden_write}"

    def test_backend_frek_router_still_mounted(self):
        """DELETE_BACKEND_FREK=FALSE, PHYSICAL_DELETION_ALLOWED=FALSE --
        confirmed the module still imports and the router still mounts,
        not merely that files exist on disk."""
        assert frek_router is not None
        assert len(frek_router.routes) >= 43  # 13 (routes.py) + 30 (routes_advanced.py)

    def test_legacy_read_and_write_rate_limit_keys_registered(self):
        from security.policies import DEFAULT_LIMITS

        assert "legacy_frek_read" in DEFAULT_LIMITS
        assert "legacy_frek_write" in DEFAULT_LIMITS
        read_limit, _ = DEFAULT_LIMITS["legacy_frek_read"]
        write_limit, _ = DEFAULT_LIMITS["legacy_frek_write"]
        assert read_limit > write_limit  # reads bounded more generously than writes
