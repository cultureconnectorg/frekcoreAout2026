"""
Universe Mission (FREKCORE Phase 1-6) — backend contract regression tests.

Contract to verify (per review request):
- GET /api/v1/health/deep 200
- GET /api/v1/moment/stats 200
- GET /api/v1/fk/stats 200
- POST /api/v1/identity/init {"identity_type": "individual"} 200 + frek_id shape id-XXXXXXXXXXXX-XXXX
- POST /api/v1/moment/sign minimal body 200
- POST /api/v1/identity/authenticate/begin 200 (challenge)
- GET /api/v1/spec/ 200

No new endpoints must have been created by Universe.jsx.
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break

BASE_URL = BASE_URL.rstrip("/")

FREK_ID_RE = re.compile(r"^id-[A-Za-z0-9]{12}-[A-Za-z0-9]{4}$")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
class TestHealth:
    def test_health_deep(self, api):
        r = api.get(f"{BASE_URL}/api/v1/health/deep", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, dict)


# ---------- Stats (used by Universe pulse) ----------
class TestStats:
    def test_moment_stats(self, api):
        r = api.get(f"{BASE_URL}/api/v1/moment/stats", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # Must expose at least a counter for moments
        assert isinstance(data, dict)

    def test_fk_stats(self, api):
        r = api.get(f"{BASE_URL}/api/v1/fk/stats", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, dict)


# ---------- Identity Engine (Universe orchestrates these) ----------
class TestIdentityInit:
    def test_init_individual_returns_valid_frek_id(self, api):
        payload = {"identity_type": "individual"}
        r = api.post(f"{BASE_URL}/api/v1/identity/init", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "frek_id" in data, data
        frek_id = data["frek_id"]
        assert FREK_ID_RE.match(frek_id), f"frek_id shape mismatch: {frek_id}"

    def test_init_institution_returns_valid_frek_id(self, api):
        # Universe profile "Institution" or "Organisation" sends identity_type=institution
        payload = {"identity_type": "institution", "session_id": "TEST_universe_sess_inst"}
        r = api.post(f"{BASE_URL}/api/v1/identity/init", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        assert FREK_ID_RE.match(r.json()["frek_id"])

    def test_init_professional_returns_valid_frek_id(self, api):
        payload = {"identity_type": "professional", "session_id": "TEST_universe_sess_pro"}
        r = api.post(f"{BASE_URL}/api/v1/identity/init", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        assert FREK_ID_RE.match(r.json()["frek_id"])


class TestAuthenticateBegin:
    def test_authenticate_begin_returns_challenge(self, api):
        r = api.post(f"{BASE_URL}/api/v1/identity/authenticate/begin", json={}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # Must expose a challenge for the browser to solve
        assert "challenge" in data or "publicKey" in data or "options" in data, data


# ---------- Moment sign — non-regression ----------
class TestMomentSign:
    def test_moment_sign_minimal(self, api):
        # Minimal JSON body — must remain 200 (regression contract from previous iteration)
        payload = {
            "session_id": "TEST_universe_sess_moment",
            "signature": "TEST universe non-regression sign",
        }
        r = api.post(f"{BASE_URL}/api/v1/moment/sign", json=payload, timeout=20)
        # Some implementations may accept empty body — either 200 or 422 is OK per liberal contract,
        # but the review states "200 must be preserved"
        assert r.status_code == 200, f"expected 200, got {r.status_code} — {r.text[:400]}"


# ---------- Spec ----------
class TestSpec:
    def test_spec_root(self, api):
        r = api.get(f"{BASE_URL}/api/v1/spec/", timeout=15)
        assert r.status_code == 200, r.text
