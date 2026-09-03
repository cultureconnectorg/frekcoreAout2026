"""End-to-end test for FrekcoreIdentityClient — real request/response cycles
against the actual `identity_router` FastAPI app, no live server or network
needed (same in-process TestClient technique as test_registry_client.py).

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

from identity_engine.routes import identity_router  # noqa: E402
import identity_engine.routes as identity_routes  # noqa: E402
from identity_engine import service as identity_service  # noqa: E402
from frekcore_sdk import FrekcoreIdentityClient  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def sdk_client_with_db():
    """identity_engine needs a real (mongomock) DB wired in — same
    technique as test_registry_client.py's `sdk_client_with_db` and
    backend/tests/test_registry_objects_unit.py."""
    import mongomock_motor

    db = mongomock_motor.AsyncMongoMockClient()["frekcore_sdk_test_identity"]
    identity_routes.set_db(db)

    app = FastAPI()
    app.include_router(identity_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreIdentityClient(client=test_client) as client:
        yield client, db


@pytest.fixture()
def seeded_identity(sdk_client_with_db):
    """Inserts one FREKIdentity directly (no WebAuthn ceremony needed for
    these read-only endpoints) and mints a real holder session token via
    `identity_service.issue_session_token` — the exact function
    `authenticate_complete` itself calls."""
    import asyncio

    _client, db = sdk_client_with_db
    frek_id = "id-sdktest0001-ab12"

    async def _seed():
        await db.frek_persons.insert_one(
            {
                "frek_id": frek_id,
                "identity_type": "individual",
                "display_name": "SDK Test Identity",
                "status": "active",
                "credentials": [{"secret": "must-never-leak"}],
                "linked_objects": ["frek-fk-1"],
                "linked_sessions": [],
                "created_at": "2026-08-31T00:00:00+00:00",
            }
        )

    asyncio.run(_seed())
    session_token = identity_service.issue_session_token(frek_id)
    return frek_id, session_token


def test_get_identity_returns_public_view_no_auth_needed(
    seeded_identity, sdk_client_with_db
):
    frek_id, _session_token = seeded_identity
    client, _db = sdk_client_with_db
    identity = client.get_identity(frek_id)
    assert identity["frek_id"] == frek_id
    assert identity["display_name"] == "SDK Test Identity"
    assert "credentials" not in identity


def test_get_identity_unknown_frek_id_raises(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(Exception):
        client.get_identity("id-doesnotexist-0000")


def test_get_me_without_session_raises(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(Exception):
        client.get_me("not-a-real-session-token")


def test_get_me_with_valid_session_returns_own_identity(
    seeded_identity, sdk_client_with_db
):
    frek_id, session_token = seeded_identity
    client, _db = sdk_client_with_db
    me = client.get_me(session_token)
    assert me["frek_id"] == frek_id


def test_get_linked_objects_requires_matching_session(
    seeded_identity, sdk_client_with_db
):
    frek_id, session_token = seeded_identity
    client, _db = sdk_client_with_db
    result = client.get_linked_objects(frek_id, session_token)
    assert result["frek_id"] == frek_id
    assert result["linked_sessions_count"] == 0


def test_get_linked_objects_wrong_session_raises(seeded_identity, sdk_client_with_db):
    frek_id, _session_token = seeded_identity
    client, _db = sdk_client_with_db
    other_session = identity_service.issue_session_token("id-someoneelse-9999")
    with pytest.raises(Exception):
        client.get_linked_objects(frek_id, other_session)


def test_search_identities_without_admin_key_raises(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(Exception):
        client.search_identities(admin_key="not-the-real-key")


def test_search_identities_with_admin_key_finds_seeded_identity(
    seeded_identity, sdk_client_with_db
):
    frek_id, _session_token = seeded_identity
    client, _db = sdk_client_with_db
    result = client.search_identities(admin_key=ADMIN_KEY, display_name="SDK Test")
    assert result["total"] >= 1
    assert any(i["frek_id"] == frek_id for i in result["identities"])
    # Credentials never leak through the SDK's search results either.
    assert all("credentials" not in i for i in result["identities"])
