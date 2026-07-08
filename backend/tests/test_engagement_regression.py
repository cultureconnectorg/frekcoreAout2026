"""FREKCORE — Iteration 23 regression tests for WebAuthn diag + engagement session.
Validates the 5 backend endpoints listed in the review request.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://culture-chain.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def session_id():
    return f"TEST_engage_sess_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def identity(session_id):
    """Create an anonymous identity to use for register/begin ceremony options."""
    r = requests.post(
        f"{BASE_URL}/api/v1/identity/init",
        json={"session_id": session_id, "identity_type": "individual"},
        timeout=15,
    )
    assert r.status_code == 200, f"init failed: {r.status_code} {r.text}"
    data = r.json()
    assert "frek_id" in data
    assert data["frek_id"].startswith("id-")
    return data


# --- 1. identity/init ---
class TestIdentityInit:
    def test_init_returns_valid_frek_id(self, identity):
        assert identity["frek_id"].startswith("id-")
        # id-XXXXXXXXXXXX-XXXX (id- + 12 hex + - + 4 hex) => 22 chars total incl. "id-"
        parts = identity["frek_id"].split("-")
        assert len(parts) == 3
        assert parts[0] == "id"

    def test_init_default_type_individual(self, identity):
        assert identity.get("identity_type") in ("individual", None)


# --- 2. identity/register/begin ---
class TestRegisterBegin:
    def test_register_begin_returns_full_options(self, identity):
        r = requests.post(
            f"{BASE_URL}/api/v1/identity/{identity['frek_id']}/register/begin",
            json={},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        opts = r.json()
        # Required WebAuthn PublicKeyCredentialCreationOptions fields
        assert "rp" in opts and "id" in opts["rp"], f"missing rp.id: {opts}"
        assert "challenge" in opts and len(opts["challenge"]) > 0
        assert "user" in opts and "id" in opts["user"]
        assert "pubKeyCredParams" in opts and isinstance(opts["pubKeyCredParams"], list) and len(opts["pubKeyCredParams"]) >= 1
        assert "authenticatorSelection" in opts


# --- 3. identity/authenticate/begin ---
class TestAuthenticateBegin:
    def test_authenticate_begin_returns_options(self):
        r = requests.post(
            f"{BASE_URL}/api/v1/identity/authenticate/begin",
            json={},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        opts = r.json()
        assert "challenge" in opts
        assert "rpId" in opts or ("rp" in opts and "id" in opts["rp"])


# --- 4. moment/sign ---
class TestMomentSign:
    def test_moment_sign_returns_proof(self, session_id):
        r = requests.post(
            f"{BASE_URL}/api/v1/moment/sign",
            json={
                "title": "TEST_engagement_moment",
                "session_id": session_id,
                "geo": None,
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "frek_id" in data
        assert data["frek_id"].startswith("mo-") or data["frek_id"].startswith("id-") or "-" in data["frek_id"]
        assert "created_at" in data
        assert "layers_captured" in data


# --- 5. fk/create ---
class TestFkCreate:
    def test_fk_create_returns_object(self, session_id):
        # /fk/create uses multipart/form-data
        data = {
            "title": "TEST_engagement_fk",
            "object_type": "other",
            "primary_creator_name": "TEST_creator",
            "primary_creator_role": "creator",
            "keep": "false",
            "return_json": "true",
        }
        files = [
            ("files", ("hello.txt", b"hello world engagement test", "text/plain")),
        ]
        r = requests.post(
            f"{BASE_URL}/api/v1/fk/create",
            data=data,
            files=files,
            timeout=15,
        )
        assert r.status_code == 200, f"fk/create failed: {r.status_code} {r.text[:400]}"
        # return_json=true returns JSON body with fk info
        body = r.json()
        assert "frek_id" in body or "fk_id" in body or "id" in body or "info" in body
