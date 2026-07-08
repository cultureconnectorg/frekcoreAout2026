"""Backend tests for FREKCORE Identity Engine (Passkey/WebAuthn attached to FREK-ID)."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://culture-chain.preview.emergentagent.com").rstrip("/")
EXPECTED_RP_ID = "culture-chain.preview.emergentagent.com"
FREK_ID_RE = re.compile(r"^id-[0-9a-f]{12}-[0-9a-f]{4}$")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def created_identity(api):
    r = api.post(f"{BASE_URL}/api/v1/identity/init", json={
        "session_id": "TEST_sess_engine_1",
        "identity_type": "individual",
    })
    assert r.status_code == 200, r.text
    return r.json()


# ------------- INIT -------------
class TestIdentityInit:
    def test_init_individual_ok(self, created_identity):
        d = created_identity
        assert FREK_ID_RE.match(d["frek_id"]), d["frek_id"]
        assert d["identity_type"] == "individual"
        assert d["status"] == "anonymous"
        assert d["credentials_count"] == 0
        assert d["protected"] is False
        assert "linked_moments_count" in d

    def test_init_invalid_type_returns_400(self, api):
        r = api.post(f"{BASE_URL}/api/v1/identity/init", json={"identity_type": "alien"})
        # Pydantic Literal enforcement returns 422 by FastAPI, our code raises 400 only if it slips through
        assert r.status_code in (400, 422), r.text

    def test_init_professional_ok(self, api):
        r = api.post(f"{BASE_URL}/api/v1/identity/init", json={"identity_type": "professional"})
        assert r.status_code == 200
        assert r.json()["identity_type"] == "professional"


# ------------- REGISTER BEGIN -------------
class TestRegisterBegin:
    def test_register_begin_returns_valid_options(self, api, created_identity):
        fid = created_identity["frek_id"]
        r = api.post(f"{BASE_URL}/api/v1/identity/{fid}/register/begin", json={})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["rp"]["id"] == EXPECTED_RP_ID, f"rp.id must be {EXPECTED_RP_ID} not {d['rp']['id']}"
        assert d["rp"]["name"] == "FREKCORE"
        assert isinstance(d["challenge"], str) and len(d["challenge"]) > 20
        assert d["user"]["id"]  # base64url string
        assert isinstance(d["pubKeyCredParams"], list) and len(d["pubKeyCredParams"]) > 0
        assert "authenticatorSelection" in d
        assert d["authenticatorSelection"]["userVerification"] in ("preferred", "required", "discouraged")

    def test_register_begin_unknown_frek_id_404(self, api):
        r = api.post(f"{BASE_URL}/api/v1/identity/id-000000000000-0000/register/begin", json={})
        assert r.status_code == 404


# ------------- AUTHENTICATE BEGIN -------------
class TestAuthenticateBegin:
    def test_authenticate_begin_returns_options(self, api):
        r = api.post(f"{BASE_URL}/api/v1/identity/authenticate/begin", json={})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["rpId"] == EXPECTED_RP_ID, f"rpId must be {EXPECTED_RP_ID} not {d.get('rpId')}"
        assert isinstance(d["challenge"], str) and len(d["challenge"]) > 20


# ------------- GET IDENTITY PUBLIC -------------
class TestGetIdentity:
    def test_get_public_view(self, api, created_identity):
        fid = created_identity["frek_id"]
        r = api.get(f"{BASE_URL}/api/v1/identity/{fid}")
        assert r.status_code == 200
        d = r.json()
        assert d["frek_id"] == fid
        assert "credentials" not in d, "credentials must never be leaked"
        assert d["credentials_count"] == 0
        assert d["protected"] is False

    def test_get_unknown_404(self, api):
        r = api.get(f"{BASE_URL}/api/v1/identity/id-000000000000-0000")
        assert r.status_code == 404


# ------------- AUTH GUARDS -------------
class TestAuthGuards:
    def test_me_without_session_401(self, api):
        r = api.get(f"{BASE_URL}/api/v1/identity/me")
        assert r.status_code == 401

    def test_me_with_fake_session_401(self, api):
        r = api.get(f"{BASE_URL}/api/v1/identity/me", headers={"X-FREK-Session": "fake.token"})
        assert r.status_code == 401

    def test_get_objects_without_session_401(self, api, created_identity):
        fid = created_identity["frek_id"]
        r = api.get(f"{BASE_URL}/api/v1/identity/{fid}/objects")
        assert r.status_code == 401

    def test_get_objects_with_fake_session_401(self, api, created_identity):
        fid = created_identity["frek_id"]
        r = api.get(
            f"{BASE_URL}/api/v1/identity/{fid}/objects",
            headers={"X-FREK-Session": "fake.token"},
        )
        assert r.status_code == 401

    def test_link_object_without_session_401(self, api):
        r = api.post(f"{BASE_URL}/api/v1/identity/link-object", json={"object_id": "m-fake"})
        assert r.status_code == 401

    def test_link_object_with_fake_session_401(self, api):
        r = api.post(
            f"{BASE_URL}/api/v1/identity/link-object",
            json={"object_id": "m-fake"},
            headers={"X-FREK-Session": "fake.token"},
        )
        assert r.status_code == 401


# ------------- REGRESSION SMOKE -------------
class TestRegressionSmoke:
    def test_fk_stats(self, api):
        r = api.get(f"{BASE_URL}/api/v1/fk/stats")
        assert r.status_code == 200, r.text

    def test_moment_stats(self, api):
        r = api.get(f"{BASE_URL}/api/v1/moment/stats")
        assert r.status_code == 200, r.text

    def test_moment_sign_json(self, api):
        r = api.post(f"{BASE_URL}/api/v1/moment/sign", json={
            "email": "TEST_regression@example.com",
            "content": "test regression moment",
            "session_id": "TEST_sess_regression",
        })
        # Accept 200 (created) or 429 (rate limit); anything else is a failure
        assert r.status_code in (200, 201, 429), r.text

    def test_moment_sign_media_multipart(self, api):
        files = {
            "file": ("test.txt", b"hello world regression", "text/plain"),
        }
        data = {
            "email": "TEST_regression_media@example.com",
            "session_id": "TEST_sess_regression_media",
            "declared_type": "text",
        }
        r = requests.post(f"{BASE_URL}/api/v1/moment/sign-media", data=data, files=files)
        # Accept 200/201 or 4xx client errors indicating endpoint alive (not 5xx)
        assert r.status_code < 500, r.text

    def test_fk_create_multipart(self, api):
        files = {"file": ("test.txt", b"fk regression bytes", "text/plain")}
        data = {
            "email": "TEST_regression_fk@example.com",
            "title": "TEST regression fk",
            "session_id": "TEST_sess_regression_fk",
        }
        r = requests.post(f"{BASE_URL}/api/v1/fk/create", data=data, files=files)
        assert r.status_code < 500, r.text
