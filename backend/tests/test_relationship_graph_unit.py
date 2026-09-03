"""D3 -- Relationship / Provenance Graph (founder decision D3, 2026-09-02)
-- unit tests.

Same isolated-app technique as `test_content_binding_unit.py` and
`test_creative_lifecycle_unit.py`: FastAPI + TestClient + mongomock_motor,
no live server/Mongo/notary needed.
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

os.environ.setdefault(
    "SECRET_KEY", "dev-only-not-a-real-secret-relationship-graph-test"
)
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import mongomock_motor  # noqa: E402

import relationship_graph.routes as rg_routes  # noqa: E402
from relationship_graph.routes import relationship_graph_router  # noqa: E402
from relationship_graph.models import (  # noqa: E402
    HISTORICAL_NODE_TYPE_TAXONOMY,
    HISTORICAL_RELATION_TAXONOMY,
    RelationLayer,
    Relationship,
)
from relationship_graph.service import (  # noqa: E402
    MAX_PATH_DEPTH_HARD_CAP,
    UnknownPredicateError,
    resolve_layer,
)
from identity_engine import service as identity_service  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_relationship_graph_test"]
    rg_routes.set_db(db)

    fresh_bus = InProcessEventBus()
    monkeypatch.setattr("eventbus.bus.default_bus", fresh_bus)

    async def _fake_notarize_fail(*args, **kwargs):
        raise RuntimeError("no notary wired in this isolated test app")

    monkeypatch.setattr(
        "notary.service.notarize_event", _fake_notarize_fail, raising=False
    )

    app = FastAPI()
    app.include_router(relationship_graph_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db, fresh_bus


def _holder_headers(frek_id: str) -> dict:
    token = identity_service.issue_session_token(frek_id)
    return {"X-FREK-Session": token}


def _admin_headers() -> dict:
    return {"X-Admin-Key": ADMIN_KEY}


async def _seed_fk_object(db, frek_id: str):
    await db.fk_objects.insert_one({"frek_id": frek_id, "object_type": "song"})


async def _seed_identity(db, frek_id: str):
    await db.frek_persons.insert_one({"frek_id": frek_id, "linked_objects": []})


async def _seed_lifecycle_event(db, event_id: str, pre_id: str):
    await db.creative_lifecycle_events.insert_one(
        {"event_id": event_id, "pre_id": pre_id, "stage": "METAMORPHOSE", "sequence": 3}
    )


async def _seed_content_binding(db, binding_id: str):
    await db.content_bindings.insert_one({"binding_id": binding_id, "frek_id": "FK-1"})


def _create(
    client,
    headers,
    *,
    subject_id="A",
    subject_type=None,
    predicate="created_by",
    object_id="B",
    object_type=None,
    origin="declared",
    statement="a asserts a relation",
    visibility=None,
    source_event_id=None,
    source_content_binding_id=None,
):
    body = {
        "subject_id": subject_id,
        "subject_type": subject_type,
        "predicate": predicate,
        "object_id": object_id,
        "object_type": object_type,
        "origin": origin,
        "statement": statement,
        "data": {},
    }
    if visibility is not None:
        body["visibility"] = visibility
    if source_event_id is not None:
        body["source_event_id"] = source_event_id
    if source_content_binding_id is not None:
        body["source_content_binding_id"] = source_content_binding_id
    return client.post("/api/v1/relationships", json=body, headers=headers)


class TestTrustVsCulturalSplit:
    """#1: trust graph != cultural/inferred graph."""

    def test_layer_resolution_is_closed_and_derived(self):
        assert resolve_layer("created_by") == RelationLayer.TRUST
        assert resolve_layer("similar_to") == RelationLayer.CULTURAL
        with pytest.raises(UnknownPredicateError):
            resolve_layer("not_a_real_predicate")

    def test_create_trust_and_cultural_relations_have_distinct_layers(self, app_and_db):
        client, _db, _bus = app_and_db
        trust = _create(
            client,
            _admin_headers(),
            predicate="created_by",
            subject_id="OBJ-1",
            object_id="ART-1",
        )
        cultural = _create(
            client,
            _admin_headers(),
            predicate="similar_to",
            subject_id="OBJ-1",
            object_id="OBJ-2",
            origin="computed",
        )
        assert trust.json()["layer"] == "trust"
        assert cultural.json()["layer"] == "cultural"


