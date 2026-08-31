"""Registry instance store (POST/GET /objects/{namespace}) — unit-tier
coverage, isolated FastAPI app + TestClient + mongomock_motor.

tests/test_registry_objects.py already covers this behaviorally against a
live server (integration-marked, needs real infra to run). This file
exists for a narrower, mechanical reason: registry/routes.py is in CI's
coverage-gated MODULES set (.github/workflows/ci.yml's --cov-fail-under=90
step runs unit-tier only, per pytest.ini's default -m "not integration"),
and the /objects endpoints had zero unit-tier coverage — every line of
create_registry_object/list_registry_objects/get_registry_object/
_authorize_write/_require_db ran only under the integration marker, so the
coverage job never saw them execute at all. No live server or real
network needed here, same technique as tests/test_fk_object_created_event.py.
"""

import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-unit-test")

import mongomock_motor  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import frek_v1.auth as frek_v1_auth  # noqa: E402
import registry.routes as registry_routes  # noqa: E402
from frek_v1.utils import create_access_token, hash_secret  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402

pytestmark = pytest.mark.unit

ISSUER_CLIENT_ID = "unit-test-issuer"


@pytest.fixture()
def db():
    return mongomock_motor.AsyncMongoMockClient()["frekcore_test_registry_objects_unit"]


@pytest.fixture()
def client(db):
    registry_routes.set_db(db)
    frek_v1_auth.set_db(db)
    app = FastAPI()
    app.include_router(registry_routes.registry_router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture()
def issuer_token(db):
    async def _seed():
        await db.frek_clients.insert_one(
            {
                "client_id": ISSUER_CLIENT_ID,
                "secret_hash": hash_secret("unused"),
                "permissions": ["registry:write"],
                "active": True,
            }
        )

    import asyncio

    asyncio.run(_seed())
    return create_access_token(ISSUER_CLIENT_ID)


def H_issuer(token):
    return {"Authorization": f"Bearer {token}"}


def H_holder(token):
    return {"X-FREK-Session": token}


class TestUnknownNamespace:
    def test_create_unknown_namespace_is_404(self, client, issuer_token):
        r = client.post(
            "/api/v1/registry/objects/frek.not-a-namespace",
            json={"payload": {}},
            headers=H_issuer(issuer_token),
        )
        assert r.status_code == 404

    def test_list_unknown_namespace_is_404(self, client):
        r = client.get("/api/v1/registry/objects/frek.not-a-namespace")
        assert r.status_code == 404

    def test_get_unknown_namespace_is_404(self, client):
        r = client.get("/api/v1/registry/objects/frek.not-a-namespace/frek-x")
        assert r.status_code == 404


class TestCreateAuthority:
    def test_create_without_any_credential_is_403(self, client):
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "No Auth"}},
        )
        assert r.status_code == 403

    def test_create_with_bad_bearer_token_is_403(self, client):
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "Bad Token"}},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert r.status_code == 403

    def test_create_with_invalid_session_token_is_403(self, client):
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "Bad Session"}},
            headers=H_holder("not-a-real-session-token"),
        )
        assert r.status_code == 403


