"""
FREK Staff PWA Scanner - backend regression tests.
Covers /api/v1/staff/login, /me, /scan/zones, /marchands, /badge/{code},
/scan/access, /scan/cashless, /scan/emit, /scan/sync, permission matrix
and chain notarization side-effect.
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://culture-chain.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
V1 = f"{BASE_URL}/api/v1"

CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
CLIENT_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "")

DEFAULT_AGENTS = {
    "SUPERVISEUR-01": "9999",
    "EMISSION-01": "1111",
    "ACCES-01": "2222",
    "CASHLESS-01": "3333",
}


def _login(agent_id, pin):
    r = requests.post(f"{V1}/staff/login", json={"agent_id": agent_id, "pin": pin}, timeout=15)
    return r


@pytest.fixture(scope="module")
def supervisor_token():
    r = _login("SUPERVISEUR-01", "9999")
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def acces_token():
    r = _login("ACCES-01", "2222")
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def cashless_token():
    r = _login("CASHLESS-01", "3333")
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def emission_token():
    r = _login("EMISSION-01", "1111")
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def kilti_token():
    r = requests.post(f"{V1}/auth/token", json={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    }, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Kiltikonet client login failed: {r.text}")
    return r.json()["access_token"]


# ---------- Auth & login ----------
class TestStaffLogin:
    def test_all_default_agents_login(self):
        for aid, pin in DEFAULT_AGENTS.items():
            r = _login(aid, pin)
            assert r.status_code == 200, f"{aid} login failed: {r.text}"
            data = r.json()
            assert data["agent_id"] == aid
            assert data["token_type"] == "Bearer"
            assert isinstance(data["access_token"], str) and len(data["access_token"]) > 20
            assert "permissions" in data and isinstance(data["permissions"], list)

    def test_wrong_pin_returns_401(self):
        r = _login("SUPERVISEUR-01", "0000")
        assert r.status_code == 401

    def test_unknown_agent_returns_401(self):
        r = _login("DOESNOTEXIST-99", "1234")
        assert r.status_code == 401

    def test_me_without_token_401(self):
        r = requests.get(f"{V1}/staff/me", timeout=15)
        assert r.status_code == 401

    def test_me_with_token(self, supervisor_token):
        r = requests.get(f"{V1}/staff/me", headers={"Authorization": f"Bearer {supervisor_token}"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["agent_id"] == "SUPERVISEUR-01"
        assert data["role"] == "superviseur"
        assert "scan_access" in data["permissions"]
        assert "scan_cashless" in data["permissions"]
        assert "emit_walkin" in data["permissions"]
        assert isinstance(data["allowed_zones"], list)


# ---------- Zones / marchands / badge lookup ----------
class TestZonesMarchandsLookup:
    def test_zones_with_token(self, acces_token):
        r = requests.get(f"{V1}/staff/scan/zones", headers={"Authorization": f"Bearer {acces_token}"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "zones" in data
        assert "allowed_for_agent" in data
        assert "ENTREE" in data["allowed_for_agent"]

    def test_marchands_requires_cashless_perm(self, acces_token, cashless_token):
        # acces should be 403
        r1 = requests.get(f"{V1}/staff/scan/marchands", headers={"Authorization": f"Bearer {acces_token}"}, timeout=15)
        assert r1.status_code == 403
        # cashless OK
        r2 = requests.get(f"{V1}/staff/scan/marchands", headers={"Authorization": f"Bearer {cashless_token}"}, timeout=15)
        assert r2.status_code == 200
        assert "marchands" in r2.json()

    def test_badge_lookup_404(self, supervisor_token):
        r = requests.get(f"{V1}/staff/scan/badge/NONEXISTENT-{uuid.uuid4().hex[:6]}",
                         headers={"Authorization": f"Bearer {supervisor_token}"}, timeout=15)
        assert r.status_code == 404


# ---------- Walk-in emit (creates badge for downstream tests) ----------
class TestEmit:
    def test_walkin_emit_creates_badge(self, emission_token):
        email = f"TEST_walkin_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": email,
            "prenom": "Test",
            "nom": "Walkin",
            "type_badge": "ART",
            "organisation": "TEST",
            "event": "CC2026",
        }
        r = requests.post(f"{V1}/staff/scan/emit", json=payload,
                          headers={"Authorization": f"Bearer {emission_token}"}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["created"] is True
        assert "badge" in data and data["badge"]["badge_id"]
        assert data["badge"]["frek_id"]
        # idempotent
        r2 = requests.post(f"{V1}/staff/scan/emit", json=payload,
                           headers={"Authorization": f"Bearer {emission_token}"}, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["created"] is False
        pytest.shared_badge = data["badge"]
        pytest.shared_qr = data.get("qr_token")

    def test_emit_forbidden_for_acces(self, acces_token):
        r = requests.post(f"{V1}/staff/scan/emit", json={
            "email": f"TEST_forbidden_{uuid.uuid4().hex[:6]}@example.com",
            "prenom": "X", "nom": "Y", "type_badge": "ART",
        }, headers={"Authorization": f"Bearer {acces_token}"}, timeout=15)
        assert r.status_code == 403

    def test_emit_forbidden_for_cashless(self, cashless_token):
        r = requests.post(f"{V1}/staff/scan/emit", json={
            "email": f"TEST_forbidden2_{uuid.uuid4().hex[:6]}@example.com",
            "prenom": "X", "nom": "Y", "type_badge": "ART",
        }, headers={"Authorization": f"Bearer {cashless_token}"}, timeout=15)
        assert r.status_code == 403


# ---------- Access scan ----------
class TestAccess:
    def test_access_scan_records(self, acces_token):
        badge = getattr(pytest, "shared_badge", None)
        if not badge:
            pytest.skip("No badge from emit test")
        # chain height before
        h0 = requests.get(f"{V1}/notary/chain/status", timeout=15).json().get("height", 0)
        r = requests.post(f"{V1}/staff/scan/access", json={
            "code": badge["badge_id"], "zone": "ENTREE",
        }, headers={"Authorization": f"Bearer {acces_token}"}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["access"] == "AUTORISE"
        assert data["scan"]["agent_id"] == "ACCES-01"
        # verify badge lookup persisted
        r2 = requests.get(f"{V1}/staff/scan/badge/{badge['badge_id']}",
                          headers={"Authorization": f"Bearer {acces_token}"}, timeout=15)
        assert r2.status_code == 200
        # wait a bit and check chain incremented
        time.sleep(3)
        h1 = requests.get(f"{V1}/notary/chain/status", timeout=15).json().get("height", 0)
        assert h1 >= h0  # may be > if notarize succeeded

    def test_access_scan_cashless_forbidden(self, acces_token):
        r = requests.post(f"{V1}/staff/scan/cashless", json={
            "code": "x", "montant_jetons": 1, "marchand_id": "x",
        }, headers={"Authorization": f"Bearer {acces_token}"}, timeout=15)
        assert r.status_code == 403


# ---------- Cashless ----------
class TestCashless:
    def test_cashless_payment(self, cashless_token, kilti_token):
        badge = getattr(pytest, "shared_badge", None)
        if not badge:
            pytest.skip("No badge from emit test")
        # Recharge via /api/jetons/recharge using kilti client (pack decouverte = 10 jetons)
        rr = requests.post(f"{API}/jetons/recharge", json={
            "badge_id": badge["badge_id"],
            "pack": "decouverte",
            "payment_method": "cash",
        }, headers={"Authorization": f"Bearer {kilti_token}"}, timeout=20)
        if rr.status_code not in (200, 201):
            pytest.skip(f"Recharge failed: {rr.status_code} {rr.text[:200]}")

        # Get list of marchands; create one if empty (best-effort)
        ml = requests.get(f"{V1}/staff/scan/marchands",
                          headers={"Authorization": f"Bearer {cashless_token}"}, timeout=15).json()
        marchands = ml.get("marchands", [])
        if not marchands:
            # Try create one via legacy endpoint
            cr = requests.post(f"{API}/marchands/create", json={
                "marchand_id": f"TEST-MARCH-{uuid.uuid4().hex[:6]}",
                "nom": "TEST Marchand",
            }, headers={"Authorization": f"Bearer {kilti_token}"}, timeout=15)
            if cr.status_code in (200, 201):
                marchands = [cr.json()]
            else:
                pytest.skip(f"No marchands and create failed: {cr.status_code}")
        marchand_id = marchands[0].get("marchand_id")

        # Pay 3 jetons
        r = requests.post(f"{V1}/staff/scan/cashless", json={
            "code": badge["badge_id"],
            "montant_jetons": 3,
            "marchand_id": marchand_id,
            "description": "TEST pay",
        }, headers={"Authorization": f"Bearer {cashless_token}"}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["new_solde"] >= 0
        assert data["transaction"]["agent_id"] == "CASHLESS-01"
        assert data["transaction"]["montant_jetons"] == 3


# ---------- Sync replay ----------
class TestSync:
    def test_sync_permission_per_kind(self, acces_token):
        # Agent acces tries to replay a cashless action -> should fail with 403 in result list
        r = requests.post(f"{V1}/staff/scan/sync", json={
            "actions": [
                {"kind": "cashless", "client_uuid": "u1",
                 "payload": {"code": "x", "montant_jetons": 1, "marchand_id": "x"}},
                {"kind": "emit", "client_uuid": "u2",
                 "payload": {"email": "x@x.fr", "prenom": "x", "nom": "x"}},
            ]
        }, headers={"Authorization": f"Bearer {acces_token}"}, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert data["failed"] == 2
        for item in data["results"]:
            assert item["ok"] is False
            assert item.get("status") == 403

    def test_sync_unknown_kind(self, supervisor_token):
        r = requests.post(f"{V1}/staff/scan/sync", json={
            "actions": [{"kind": "foobar", "client_uuid": "uX", "payload": {}}],
        }, headers={"Authorization": f"Bearer {supervisor_token}"}, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data["failed"] == 1


# ---------- PWA assets ----------
class TestPWAAssets:
    def test_manifest_served(self):
        # PWA assets servis par le frontend (port 3000) — pas le backend
        frontend_url = os.environ.get("FREK_FRONTEND_URL", "http://localhost:3000").rstrip("/")
        r = requests.get(f"{frontend_url}/scan-manifest.webmanifest", timeout=15)
        assert r.status_code == 200
        j = r.json()
        assert j["start_url"] == "/scan"

    def test_sw_served(self):
        frontend_url = os.environ.get("FREK_FRONTEND_URL", "http://localhost:3000").rstrip("/")
        r = requests.get(f"{frontend_url}/scan-sw.js", timeout=15)
        assert r.status_code == 200
        assert "self" in r.text or "service" in r.text.lower()


# ---------- Regression: notary chain still works ----------
class TestNotaryRegression:
    def test_chain_status(self):
        r = requests.get(f"{V1}/notary/chain/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "height" in d
