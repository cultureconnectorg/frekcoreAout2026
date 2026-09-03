"""End-to-end test for FrekcoreRelationshipGraphClient — real request/
response cycles against the actual `relationship_graph_router` FastAPI
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

import relationship_graph.routes as relationship_graph_routes  # noqa: E402
from relationship_graph.routes import relationship_graph_router  # noqa: E402
from frekcore_sdk import FrekcoreRelationshipGraphClient  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def sdk_client_with_db():
    import mongomock_motor

    db = mongomock_motor.AsyncMongoMockClient()["frekcore_sdk_test_relationship_graph"]
    relationship_graph_routes.set_db(db)

    app = FastAPI()
    app.include_router(relationship_graph_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreRelationshipGraphClient(client=test_client) as client:
        yield client, db


def test_create_relationship_then_read_neighbors(sdk_client_with_db):
    client, _db = sdk_client_with_db
    created = client.create_relationship(
        subject_id="OBJ-1",
        predicate="created_by",
        object_id="ARTIST-1",
        origin="declared",
        statement="OBJ-1 was created by ARTIST-1",
        admin_key=ADMIN_KEY,
    )
    assert created["subject_id"] == "OBJ-1"
    assert created["predicate"] == "created_by"
    assert created["layer"] == "trust"

    neighbors = client.get_neighbors("OBJ-1")
    assert neighbors["entity_id"] == "OBJ-1"
    assert neighbors["neighbors_count"] == 1


def test_get_neighbors_of_unknown_entity_returns_empty_not_an_error(sdk_client_with_db):
    client, _db = sdk_client_with_db
    result = client.get_neighbors("no-such-entity")
    assert result["neighbors_count"] == 0
