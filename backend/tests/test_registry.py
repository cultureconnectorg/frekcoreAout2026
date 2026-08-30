"""Tests unitaires du FREK Registry (Bloc 1).

Contrairement au reste de la suite backend (integration via serveur live,
voir tests/conftest.py), ce module est sans etat (pas de MongoDB) : on peut
donc le tester directement via TestClient sur une app FastAPI isolee.
"""
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from registry import service  # noqa: E402
from registry.routes import registry_router  # noqa: E402

EXPECTED_NAMESPACES = {
    "frek.artist",
    "frek.track",
    "frek.album",
    "frek.work",
    "frek.certificate",
    "frek.organization",
    "frek.wallet",
    "frek.event",
}


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(registry_router, prefix="/api/v1")
    return TestClient(app)


def test_versions_lists_v1(client):
    resp = client.get("/api/v1/registry/versions")
    assert resp.status_code == 200
    body = resp.json()
    assert "v1" in body["versions"]
    assert body["default"] == "v1"


def test_namespaces_cover_bloc1_catalog(client):
    resp = client.get("/api/v1/registry/namespaces")
    assert resp.status_code == 200
    namespaces = {row["namespace"] for row in resp.json()}
    assert namespaces == EXPECTED_NAMESPACES


def test_get_schema_for_each_namespace_is_valid_json_schema(client):
    for ns in EXPECTED_NAMESPACES:
        resp = client.get(f"/api/v1/registry/namespaces/{ns}")
        assert resp.status_code == 200, ns
        schema = resp.json()
        assert schema["x-frek-namespace"] == ns
        # allOf[0] must be the inlined _base.schema.json (no unresolved $ref left).
        assert "$ref" not in schema["allOf"][0]
        assert "frek_id" in schema["allOf"][0]["properties"]


def test_unknown_namespace_is_404(client):
    resp = client.get("/api/v1/registry/namespaces/frek.does-not-exist")
    assert resp.status_code == 404


def test_validate_valid_artist_payload(client):
    payload = {
        "frek_id": "id-abcdef012345-ab12",
        "entity_type": "frek.artist",
        "status": "active",
        "created_at": "2026-08-30T00:00:00Z",
        "display_name": "Luciole",
    }
    resp = client.post(
        "/api/v1/registry/validate",
        json={"namespace": "frek.artist", "payload": payload},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["errors"] == []


def test_validate_rejects_missing_required_field(client):
    payload = {
        "frek_id": "id-abcdef012345-ab12",
        "entity_type": "frek.artist",
        "status": "active",
        "created_at": "2026-08-30T00:00:00Z",
        # display_name manquant
    }
    resp = client.post(
        "/api/v1/registry/validate",
        json={"namespace": "frek.artist", "payload": payload},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert any("display_name" in err for err in body["errors"])


def test_validate_rejects_bad_frek_id_pattern(client):
    payload = {
        "frek_id": "not-a-valid-id",
        "entity_type": "frek.organization",
        "status": "active",
        "created_at": "2026-08-30T00:00:00Z",
        "legal_name": "CVLN Group",
        "org_type": "group",
    }
    resp = client.post(
        "/api/v1/registry/validate",
        json={"namespace": "frek.organization", "payload": payload},
    )
    body = resp.json()
    assert body["valid"] is False


def test_validate_unknown_namespace_is_404(client):
    resp = client.post(
        "/api/v1/registry/validate",
        json={"namespace": "frek.nope", "payload": {}},
    )
    assert resp.status_code == 404


def test_event_registry_catalog_shape(client):
    resp = client.get("/api/v1/registry/events")
    assert resp.status_code == 200
    body = resp.json()
    assert "catalog" in body and isinstance(body["catalog"], list)
    assert len(body["catalog"]) >= 8
    for entry in body["catalog"]:
        assert "event_type" in entry
        assert "implemented" in entry
        assert "status" in entry


def test_service_all_namespace_schemas_are_valid_draft202012():
    """Chaque schema namespace doit etre un JSON Schema draft 2020-12 valide (base inlinee)."""
    from jsonschema import Draft202012Validator

    for entry in service.list_namespaces():
        Draft202012Validator.check_schema(entry.schema)