class TestCulturalNeverVerified:
    """#2, #3: an inferred/computed relation is never automatically
    verified -- SIMILARITY_EQUALS_FACT / INFLUENCE_EQUALS_FACT /
    RESONANCE_EQUALS_FACT = FALSE, structurally, not just documented."""

    def test_inferred_relation_status_is_inferred_not_verified(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            predicate="influenced_by",
            origin="inferred",
            statement="AI inference",
        )
        assert r.json()["status"] == "inferred"

    def test_computed_similarity_is_not_verified_fact(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            predicate="similar_to",
            origin="computed",
            statement="cosine similarity 0.91",
        )
        assert r.json()["status"] == "computed"
        assert r.json()["layer"] == "cultural"

    def test_cultural_relation_can_never_be_marked_verified(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), predicate="similar_to", origin="computed")
        rel_id = r.json()["relationship_id"]
        v = client.post(
            f"/api/v1/relationships/{rel_id}/verify", json={}, headers=_admin_headers()
        )
        assert v.status_code == 409

    def test_trust_relation_can_be_verified(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), predicate="created_by")
        rel_id = r.json()["relationship_id"]
        v = client.post(
            f"/api/v1/relationships/{rel_id}/verify", json={}, headers=_admin_headers()
        )
        assert v.status_code == 200
        assert v.json()["status"] == "verified"


class TestCanonicalEntityReferences:
    """#4: relationship references canonical entities."""

    def test_recognized_type_must_exist(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            subject_type="fk_object",
            subject_id="FK-DOES-NOT-EXIST",
        )
        assert r.status_code == 404

    def test_recognized_type_existing_succeeds(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_fk_object(db, "FK-1"))
        r = _create(
            client, _admin_headers(), subject_type="fk_object", subject_id="FK-1"
        )
        assert r.status_code == 200

    def test_unrecognized_type_is_accepted_unchecked(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            subject_type="external_dataset",
            subject_id="XYZ-1",
        )
        assert r.status_code == 200


class TestActorSourcePreserved:
    """#5: actor/source is preserved."""

    def test_holder_actor_recorded_on_assertion(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _holder_headers("ARTIST-1"), origin="declared")
        assert r.status_code == 200
        history = client.get(
            f"/api/v1/relationships/{r.json()['relationship_id']}/history",
            headers=_holder_headers("ARTIST-1"),
        ).json()
        assert history["assertions"][0]["actor_id"] == "ARTIST-1"
        assert history["assertions"][0]["authority"] == "holder"


class TestAuthorityEnforced:
    """#6, #7: authority enforced, unauthorized rejected."""

    def test_no_credentials_is_403(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, {})
        assert r.status_code == 403

    def test_holder_cannot_self_assert_computed_origin(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _holder_headers("ARTIST-1"), origin="computed")
        assert r.status_code == 403

    def test_admin_can_assert_computed_origin(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), origin="computed")
        assert r.status_code == 200

    def test_holder_can_self_assert_declared_origin(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _holder_headers("ARTIST-1"), origin="declared")
        assert r.status_code == 200


