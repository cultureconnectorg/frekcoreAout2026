"""End-to-end test for FrekcoreRegistryClient — real request/response cycles
against the actual `registry_router` FastAPI app, no live server or network
needed (FastAPI's TestClient is an httpx.Client subclass bound directly to
the ASGI app in-process, which is exactly the `client=` constructor path
FrekcoreRegistryClient supports for testing).

Run from repo root:
    PYTHONPATH=backend:sdk/python python3 -m pytest sdk/python/tests -v
"""

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