class TestCreateAsIssuer:
    def test_create_valid_object_returns_full_envelope(self, client, issuer_token):
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "Test Artist Issuer"}},
            headers=H_issuer(issuer_token),
        )
        assert r.status_code == 201, r.text
        obj = r.json()
        assert obj["frek_id"].startswith("frek-")
        assert obj["entity_type"] == "frek.artist"
        assert obj["status"] == "draft"
        assert obj["version"] == 1
        assert obj["owner_id"] is None
        assert obj["created_by"] == {"authority": "issuer", "actor": ISSUER_CLIENT_ID}

    def test_entity_type_override_in_payload_is_ignored(self, client, issuer_token):
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "X", "entity_type": "frek.track"}},
            headers=H_issuer(issuer_token),
        )
        assert r.status_code == 201, r.text
        assert r.json()["entity_type"] == "frek.artist"

    def test_invalid_payload_missing_required_field_is_422(self, client, issuer_token):
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"legal_name": "no display_name"}},
            headers=H_issuer(issuer_token),
        )
        assert r.status_code == 422
        assert "display_name" in str(r.json())

    def test_issuer_can_set_arbitrary_owner_id(self, client, issuer_token):
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={
                "payload": {
                    "display_name": "Owned Artist",
                    "owner_id": "id-abc123def456-0001",
                }
            },
            headers=H_issuer(issuer_token),
        )
        assert r.status_code == 201, r.text
        assert r.json()["owner_id"] == "id-abc123def456-0001"

    def test_duplicate_explicit_frek_id_in_same_namespace_is_409(
        self, client, issuer_token
    ):
        body = {"payload": {"display_name": "Dup", "frek_id": "frek-abcdef012345-0001"}}
        r1 = client.post(
            "/api/v1/registry/objects/frek.artist",
            json=body,
            headers=H_issuer(issuer_token),
        )
        assert r1.status_code == 201, r1.text
        r2 = client.post(
            "/api/v1/registry/objects/frek.artist",
            json=body,
            headers=H_issuer(issuer_token),
        )
        assert r2.status_code == 409


class TestCreateAsOwner:
    def test_owner_session_creates_object_owned_by_self(self, client):
        frek_id = "id-fedcba987654-0002"
        token = identity_service.issue_session_token(frek_id)
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "Self Published Artist"}},
            headers=H_holder(token),
        )
        assert r.status_code == 201, r.text
        assert r.json()["owner_id"] == frek_id
        assert r.json()["created_by"] == {"authority": "owner", "actor": frek_id}

    def test_owner_session_cannot_set_a_different_owner_id(self, client):
        token = identity_service.issue_session_token("id-fedcba987654-0003")
        r = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={
                "payload": {
                    "display_name": "Impersonation Attempt",
                    "owner_id": "id-someoneelse-0000",
                }
            },
            headers=H_holder(token),
        )
        assert r.status_code == 403


class TestReadEndpoints:
    def test_get_by_frek_id_round_trips(self, client, issuer_token):
        created = client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "Round Trip Artist"}},
            headers=H_issuer(issuer_token),
        ).json()
        r = client.get(f"/api/v1/registry/objects/frek.artist/{created['frek_id']}")
        assert r.status_code == 200, r.text
        assert r.json()["display_name"] == "Round Trip Artist"

    def test_get_unknown_frek_id_is_404(self, client):
        r = client.get("/api/v1/registry/objects/frek.artist/frek-doesnotexist-0000")
        assert r.status_code == 404

    def test_list_respects_owner_filter_and_pagination(self, client, issuer_token):
        for i in range(3):
            client.post(
                "/api/v1/registry/objects/frek.artist",
                json={
                    "payload": {
                        "display_name": f"Artist {i}",
                        "owner_id": "id-filtertarget-0001",
                    }
                },
                headers=H_issuer(issuer_token),
            )
        r = client.get(
            "/api/v1/registry/objects/frek.artist",
            params={"owner_id": "id-filtertarget-0001", "limit": 2},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["namespace"] == "frek.artist"
        assert body["total"] == 3
        assert len(body["objects"]) == 2
        assert all(o["owner_id"] == "id-filtertarget-0001" for o in body["objects"])

    def test_list_namespace_isolation(self, client, issuer_token):
        client.post(
            "/api/v1/registry/objects/frek.artist",
            json={"payload": {"display_name": "Isolation Check"}},
            headers=H_issuer(issuer_token),
        )
        r = client.get("/api/v1/registry/objects/frek.track")
        assert r.status_code == 200
        assert r.json()["objects"] == []


class TestDbNotConfigured:
    """_require_db()'s 503 branch — a router mounted without set_db()."""

    def test_list_without_set_db_returns_503(self):
        registry_routes.db = None
        app = FastAPI()
        app.include_router(registry_routes.registry_router, prefix="/api/v1")
        c = TestClient(app)
        r = c.get("/api/v1/registry/objects/frek.artist")
        assert r.status_code == 503