class TestVisibility:
    """#8, #9: visibility policy enforced, private relationship not
    leaked (404, not 403 -- existence itself is not disclosed)."""

    def test_global_visibility_is_public(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), visibility={"type": "global"})
        rel_id = r.json()["relationship_id"]
        got = client.get(f"/api/v1/relationships/{rel_id}")
        assert got.status_code == 200

    def test_object_scoped_visibility_hides_from_non_party(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _holder_headers("ARTIST-1"),
            subject_id="ARTIST-1",
            visibility={"type": "object"},
        )
        rel_id = r.json()["relationship_id"]
        blocked = client.get(
            f"/api/v1/relationships/{rel_id}", headers=_holder_headers("SOMEONE-ELSE")
        )
        assert blocked.status_code == 404

    def test_object_scoped_visibility_visible_to_party(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _holder_headers("ARTIST-1"),
            subject_id="ARTIST-1",
            visibility={"type": "object"},
        )
        rel_id = r.json()["relationship_id"]
        ok = client.get(
            f"/api/v1/relationships/{rel_id}", headers=_holder_headers("ARTIST-1")
        )
        assert ok.status_code == 200

    def test_object_scoped_visibility_visible_to_admin(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _holder_headers("ARTIST-1"),
            subject_id="ARTIST-1",
            visibility={"type": "object"},
        )
        rel_id = r.json()["relationship_id"]
        ok = client.get(f"/api/v1/relationships/{rel_id}", headers=_admin_headers())
        assert ok.status_code == 200

    def test_private_relationship_not_leaked_via_neighbors(self, app_and_db):
        client, _db, _bus = app_and_db
        _create(
            client,
            _holder_headers("ARTIST-1"),
            subject_id="ARTIST-1",
            object_id="OBJ-1",
            visibility={"type": "object"},
        )
        neighbors = client.get("/api/v1/relationships/entity/ARTIST-1/neighbors").json()
        assert neighbors["neighbors_count"] == 0


class TestProvenanceRetained:
    """#10: provenance retained."""

    def test_history_carries_claim_evidence_actor_authority_timestamp(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            predicate="similar_to",
            origin="computed",
            statement="cosine 0.9",
        )
        rel_id = r.json()["relationship_id"]
        history = client.get(
            f"/api/v1/relationships/{rel_id}/history", headers=_admin_headers()
        ).json()
        a = history["assertions"][0]
        assert a["claim"]["statement"] == "cosine 0.9"
        assert a["claim"]["origin"] == "computed"
        assert a["evidence"][0]["kind"] == "computation"
        assert a["authority"] == "admin"
        assert a["created_at"]


class TestD6Reuse:
    """#11: D6 semantics reused -- structural proof, not just a claim."""

    def test_relationship_round_trips_through_real_claim_evidence_types(
        self, app_and_db
    ):
        client, _db, _bus = app_and_db
        r = _create(client, _admin_headers(), predicate="similar_to", origin="computed")
        body = r.json()
        relationship = Relationship.model_validate(body)
        assert relationship.assertions[0].claim.origin.value == "computed"
        assert relationship.assertions[0].evidence[0].kind.value == "computation"


class TestD2Reuse:
    """#12: D2 lifecycle relation can be referenced (D3_CONSUMES_D2=TRUE,
    D3_REIMPLEMENTS_D2=FALSE)."""

    def test_derived_from_can_reference_a_real_lifecycle_event(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_lifecycle_event(db, "EVT-1", "PRE-1"))
        r = _create(
            client,
            _admin_headers(),
            predicate="derived_from",
            subject_type="creative_lifecycle",
            subject_id="PRE-1",
            source_event_id="EVT-1",
        )
        assert r.status_code == 200
        assert r.json()["source_event_id"] == "EVT-1"

    def test_unknown_source_event_id_is_404(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            predicate="derived_from",
            source_event_id="EVT-DOES-NOT-EXIST",
        )
        assert r.status_code == 404

    def test_derived_from_can_reference_a_real_content_binding(self, app_and_db):
        client, db, _bus = app_and_db
        asyncio.run(_seed_content_binding(db, "CB-1"))
        r = _create(
            client,
            _admin_headers(),
            predicate="derived_from",
            source_content_binding_id="CB-1",
        )
        assert r.status_code == 200
        assert r.json()["source_content_binding_id"] == "CB-1"


