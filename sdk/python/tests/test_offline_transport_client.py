"""End-to-end test for FrekcoreOfflineTransportClient — real request/
response cycles against the actual `offline_transport_router` FastAPI
app, no live server or network needed.

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
os.environ.setdefault(
    "FREK_PASSPORT_KEY_PATH", "/tmp/frekcore_sdk_test_offline_transport_passport_key.pem"
)

import offline_transport.routes as offline_transport_routes  # noqa: E402
from offline_transport.routes import offline_transport_router  # noqa: E402
from frekcore_sdk import FrekcoreOfflineTransportClient, NotFoundError  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def sdk_client_with_db():
    import mongomock_motor

    db = mongomock_motor.AsyncMongoMockClient()["frekcore_sdk_test_offline_transport"]
    offline_transport_routes.set_db(db)

    app = FastAPI()
    app.include_router(offline_transport_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreOfflineTransportClient(client=test_client) as client:
        yield client, db


def test_get_protocols_returns_the_5_historical_plus_new_adapters(sdk_client_with_db):
    client, _db = sdk_client_with_db
    result = client.get_protocols()
    assert "protocols" in result
    assert "bluetooth_ble" in result["protocols"]


def test_get_envelope_returns_the_seeded_envelope(sdk_client_with_db):
    client, db = sdk_client_with_db

    async def _seed():
        await db.transport_envelopes.insert_one(
            {
                "envelope_id": "env-1",
                "issuer_id": "admin",
                "authority": "admin",
                "sync_status": "pending",
            }
        )

    asyncio.run(_seed())
    envelope = client.get_envelope("env-1", admin_key=ADMIN_KEY)
    assert envelope["envelope_id"] == "env-1"


def test_get_envelope_unknown_id_raises_not_found_error(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(NotFoundError):
        client.get_envelope("does-not-exist", admin_key=ADMIN_KEY)
