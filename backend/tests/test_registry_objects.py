"""Registry instance store (P1: POST/GET /api/v1/registry/objects/{namespace})
— live regression tests.

reports/08_NEXT_INTEGRATION.md item 2 / reports/FREKCORE_COMPLETION_BACKLOG.md
P1 #7. Requires a live server + MongoDB (or the mongomock substitute) — see
backend/tests/test_identity_lifecycle.py for the same live-suite convention
this file follows.
"""
import os
import sys
from pathlib import Path

import pytest
import requests

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from identity_engine import service as identity_service  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1/registry"

KILTIKONET_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
KILTIKONET_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "")


@pytest.fixture(scope="module")
def issuer_token():
    """A real client-credentials bearer token for the seeded CC2026 client
    (server.py: permissions include "registry:write" as of this P1 pass)."""
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": KILTIKONET_ID,
            "client_secret": KILTIKONET_SECRET,
        },
        timeout=5,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def H_issuer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def holder_session():
    """A real holder frek_id + a validly-signed session token, minted
    in-process the same way identity_engine/service.py:issue_session_token
    mints one after a real WebAuthn ceremony — no virtual authenticator is
    available in this sandbox to simulate that ceremony end-to-end (same
    documented limitation as test_identity_lifecycle.py), so this fixture
    exercises the exact signing function rather than skipping owner-path
    coverage entirely."""
    frek_id = f"id-{os.urandom(6).hex()}-{os.urandom(2).hex()}"
    token = identity_service.issue_session_token(frek_id)
    return frek_id, token


def H_holder(token):
    return {"X-FREK-Session": token}


class TestUnknownNamespace:
    def test_create_unknown_namespace_is_404(self, issuer_token):
        r = requests.post(
            f"{API}/objects/frek.not-a-namespace",
            json={"payload": {}},
            headers=H_issuer(issuer_token),
            timeout=5,
        )
        assert r.status_code == 404

    def test_list_unknown_namespace_is_404(self):
        r = requests.get(f"{API}/objects/frek.not-a-namespace", timeout=5)
        assert r.status_code == 404

    def test_get_unknown_namespace_is_404(self):
        r = requests.get(f"{API}/objects/frek.not-a-namespace/frek-x", timeout=5)
        assert r.status_code == 404


class TestCreateAuthority:
    def test_create_without_any_credential_is_403(self):
        r = requests.post(
            f"{API}/objects/frek.artist", json={"payload": {"display_name": "No Auth"}}, timeout=5
        )
        assert r.status_code == 403

    def test_create_with_bad_bearer_token_is_403(self):
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Bad Token"}},
            headers={"Authorization": "Bearer not-a-real-token"},
            timeout=5,
        )
        assert r.status_code == 403

    def test_create_with_client_lacking_registry_write_is_403(self):
        # cvl-brain is seeded with only ["stats"] — never registry:write.
        cvl_id = os.environ.get("FREK_CLIENT_CVLBRAIN_ID", "cvl-brain")
        cvl_secret = os.environ.get("FREK_CLIENT_CVLBRAIN_SECRET", "")
        if not cvl_secret:
            pytest.skip("FREK_CLIENT_CVLBRAIN_SECRET not set in this environment")
        tok = requests.post(
            f"{BASE_URL}/api/v1/auth/token",
            json={"grant_type": "client_credentials", "client_id": cvl_id, "client_secret": cvl_secret},
            timeout=5,
        ).json()["access_token"]
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Wrong Scope"}},
            headers=H_issuer(tok),
            timeout=5,
        )
        assert r.status_code == 403


