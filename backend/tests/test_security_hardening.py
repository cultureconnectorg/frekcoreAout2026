"""
FREK Security Hardening — Phase 2.5
Tests:
  - Rate-limit silencieux (429 sans Retry-After)
  - Idempotence emit ne consomme pas le quota
  - Anomaly trail (security_events) sur rate-limit hit
  - Brute-force lockout PIN staff (5 fails / 15 min)
  - Lockouts admin endpoints
  - Manual unlock
  - Admin endpoints protégés (403 missing X-Admin-Key)
  - Spec ouverture sectorielle (domains + security_policies)
  - Token revocation après rotate
"""
import os
import secrets
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient

# Phase 2 (reports/10_TEST_INFRASTRUCTURE.md): these paths used to be hardcoded
# to /app/{backend,frontend}/.env, which only exists inside the original
# Emergent container layout (Dockerfile: WORKDIR /app/backend). Resolving
# relative to this file's location makes collection portable across any
# checkout path (local sandbox, CI runner, ...) while still finding the same
# files when the repo genuinely is mounted at /app.
REPO_ROOT = Path(__file__).resolve().parents[2]

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Fallback read frontend .env
    frontend_env = REPO_ROOT / "frontend" / ".env"
    if frontend_env.exists():
        for line in frontend_env.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.strip().split("=", 1)[1]
                break