class TestD1Reuse:
    """#13: D1 computed relationship remains inference/computation, never
    an automatically-verified fact."""

    def test_similar_to_stays_computed_never_verified(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(
            client,
            _admin_headers(),
            predicate="similar_to",
            origin="computed",
            statement="frek_signal_v1 cosine=0.91",
        )
        body = r.json()
        assert body["status"] == "computed"
        assert body["layer"] == "cultural"
        rel_id = body["relationship_id"]
        v = client.post(
            f"/api/v1/relationships/{rel_id}/verify", json={}, headers=_admin_headers()
        )
        assert v.status_code == 409


class TestIdempotencyAndProvenance:
    """#14: duplicate retry idempotent. #15: independent assertions
    preserve distinct provenance."""

    def test_same_actor_retry_is_deduplicated(self, app_and_db):
        client, _db, _bus = app_and_db
        r1 = _create(client, _admin_headers())
        r2 = _create(client, _admin_headers())
        assert r1.json()["deduplicated"] is False
        assert r2.json()["deduplicated"] is True
        assert len(r2.json()["assertions"]) == 1

    def test_different_actors_preserve_distinct_assertions(self, app_and_db):
        client, _db, _bus = app_and_db
        r1 = _create(client, _holder_headers("ARTIST-1"), subject_id="ARTIST-1")
        r2 = _create(client, _holder_headers("ARTIST-2"), subject_id="ARTIST-1")
        assert r1.json()["relationship_id"] == r2.json()["relationship_id"]
        assert r2.json()["deduplicated"] is False
        actor_ids = {a["actor_id"] for a in r2.json()["assertions"]}
        assert actor_ids == {"ARTIST-1", "ARTIST-2"}


class TestRevocationPreservesHistory:
    """#16: relationship correction/revocation preserves history."""

    def test_revoked_assertion_stays_in_history(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _holder_headers("ARTIST-1"), subject_id="ARTIST-1")
        rel_id = r.json()["relationship_id"]
        assertion_id = r.json()["assertions"][0]["assertion_id"]

        revoked = client.post(
            f"/api/v1/relationships/{rel_id}/revoke",
            json={"assertion_id": assertion_id, "reason": "mistake"},
            headers=_holder_headers("ARTIST-1"),
        )
        assert revoked.status_code == 200
        assert revoked.json()["status"] == "revoked"

        history = client.get(
            f"/api/v1/relationships/{rel_id}/history", headers=_admin_headers()
        ).json()
        assert len(history["assertions"]) == 1
        assert history["assertions"][0]["revoked_at"] is not None
        assert history["assertions"][0]["revoked_reason"] == "mistake"

    def test_revoke_requires_owner_or_admin(self, app_and_db):
        client, _db, _bus = app_and_db
        r = _create(client, _holder_headers("ARTIST-1"), subject_id="ARTIST-1")
        rel_id = r.json()["relationship_id"]
        assertion_id = r.json()["assertions"][0]["assertion_id"]
        blocked = client.post(
            f"/api/v1/relationships/{rel_id}/revoke",
            json={"assertion_id": assertion_id},
            headers=_holder_headers("SOMEONE-ELSE"),
        )
        assert blocked.status_code == 403


class TestNeighborsAndDirection:
    """#17, #18: neighbor query works, incoming/outgoing query works."""

    def test_neighbors_both_directions(self, app_and_db):
        client, db, _bus = app_and_db
        _create(
            client,
            _admin_headers(),
            subject_id="A",
            predicate="created_by",
            object_id="B",
        )
        _create(
            client,
            _admin_headers(),
            subject_id="C",
            predicate="created_by",
            object_id="A",
        )
        neighbors = client.get("/api/v1/relationships/entity/A/neighbors").json()
        assert neighbors["neighbors_count"] == 2

    def test_outgoing_only(self, app_and_db):
        client, _db, _bus = app_and_db
        _create(
            client,
            _admin_headers(),
            subject_id="A",
            predicate="created_by",
            object_id="B",
        )
        _create(
            client,
            _admin_headers(),
            subject_id="C",
            predicate="created_by",
            object_id="A",
        )
        out = client.get("/api/v1/relationships/entity/A/outgoing").json()
        assert out["count"] == 1
        assert out["relationships"][0]["object_id"] == "B"

    def test_incoming_only(self, app_and_db):
        client, _db, _bus = app_and_db
        _create(
            client,
            _admin_headers(),
            subject_id="A",
            predicate="created_by",
            object_id="B",
        )
        _create(
            client,
            _admin_headers(),
            subject_id="C",
            predicate="created_by",
            object_id="A",
        )
        inc = client.get("/api/v1/relationships/entity/A/incoming").json()
        assert inc["count"] == 1
        assert inc["relationships"][0]["subject_id"] == "C"


class TestBoundedTraversal:
    """#19: bounded path traversal works. #20: unbounded traversal
    rejected. #21: cycles do not break traversal. #22: query limits
    enforced."""

    def test_path_found_within_bound(self, app_and_db):
        client, _db, _bus = app_and_db
        _create(
            client,
            _admin_headers(),
            subject_id="A",
            predicate="created_by",
            object_id="B",
        )
        _create(
            client,
            _admin_headers(),
            subject_id="B",
            predicate="created_by",
            object_id="C",
        )
        path = client.get(
            "/api/v1/relationships/traverse/path?start_id=A&end_id=C&max_depth=6"
        ).json()
        assert path["path_found"] is True
        assert path["path"][-1]["node_id"] == "C"

    def test_max_depth_beyond_hard_cap_rejected(self, app_and_db):
        client, _db, _bus = app_and_db
        bad_depth = MAX_PATH_DEPTH_HARD_CAP + 1
        r = client.get(
            f"/api/v1/relationships/traverse/path?start_id=A&end_id=B&max_depth={bad_depth}"
        )
        assert r.status_code == 422

    def test_cycle_does_not_break_traversal(self, app_and_db):
        client, _db, _bus = app_and_db
        _create(
            client,
            _admin_headers(),
            subject_id="A",
            predicate="created_by",
            object_id="B",
        )
        _create(
            client,
            _admin_headers(),
            subject_id="B",
            predicate="created_by",
            object_id="C",
        )
        _create(
            client,
            _admin_headers(),
            subject_id="C",
            predicate="created_by",
            object_id="A",
        )
        path = client.get(
            "/api/v1/relationships/traverse/path?start_id=A&end_id=C&max_depth=6"
        )
        assert path.status_code == 200
        assert path.json()["path_found"] is True

    def test_neighbors_limit_enforced(self, app_and_db):
        client, _db, _bus = app_and_db
        _create(
            client,
            _admin_headers(),
            subject_id="A",
            predicate="created_by",
            object_id="B",
        )
        _create(
            client,
            _admin_headers(),
            subject_id="A",
            predicate="similar_to",
            object_id="C",
            origin="computed",
        )
        limited = client.get("/api/v1/relationships/entity/A/neighbors?limit=1").json()
        assert limited["neighbors_count"] == 1

    def test_neighbors_limit_beyond_max_rejected(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.get("/api/v1/relationships/entity/A/neighbors?limit=100000")
        assert r.status_code == 422


class TestHistoricalTaxonomy:
    """#23: historical taxonomy preserved/mapped."""

    def test_5_node_types_and_17_relation_types_recorded(self):
        assert set(HISTORICAL_NODE_TYPE_TAXONOMY.keys()) == {
            "OEUVRE",
            "ARTISTE",
            "LIEU",
            "EPOQUE",
            "FREQUENCE",
        }
        assert len(HISTORICAL_RELATION_TAXONOMY) == 17

    def test_historical_taxonomy_endpoint_exposes_full_record(self, app_and_db):
        client, _db, _bus = app_and_db
        r = client.get("/api/v1/relationships/historical-taxonomy")
        assert r.status_code == 200
        body = r.json()
        assert len(body["node_types"]) == 5
        assert len(body["relation_types"]) == 17
        assert body["relation_types"]["cree_par"]["canonical_predicate"] == "created_by"
        assert body["relation_types"]["cree_par"]["emitted"] is True
        assert body["relation_types"]["collabore_avec"]["emitted"] is False


class TestHistoricalRoutesUnchanged:
    """#24: historical 7 routes remain untouched."""

    def test_relationship_graph_does_not_import_backend_frek(self):
        import relationship_graph.routes as mod

        src = open(mod.__file__).read()
        assert "backend.frek" not in src
        assert "from frek.routes" not in src
        assert "node06_reseau" not in src

    def test_historical_reseau_route_count_is_still_seven(self):
        advanced_py = (BACKEND_DIR / "frek" / "routes_advanced.py").read_text(
            encoding="utf-8"
        )
        count = advanced_py.count('@advanced_router.get("/reseau')
        assert count == 7
