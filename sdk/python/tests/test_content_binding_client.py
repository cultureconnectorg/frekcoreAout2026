"""End-to-end test for FrekcoreContentBindingClient — real request/
response cycles against the actual `content_binding_router` FastAPI app,
no live server or network needed (same in-process TestClient technique as
test_registry_client.py/test_identity_client.py).

Run from repo root:
    PYTHONPATH=backend:sdk/python python3 -m pytest sdk/python/tests -v
"""

import asyncio
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

import content_binding.routes as content_binding_routes  # noqa: E402
from content_binding.routes import content_binding_router  # noqa: E402
from frekcore_sdk import FrekcoreContentBindingClient, NotFoundError  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture()
def sdk_client_with_db():
    import mongomock_motor

    db = mongomock_motor.AsyncMongoMockClient()["frekcore_sdk_test_content_binding"]
    content_binding_routes.set_db(db)

    app = FastAPI()
    app.include_router(content_binding_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreContentBindingClient(client=test_client) as client:
        yield client, db


def test_get_binding_returns_the_seeded_binding(sdk_client_with_db):
    client, db = sdk_client_with_db

    async def _seed():
        await db.content_bindings.insert_one(
            {
                "binding_id": "b-1",
                "frek_id": "fk-1",
                "exact_hash": "a" * 64,
                "exact_hash_algorithm": "sha256",
                "signal_fingerprint": {
                    "algorithm": "frek_signal_v1",
                    "algorithm_version": "1.0.0",
                    "dimensions": 528,
                    "vector": [0.1] * 528,
                    "sample_rate": 44100,
                    "duration_seconds": 1.0,
                },
                "computed_at": "2026-09-03T00:00:00+00:00",
                "produced_by": "admin",
                "proof_state": "fingerprint",
            }
        )

    asyncio.run(_seed())
    binding = client.get_binding("b-1")
    assert binding["binding_id"] == "b-1"
    assert binding["frek_id"] == "fk-1"


def test_get_binding_unknown_id_raises_not_found_error(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(NotFoundError):
        client.get_binding("does-not-exist")


def test_list_bindings_returns_all_bindings_for_object(sdk_client_with_db):
    client, db = sdk_client_with_db

    async def _seed():
        for i in range(2):
            await db.content_bindings.insert_one(
                {
                    "binding_id": f"b-{i}",
                    "frek_id": "fk-1",
                    "exact_hash": f"{i}" * 64,
                    "exact_hash_algorithm": "sha256",
                    "signal_fingerprint": {
                        "algorithm": "frek_signal_v1",
                        "algorithm_version": "1.0.0",
                        "dimensions": 528,
                        "vector": [0.1] * 528,
                        "sample_rate": 44100,
                        "duration_seconds": 1.0,
                    },
                    "computed_at": "2026-09-03T00:00:00+00:00",
                    "produced_by": "admin",
                    "proof_state": "fingerprint",
                }
            )

    asyncio.run(_seed())
    result = client.list_bindings("fk-1")
    assert result["frek_id"] == "fk-1"
    assert result["count"] == 2
