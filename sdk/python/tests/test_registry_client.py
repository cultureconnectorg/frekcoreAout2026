"""End-to-end test for FrekcoreRegistryClient — real request/response cycles
against the actual `registry_router` FastAPI app, no live server or network
needed (FastAPI's TestClient is an httpx.Client subclass bound directly to
the ASGI app in-process, which is exactly the `client=` constructor path
FrekcoreRegistryClient supports for testing).

Run from repo root:
    PYTHONPATH=backend:sdk/python python3 -m pytest sdk/python/tests -v
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "backend"
SDK_DIR = REPO_ROOT / "sdk" / "python"
for p in (BACKEND_DIR, SDK_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-sdk-test")

from registry.routes import registry_router  # noqa: E402
from frekcore_sdk import FrekcoreRegistryClient  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture()
def sdk_client():
    app = FastAPI()
    app.include_router(registry_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreRegistryClient(client=test_client) as client:
        yield client


@pytest.fixture()
def sdk_client_with_db():
    """The /objects instance-store endpoints need a real (mongomock) DB and
    frek_v1's own client-credentials auth wired in — the schema-catalog
    fixture above deliberately has neither (those endpoints are stateless).
    Same technique as backend/tests/test_registry_objects_unit.py."""
    import mongomock_motor
    import frek_v1.auth as frek_v1_auth
    import registry.routes as registry_routes

    db = mongomock_motor.AsyncMongoMockClient()["frekcore_sdk_test_registry_objects"]
    registry_routes.set_db(db)
    frek_v1_auth.set_db(db)

    app = FastAPI()
    app.include_router(registry_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreRegistryClient(client=test_client) as client:
        yield client, db


@pytest.fixture()
def issuer_token(sdk_client_with_db):
    import asyncio

    from frek_v1.utils import create_access_token, hash_secret

    _client, db = sdk_client_with_db
    client_id = "sdk-test-issuer"

    async def _seed():
        await db.frek_clients.insert_one(
            {
                "client_id": client_id,
                "secret_hash": hash_secret("unused"),
                "permissions": ["registry:write"],
                "active": True,
            }
        )

    asyncio.run(_seed())
    return create_access_token(client_id)


def test_list_namespaces_returns_all_eight(sdk_client):
    namespaces = sdk_client.list_namespaces()
    names = {n.namespace for n in namespaces}
    assert names == {
        "frek.artist",
        "frek.track",
        "frek.album",
        "frek.work",
        "frek.certificate",
        "frek.organization",
        "frek.wallet",
        "frek.event",
    }


def test_get_namespace_schema_round_trips_through_sdk(sdk_client):
    schema = sdk_client.get_namespace_schema("frek.artist")
    assert schema["x-frek-namespace"] == "frek.artist"


def test_validate_valid_and_invalid_payloads(sdk_client):
    valid = sdk_client.validate(
        "frek.artist",
        {
            "frek_id": "id-abcdef012345-ab12",
            "entity_type": "frek.artist",
            "status": "active",
            "created_at": "2026-08-30T00:00:00Z",
            "display_name": "Luciole",
        },
    )
    assert valid.valid is True
    assert valid.errors == []

    invalid = sdk_client.validate("frek.artist", {"entity_type": "frek.artist"})
    assert invalid.valid is False
    assert invalid.errors  # non-empty


def test_list_events_returns_catalog(sdk_client):
    body = sdk_client.list_events()
    assert len(body["catalog"]) >= 8


def test_list_versions(sdk_client):
    body = sdk_client.list_versions()
    assert "v1" in body["versions"]


def test_create_object_without_credential_raises(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(Exception):
        client.create_object("frek.artist", {"display_name": "No Auth"})


def test_create_object_with_bearer_token_returns_the_real_envelope(
    sdk_client_with_db, issuer_token
):
    client, _db = sdk_client_with_db
    obj = client.create_object(
        "frek.artist", {"display_name": "SDK Artist"}, bearer_token=issuer_token
    )
    assert obj["frek_id"].startswith("frek-")
    assert obj["entity_type"] == "frek.artist"
    assert obj["status"] == "draft"
    assert obj["display_name"] == "SDK Artist"


def test_create_then_get_object_round_trips(sdk_client_with_db, issuer_token):
    client, _db = sdk_client_with_db
    created = client.create_object(
        "frek.artist", {"display_name": "Round Trip"}, bearer_token=issuer_token
    )
    fetched = client.get_object("frek.artist", created["frek_id"])
    assert fetched["display_name"] == "Round Trip"


def test_list_objects_respects_owner_filter(sdk_client_with_db, issuer_token):
    client, _db = sdk_client_with_db
    client.create_object(
        "frek.artist",
        {"display_name": "Filtered", "owner_id": "id-sdk-filter-target"},
        bearer_token=issuer_token,
    )
    result = client.list_objects("frek.artist", owner_id="id-sdk-filter-target")
    assert result["namespace"] == "frek.artist"
    assert result["count"] >= 1
    assert all(o["owner_id"] == "id-sdk-filter-target" for o in result["objects"])


def test_get_unknown_object_raises(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(Exception):
        client.get_object("frek.artist", "frek-doesnotexist-0000")