BASE_URL = (BASE_URL or "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"

# Read backend env
def _env(key):
    backend_env = REPO_ROOT / "backend" / ".env"
    if not backend_env.exists():
        # No .env in this checkout (e.g. CI without secrets provisioned) —
        # degrade to None rather than crashing collection. Tests that need
        # this value will fail explicitly at call time with a clear reason,
        # never silently pass.
        return None
    for line in backend_env.read_text().splitlines():
        if line.startswith(f"{key}="):
            v = line.strip().split("=", 1)[1]
            # strip surrounding quotes
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                v = v[1:-1]
            return v
    return None

ADMIN_KEY = _env("SECRET_KEY")
KILTI_ID = _env("FREK_CLIENT_KILTIKONET_ID") or "kiltikonet-cc2026"
KILTI_SECRET = _env("FREK_CLIENT_KILTIKONET_SECRET")
MONGO_URL = _env("MONGO_URL")
DB_NAME = _env("DB_NAME") or "test_database"


@pytest.fixture(scope="module")
def mongo():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture(scope="module")
def admin_headers():
    return {"X-Admin-Key": ADMIN_KEY, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def temp_client(admin_headers):
    """Crée un client de test isolé pour rate-limit (pas de pollution kiltikonet)."""
    cid = f"TEST_sec_{secrets.token_hex(4)}"
    r = requests.post(
        f"{API}/admin/clients",
        json={
            "client_id": cid,
            "name": "TEST Security",
            "permissions": ["emit", "stage", "stats"],
            "event": "TEST_SEC",
        },
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code in (200, 201), f"create client failed: {r.status_code} {r.text}"
    csec = r.json()["client_secret"]
    # Get token
    tr = requests.post(
        f"{API}/auth/token",
        json={"client_id": cid, "client_secret": csec, "grant_type": "client_credentials"},
        timeout=10,
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    yield {"client_id": cid, "client_secret": csec, "token": token}
    # Cleanup
    requests.delete(f"{API}/admin/clients/{cid}", headers=admin_headers, timeout=10)


# ---------- Rate-limit ----------
class TestRateLimit:
    def test_emit_silent_429_when_quota_exceeded(self, temp_client, mongo):
        """Pré-remplir 100 entries dans rate_limits, puis emit doit 429 silencieux."""
        cid = temp_client["client_id"]
        # Purge any prior entries for this scope
        mongo.rate_limits.delete_many({"scope": cid, "action": "identity_emit"})
        mongo.security_events.delete_many({"scope": cid, "kind": "rate_limit_hit"})

        now = datetime.now(timezone.utc)
        docs = [{"scope": cid, "action": "identity_emit", "ts": now.isoformat()} for _ in range(100)]
        mongo.rate_limits.insert_many(docs)

        # Now POST emit -> expect 429
        headers = {"Authorization": f"Bearer {temp_client['token']}", "Content-Type": "application/json"}
        r = requests.post(
            f"{API}/identity/emit",
            json={"email": f"TEST_ratelimit_{secrets.token_hex(4)}@test.io", "source": "test", "event": "TEST_SEC"},
            headers=headers,
            timeout=10,
        )
        assert r.status_code == 429, f"expected 429 got {r.status_code} body={r.text}"
        # Silent: no Retry-After header
        assert "retry-after" not in {k.lower() for k in r.headers.keys()}, f"Retry-After leaked: {r.headers}"
        body = r.json()
        # Detail must be the generic message, no leak
        assert body.get("detail") == "Trop de requetes", body

    def test_anomaly_recorded_on_rate_limit(self, temp_client, mongo):
        """security_events doit avoir un doc kind=rate_limit_hit, severity=warning."""
        cid = temp_client["client_id"]
        # Wait briefly for write
        time.sleep(0.3)
        ev = mongo.security_events.find_one(
            {"scope": cid, "kind": "rate_limit_hit", "severity": "warning"},
            sort=[("created_at", -1)],
        )
        assert ev is not None, "rate_limit_hit anomaly not recorded"
        assert ev["details"]["action"] == "identity_emit"
        assert ev["details"]["count"] >= ev["details"]["limit"]

    def test_idempotent_emit_does_not_consume_quota(self, admin_headers, mongo):
        """Une emission idempotente (email déjà existant) NE DOIT PAS consommer le quota."""
        # Use a fresh client to isolate
        cid = f"TEST_idem_{secrets.token_hex(4)}"
        r = requests.post(
            f"{API}/admin/clients",
            json={"client_id": cid, "name": "TEST Idem",
                  "permissions": ["emit"], "event": "TEST_SEC"},
            headers=admin_headers, timeout=10,
        )
        assert r.status_code in (200, 201)
        csec = r.json()["client_secret"]
        tok = requests.post(f"{API}/auth/token",
            json={"client_id": cid, "client_secret": csec, "grant_type": "client_credentials"},
            timeout=10).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
        email = f"TEST_idem_{secrets.token_hex(4)}@test.io"
        # First emit - creates
        r1 = requests.post(f"{API}/identity/emit",
            json={"email": email, "source": "test", "event": "TEST_SEC"}, headers=h, timeout=10)
        assert r1.status_code == 200, r1.text
        # Pré-remplir 100 entries pour atteindre la limite
        now = datetime.now(timezone.utc).isoformat()
        mongo.rate_limits.insert_many(
            [{"scope": cid, "action": "identity_emit", "ts": now} for _ in range(100)]
        )
        # Re-emit même email — idempotent, devrait passer SANS hit rate-limit
        r2 = requests.post(f"{API}/identity/emit",
            json={"email": email, "source": "test", "event": "TEST_SEC"}, headers=h, timeout=10)
        assert r2.status_code == 200, f"idempotent emit blocked by rate-limit: {r2.status_code} {r2.text}"
        assert r2.json()["created"] is False
        # Cleanup
        requests.delete(f"{API}/admin/clients/{cid}", headers=admin_headers, timeout=10)


# ---------- Brute-force lockout ----------
class TestStaffLockout:
    AGENT = "EMISSION-01"
    PIN_OK = "1111"
    PIN_BAD = "0000"

    @pytest.fixture(autouse=True)
    def _reset_account(self, mongo, admin_headers):
        # Pre-clean lockout state
        mongo.staff.update_one(
            {"agent_id": self.AGENT},
            {"$set": {"failed_attempts": 0, "locked_until": None}},
        )
        mongo.security_events.delete_many({"scope": self.AGENT, "kind": "staff_lockout"})
        yield
        # Post-clean
        mongo.staff.update_one(
            {"agent_id": self.AGENT},
            {"$set": {"failed_attempts": 0, "locked_until": None}},
        )

    def test_5_bad_pin_locks_account(self, mongo):
        for i in range(5):
            r = requests.post(f"{API}/staff/login",
                json={"agent_id": self.AGENT, "pin": self.PIN_BAD}, timeout=10)
            assert r.status_code == 401, f"attempt {i+1}: {r.status_code} {r.text}"
            assert r.json().get("detail") == "Agent ou PIN invalide"

        # 6e tentative — toujours 401 (pas de leak "verrouillé")
        r6 = requests.post(f"{API}/staff/login",
            json={"agent_id": self.AGENT, "pin": self.PIN_BAD}, timeout=10)
        assert r6.status_code == 401
        assert r6.json().get("detail") == "Agent ou PIN invalide"

        # PIN correct doit aussi être rejeté pendant le lockout
        rok = requests.post(f"{API}/staff/login",
            json={"agent_id": self.AGENT, "pin": self.PIN_OK}, timeout=10)
        assert rok.status_code == 401, f"correct PIN should still 401 during lockout: {rok.status_code}"
        assert rok.json().get("detail") == "Agent ou PIN invalide"

        # DB state
        s = mongo.staff.find_one({"agent_id": self.AGENT})
        assert s["failed_attempts"] >= 5
        assert s.get("locked_until")
        lu = datetime.fromisoformat(s["locked_until"].replace("Z", "+00:00"))
        if lu.tzinfo is None:
            lu = lu.replace(tzinfo=timezone.utc)
        delta = lu - datetime.now(timezone.utc)
        assert timedelta(minutes=10) < delta < timedelta(minutes=20), f"locked_until ~+15min, got {delta}"

    def test_lockout_listed_in_admin(self, admin_headers, mongo):
        # Trigger lockout
        for _ in range(5):
            requests.post(f"{API}/staff/login",
                json={"agent_id": self.AGENT, "pin": self.PIN_BAD}, timeout=10)
        time.sleep(0.2)
        r = requests.get(f"{API}/admin/security/lockouts", headers=admin_headers, timeout=10)
        assert r.status_code == 200, r.text
        data = r.json()
        ids = [x["agent_id"] for x in data["lockouts"]]
        assert self.AGENT in ids, f"lockout not listed: {data}"
        agent = next(x for x in data["lockouts"] if x["agent_id"] == self.AGENT)
        assert agent["failed_attempts"] >= 5

    def test_anomaly_trail_staff_lockout(self, admin_headers):
        for _ in range(5):
            requests.post(f"{API}/staff/login",
                json={"agent_id": self.AGENT, "pin": self.PIN_BAD}, timeout=10)
        time.sleep(0.3)
        r = requests.get(f"{API}/admin/security/events",
            params={"severity": "warning", "scope": self.AGENT, "kind": "staff_lockout"},
            headers=admin_headers, timeout=10)
        assert r.status_code == 200, r.text
        events = r.json()["events"]
        assert len(events) >= 1, f"no staff_lockout event: {events}"
        ev = events[0]
        assert ev["scope"] == self.AGENT
        assert ev["severity"] == "warning"
        assert ev["details"]["failed_attempts"] >= 5

    def test_manual_unlock_restores_login(self, admin_headers):
        # Lock first
        for _ in range(5):
            requests.post(f"{API}/staff/login",
                json={"agent_id": self.AGENT, "pin": self.PIN_BAD}, timeout=10)
        # Verify locked
        rok = requests.post(f"{API}/staff/login",
            json={"agent_id": self.AGENT, "pin": self.PIN_OK}, timeout=10)
        assert rok.status_code == 401

        # Unlock
        r = requests.post(f"{API}/admin/security/staff/{self.AGENT}/unlock",
            headers=admin_headers, timeout=10)
        assert r.status_code == 200, r.text
        assert r.json()["unlocked"] is True

        # PIN correct doit maintenant marcher
        ok = requests.post(f"{API}/staff/login",
            json={"agent_id": self.AGENT, "pin": self.PIN_OK}, timeout=10)
        assert ok.status_code == 200, f"login after unlock failed: {ok.status_code} {ok.text}"
        assert "access_token" in ok.json()


# ---------- Admin endpoints protected ----------
class TestAdminAuthGuard:
    def test_events_no_admin_key_403(self):
        r = requests.get(f"{API}/admin/security/events", timeout=10)
        # FastAPI Header(None) + manual check -> should be 403
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "Cle admin invalide ou manquante"

    def test_lockouts_no_admin_key_403(self):
        r = requests.get(f"{API}/admin/security/lockouts", timeout=10)
        assert r.status_code == 403
        assert r.json()["detail"] == "Cle admin invalide ou manquante"

    def test_unlock_no_admin_key_403(self):
        r = requests.post(f"{API}/admin/security/staff/EMISSION-01/unlock", timeout=10)
        assert r.status_code == 403
        assert r.json()["detail"] == "Cle admin invalide ou manquante"

    def test_wrong_admin_key_403(self):
        r = requests.get(f"{API}/admin/security/events",
            headers={"X-Admin-Key": "wrong"}, timeout=10)
        assert r.status_code == 403


# ---------- Token revocation after rotate ----------
class TestRotateRevokesToken:
    def test_token_issued_before_rotate_is_revoked(self, admin_headers):
        cid = f"TEST_rot_{secrets.token_hex(4)}"
        r = requests.post(f"{API}/admin/clients",
            json={"client_id": cid, "name": "TEST Rotate",
                  "permissions": ["emit", "stats"], "event": "TEST_SEC"},
            headers=admin_headers, timeout=10)
        assert r.status_code in (200, 201)
        csec = r.json()["client_secret"]
        # Get token BEFORE rotate
        tok = requests.post(f"{API}/auth/token",
            json={"client_id": cid, "client_secret": csec, "grant_type": "client_credentials"},
            timeout=10).json()["access_token"]

        # Sanity: token works (call /stats/{client_id} which uses require_permission stats)
        h = {"Authorization": f"Bearer {tok}"}
        s = requests.get(f"{API}/stats/{cid}", headers=h, timeout=10)
        assert s.status_code == 200, f"token before rotate should work: {s.status_code} {s.text}"

        # Rotate
        rot = requests.post(f"{API}/admin/clients/{cid}/rotate",
            headers=admin_headers, timeout=10)
        assert rot.status_code == 200, rot.text

        # Same token should be revoked
        s2 = requests.get(f"{API}/stats/{cid}", headers=h, timeout=10)
        assert s2.status_code == 401, f"token after rotate should be revoked: {s2.status_code} {s2.text}"
        assert s2.json().get("detail") == "Token revoque"

        # Cleanup
        requests.delete(f"{API}/admin/clients/{cid}", headers=admin_headers, timeout=10)


# ---------- Spec ouverture sectorielle ----------
class TestSpecExtension:
    def test_spec_version_unchanged(self):
        r = requests.get(f"{API}/spec/v1.0.0", timeout=10)
        assert r.status_code == 200
        spec = r.json()
        assert spec["spec_version"] == "1.0.0"

    def test_spec_has_domains_section(self):
        spec = requests.get(f"{API}/spec/v1.0.0", timeout=10).json()
        d = spec.get("domains")
        assert d is not None, "domains section missing"
        supported = d.get("supported", {})
        for sector in ["culture", "education", "health", "justice", "finance",
                       "telecom", "media", "phygital", "tech", "identity"]:
            assert sector in supported, f"sector {sector} missing"
        assert "extension_model" in d
        assert "sector_examples" in d
        assert isinstance(d["sector_examples"], dict)
        assert len(d["sector_examples"]) >= 3

    def test_spec_has_security_policies_section(self):
        spec = requests.get(f"{API}/spec/v1.0.0", timeout=10).json()
        sec = spec.get("security_policies")
        assert sec is not None
        for k in ["rate_limiting", "brute_force_lockout", "anomaly_trail", "secret_rotation"]:
            assert k in sec, f"security_policies.{k} missing"
        # Check rate_limiting has expected defaults
        assert "identity_emit" in sec["rate_limiting"]["defaults"]
        # brute_force_lockout
        assert sec["brute_force_lockout"]["duration_minutes"] == 15

    def test_spec_no_anomaly_leak_in_public_endpoints(self):
        # Public endpoints must NOT leak security_events
        # /spec/ index doesn't expose events
        r = requests.get(f"{API}/spec/", timeout=10)
        assert r.status_code == 200
        body = r.text.lower()
        assert "rate_limit_hit" not in body
        assert "staff_lockout" not in body
