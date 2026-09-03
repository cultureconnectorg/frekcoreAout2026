"""End-to-end test for FrekcoreCreativeLifecycleClient — real request/
response cycles against the actual `creative_lifecycle_router` FastAPI
app, no live server or network needed.

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
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import creative_lifecycle.routes as creative_lifecycle_routes  # noqa: E402
from creative_lifecycle.routes import creative_lifecycle_router  # noqa: E402
from frekcore_sdk import (  # noqa: E402
    AuthorityError,
    FrekcoreCreativeLifecycleClient,
    NotFoundError,
)

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def sdk_client_with_db():
    import mongomock_motor

    db = mongomock_motor.AsyncMongoMockClient()["frekcore_sdk_test_creative_lifecycle"]
    creative_lifecycle_routes.set_db(db)

    app = FastAPI()
    app.include_router(creative_lifecycle_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreCreativeLifecycleClient(client=test_client) as client:
        yield client, db


def test_start_genesis_with_admin_key_then_read_history(sdk_client_with_db):
    client, _db = sdk_client_with_db
    result = client.start_genesis(concept="a new song", admin_key=ADMIN_KEY)
    assert result["stage"] == "GENESIS"
    pre_id = result["pre_id"]

    history = client.get_history(pre_id)
    assert history["pre_id"] == pre_id
    assert history["current_stage"] == "GENESIS"


def test_start_genesis_without_any_auth_raises_authority_error(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(AuthorityError):
        client.start_genesis(concept="anonymous attempt")


def test_get_history_unknown_pre_id_raises_not_found_error(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(NotFoundError):
        client.get_history("does-not-exist")