class TestCreateAsIssuer:
    def test_create_valid_object_returns_full_envelope(self, issuer_token):
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Test Artist Issuer"}},
            headers=H_issuer(issuer_token),
            timeout=5,
        )
        assert r.status_code == 201, r.text
        obj = r.json()
        assert obj["frek_id"].startswith("frek-")
        assert obj["entity_type"] == "frek.artist"
        assert obj["status"] == "draft"
        assert obj["version"] == 1
        assert obj["owner_id"] is None
        assert obj["display_name"] == "Test Artist Issuer"
        assert "created_at" in obj

    def test_entity_type_override_in_payload_is_ignored(self, issuer_token):
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "X", "entity_type": "frek.track"}},
            headers=H_issuer(issuer_token),
            timeout=5,
        )
        assert r.status_code == 201, r.text
        assert r.json()["entity_type"] == "frek.artist"

    def test_invalid_payload_missing_required_field_is_422(self, issuer_token):
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"legal_name": "no display_name"}},
            headers=H_issuer(issuer_token),
            timeout=5,
        )
        assert r.status_code == 422
        assert "display_name" in str(r.json())

    def test_issuer_can_set_arbitrary_owner_id(self, issuer_token):
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Owned Artist", "owner_id": "id-abc123def456-0001"}},
            headers=H_issuer(issuer_token),
            timeout=5,
        )
        assert r.status_code == 201, r.text
        assert r.json()["owner_id"] == "id-abc123def456-0001"

    def test_duplicate_explicit_frek_id_in_same_namespace_is_409(self, issuer_token):
        explicit_id = f"frek-{os.urandom(6).hex()}-{os.urandom(2).hex()}"
        body = {"payload": {"display_name": "Dup", "frek_id": explicit_id}}
        r1 = requests.post(f"{API}/objects/frek.artist", json=body, headers=H_issuer(issuer_token), timeout=5)
        assert r1.status_code == 201, r1.text
        r2 = requests.post(f"{API}/objects/frek.artist", json=body, headers=H_issuer(issuer_token), timeout=5)
        assert r2.status_code == 409


class TestCreateAsOwner:
    def test_owner_session_creates_object_owned_by_self(self, holder_session):
        frek_id, token = holder_session
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Self Published Artist"}},
            headers=H_holder(token),
            timeout=5,
        )
        assert r.status_code == 201, r.text
        assert r.json()["owner_id"] == frek_id

    def test_owner_session_cannot_set_a_different_owner_id(self, holder_session):
        _frek_id, token = holder_session
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Impersonation Attempt", "owner_id": "id-someoneelse-0000"}},
            headers=H_holder(token),
            timeout=5,
        )
        assert r.status_code == 403

    def test_invalid_session_token_is_403(self):
        r = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Bad Session"}},
            headers={"X-FREK-Session": "not-a-real-session-token"},
            timeout=5,
        )
        assert r.status_code == 403


class TestReadEndpoints:
    def test_get_by_frek_id_round_trips(self, issuer_token):
        create = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Round Trip Artist"}},
            headers=H_issuer(issuer_token),
            timeout=5,
        ).json()
        r = requests.get(f"{API}/objects/frek.artist/{create['frek_id']}", timeout=5)
        assert r.status_code == 200, r.text
        assert r.json()["display_name"] == "Round Trip Artist"

    def test_get_unknown_frek_id_is_404(self):
        r = requests.get(f"{API}/objects/frek.artist/frek-doesnotexist-0000", timeout=5)
        assert r.status_code == 404

    def test_list_includes_created_object_and_respects_owner_filter(self, holder_session, issuer_token):
        frek_id, token = holder_session
        created = requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Filter Me"}},
            headers=H_holder(token),
            timeout=5,
        ).json()

        r = requests.get(f"{API}/objects/frek.artist", params={"owner_id": frek_id}, timeout=5)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["namespace"] == "frek.artist"
        assert any(o["frek_id"] == created["frek_id"] for o in body["objects"])
        assert all(o["owner_id"] == frek_id for o in body["objects"])

    def test_list_namespace_isolation(self, issuer_token):
        """An object created in frek.artist must never appear when listing
        a different namespace — namespace is part of the storage key."""
        requests.post(
            f"{API}/objects/frek.artist",
            json={"payload": {"display_name": "Isolation Check"}},
            headers=H_issuer(issuer_token),
            timeout=5,
        )
        r = requests.get(f"{API}/objects/frek.track", timeout=5)
        assert r.status_code == 200
        assert all(o["entity_type"] == "frek.track" for o in r.json()["objects"])
