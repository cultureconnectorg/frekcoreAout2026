"""Tests d'integration pour l'ecosystem registry."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def test_ecosystem_root_returns_registry():
    r = client.get("/api/v1/ecosystem")
    assert r.status_code == 200
    data = r.json()
    assert "components" in data
    assert "doctrine" in data
    assert "atteste" in data["doctrine"].lower()


def test_ecosystem_lists_core_active_components():
    r = client.get("/api/v1/ecosystem/components")
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()["components"]}
    for expected in {"frekcore", "frek_id", "fk", "frek_chain", "passport"}:
        assert expected in ids, f"{expected} missing from ecosystem"


def test_frekraw_declared_not_installed():
    r = client.get("/api/v1/ecosystem/components/frekraw")
    assert r.status_code == 200
    c = r.json()
    assert c["status"] == "external_specified"
    assert c["integration_points"] == []
    # Doctrine : FREKRAW n'est PAS un langage de programmation
    assert "programming" not in (c.get("role") or "").lower()
    assert c["role"] == "record_certification"


def test_frekansla_declared_not_installed():
    r = client.get("/api/v1/ecosystem/components/frekansla")
    assert r.status_code == 200
    c = r.json()
    assert c["status"] == "external_specified"
    assert c["integration_points"] == []


def test_frek_v3_isolated_from_backend():
    r = client.get("/api/v1/ecosystem/components/frek_v3")
    assert r.status_code == 200
    c = r.json()
    assert c["status"] == "specified_isolated"
    assert c["location"] == "/app/frek_v3/"
    # Aucun endpoint backend pour frek_v3 — c'est intentionnel
    assert c["integration_points"] == []


def test_capabilities_endpoint():
    r = client.get("/api/v1/ecosystem/capabilities")
    assert r.status_code == 200
    caps = r.json()["capabilities"]
    assert caps["identity"]["state"] == "active"
    assert caps["record_certification"]["state"] == "not_installed"
    assert caps["record_certification"]["external"] is True


def test_integrations_endpoint():
    r = client.get("/api/v1/ecosystem/integrations")
    assert r.status_code == 200
    integrations = r.json()["integrations"]
    ids = {i["id"] for i in integrations}
    assert "frekraw" in ids
    assert "frekansla" in ids
    assert "frek_v3" in ids


def test_integration_status_missing_branch_returns_clean_not_installed():
    """Une branche INCONNUE doit renvoyer NOT_INSTALLED, jamais 500."""
    r = client.get("/api/v1/ecosystem/integrations/nonexistent_branch/status")
    assert r.status_code == 200
    assert r.json()["status"] == "NOT_INSTALLED"


def test_integration_status_frekraw():
    r = client.get("/api/v1/ecosystem/integrations/frekraw/status")
    assert r.status_code == 200
    assert r.json()["status"] == "NOT_INSTALLED"


def test_contracts_files_exist_for_specified_branches():
    """Chaque branche non-active doit avoir un contrat d'integration ecrit."""
    for branch in ("frekraw", "frekansla", "frek_v3"):
        contract = Path(f"/app/ecosystem/contracts/{branch}.md")
        assert contract.exists(), f"Contract missing: {contract}"
        content = contract.read_text()
        assert len(content) > 500, f"Contract {branch}.md too thin"


def test_frekraw_contract_forbids_programming_language_interpretation():
    """FREKRAW N'EST PAS UN LANGAGE DE PROGRAMMATION — verifie."""
    content = Path("/app/ecosystem/contracts/frekraw.md").read_text()
    assert "NOT" in content and "programming language" in content.lower()


def test_registry_json_valid():
    reg = json.loads(Path("/app/ecosystem/registry.json").read_text())
    assert reg["registry_version"]
    # Aucune version inventee pour les branches absentes
    for c in reg["components"]:
        if c["status"] == "external_specified":
            assert c["version"] is None, f"{c['id']} claims a version but is not installed"
            assert c["protocol"] is None, f"{c['id']} claims a protocol but is not installed"


def test_regression_health_still_alive():
    """Non-regression : FREKCORE endpoints existants intacts."""
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"
