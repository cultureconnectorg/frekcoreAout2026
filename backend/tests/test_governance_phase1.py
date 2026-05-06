"""
Tests Phase 1 Governance:
- A.1 Revocation immutable (POST /identity/{id}/revoke + idempotence + chaine intacte)
- A.2 Renouvellement / expiration (renew + expires_at + scan blocked)
- E.4 Audit trail humain (per FREK-ID public, per agent auth, per event auth+stats)
- Status enrichi (revoked/expires_at/expired)
- Regression: chain integrity, FREK Notary previous tests, scan flows
"""
import os
import time
import uuid
import requests
import pytest
from datetime import datetime, timezone, timedelta

def _read_env(path, key):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL")
).rstrip("/")
API = f"{BASE_URL}/api"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def env_creds():
    creds = {}
    with open("/app/backend/.env") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                creds[k] = v.strip().strip('"').strip("'")
    return creds


@pytest.fixture(scope="module")
def client_token(env_creds):
    cid = env_creds.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
    csec = env_creds.get("FREK_CLIENT_KILTIKONET_SECRET", "")
    r = requests.post(
        f"{API}/v1/auth/token",
        json={"client_id": cid, "client_secret": csec, "grant_type": "client_credentials"},
        timeout=15,
    )
    assert r.status_code == 200, f"Auth client failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def client_headers(client_token):
    return {"Authorization": f"Bearer {client_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def staff_token():
    r = requests.post(
        f"{API}/v1/staff/login",
        json={"agent_id": "SUPERVISEUR-01", "pin": "9999"},
        timeout=15,
    )
    assert r.status_code == 200, f"Staff login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def staff_headers(staff_token):
    return {"Authorization": f"Bearer {staff_token}", "Content-Type": "application/json"}


def _emit_identity(client_headers, email=None, expires_at=None, event="CC2026"):
    payload = {
        "email": email or f"TEST_{uuid.uuid4().hex[:10]}@frek-test.com",
        "source": "api-test",
        "event": event,
    }
    if expires_at:
        payload["expires_at"] = expires_at
    r = requests.post(f"{API}/v1/identity/emit", json=payload, headers=client_headers, timeout=15)
    assert r.status_code == 200, f"emit failed: {r.text}"
    return r.json()["frek_id"]


# ---------- A.1 Revocation ----------
class TestRevocation:
    def test_revoke_no_auth_returns_401(self, client_headers):
        frek_id = _emit_identity(client_headers)
        r = requests.post(f"{API}/v1/identity/{frek_id}/revoke", json={"reason": "no auth"}, timeout=15)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_revoke_unknown_frek_id_returns_404(self, client_headers):
        r = requests.post(
            f"{API}/v1/identity/unknown-id-xyz-9999/revoke",
            json={"reason": "ghost"},
            headers=client_headers,
            timeout=15,
        )
        assert r.status_code == 404

    def test_revoke_success_then_idempotent(self, client_headers):
        frek_id = _emit_identity(client_headers)

        # First revoke
        r = requests.post(
            f"{API}/v1/identity/{frek_id}/revoke",
            json={"reason": "Test audit revocation"},
            headers=client_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["revoked"] is True
        assert data["frek_id"] == frek_id
        assert data.get("revoked_at")

        # Second revoke = idempotent
        r2 = requests.post(
            f"{API}/v1/identity/{frek_id}/revoke",
            json={"reason": "again"},
            headers=client_headers,
            timeout=15,
        )
        assert r2.status_code == 200
        assert r2.json().get("message", "").lower().startswith("deja revoque")

        # Status enriched
        s = requests.get(f"{API}/v1/identity/{frek_id}/status", timeout=15)
        assert s.status_code == 200
        sdata = s.json()
        assert sdata["revoked"] is True
        assert sdata["revoke_reason"] == "Test audit revocation"
        assert sdata.get("revoked_at")

    def test_chain_integrity_after_revoke(self, client_headers):
        frek_id = _emit_identity(client_headers)
        requests.post(
            f"{API}/v1/identity/{frek_id}/revoke",
            json={"reason": "chain integrity test"},
            headers=client_headers,
            timeout=15,
        )
        r = requests.get(f"{API}/v1/notary/chain/verify", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("valid") is True, f"Chain invalid after revoke: {data}"


# ---------- A.2 Renewal & Expiration ----------
class TestRenewalExpiration:
    def test_renew_updates_expires_at(self, client_headers):
        frek_id = _emit_identity(client_headers)
        new_exp = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        r = requests.post(
            f"{API}/v1/identity/{frek_id}/renew",
            json={"expires_at": new_exp, "reason": "Annual renewal"},
            headers=client_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["expires_at"] == new_exp

        s = requests.get(f"{API}/v1/identity/{frek_id}/status", timeout=15).json()
        assert s["expires_at"] == new_exp
        assert s["expired"] is False

    def test_renew_blocked_on_revoked(self, client_headers):
        frek_id = _emit_identity(client_headers)
        requests.post(
            f"{API}/v1/identity/{frek_id}/revoke",
            json={"reason": "block renew"},
            headers=client_headers,
            timeout=15,
        )
        new_exp = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        r = requests.post(
            f"{API}/v1/identity/{frek_id}/renew",
            json={"expires_at": new_exp, "reason": "should fail"},
            headers=client_headers,
            timeout=15,
        )
        assert r.status_code == 400
        assert "revoqu" in r.json().get("detail", "").lower()

    def test_emit_with_expires_at_in_past_marks_expired(self, client_headers):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        frek_id = _emit_identity(client_headers, expires_at=past)
        s = requests.get(f"{API}/v1/identity/{frek_id}/status", timeout=15).json()
        assert s["expired"] is True
        assert s["expires_at"] == past

    def test_emit_with_future_expires_at_not_expired(self, client_headers):
        future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        frek_id = _emit_identity(client_headers, expires_at=future)
        s = requests.get(f"{API}/v1/identity/{frek_id}/status", timeout=15).json()
        assert s["expired"] is False


# ---------- Scan integration: revoked + expired blocked ----------
class TestScanBlocked:
    def _create_badge(self, client_headers, email=None):
        """Create a badge — returns (badge_doc, frek_id, qr_token) or (None,...) if endpoint unavailable."""
        payload = {
            "type_badge": "ART",
            "event": "CC2026",
            "prenom": "Test",
            "nom": "Govern",
            "email": email or f"TEST_govern_{uuid.uuid4().hex[:8]}@x.io",
            "organisation": None,
        }
        r = requests.post(f"{API}/badges/create", json=payload, headers=client_headers, timeout=15)
        if r.status_code not in (200, 201):
            return None, None, None, r
        data = r.json()
        badge = data.get("badge") or data
        return badge, badge.get("frek_id"), badge.get("qr_token"), r

    def _set_expires_at_in_db(self, frek_id, iso_value):
        """Patch via renew endpoint cannot put past date in spec, so we use an admin approach: emit fresh with past."""
        return None

    def test_scan_blocked_on_revoked_frek(self, client_headers, staff_headers):
        badge, frek_id, qr, r = self._create_badge(client_headers)
        if not badge:
            pytest.skip(f"badge create unavailable: {r.status_code} {r.text[:200]}")

        # Revoke
        rv = requests.post(
            f"{API}/v1/identity/{frek_id}/revoke",
            json={"reason": "scan block test"},
            headers=client_headers,
            timeout=15,
        )
        assert rv.status_code == 200, rv.text

        # Scan -> 403 with FREK-ID revoque
        sc = requests.post(
            f"{API}/v1/staff/scan/access",
            json={"code": qr, "zone": "ENTREE"},
            headers=staff_headers,
            timeout=15,
        )
        assert sc.status_code == 403, f"expected 403 got {sc.status_code} {sc.text}"
        assert "revoqu" in sc.json().get("detail", "").lower()

    def test_scan_blocked_on_expired_frek(self, client_headers, staff_headers):
        # Create badge (which creates its own FREK-ID without expires_at)
        badge, frek_id, qr, r = self._create_badge(client_headers)
        if not badge:
            pytest.skip(f"badge create unavailable")

        # Use a separate emit to set expires_at=past on a NEW identity, then attach via badge later is complex.
        # Simpler: directly patch frek_identities via admin API if exists, else skip.
        # We try the renew endpoint with past date (server doesn't validate future-only).
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        renew = requests.post(
            f"{API}/v1/identity/{frek_id}/renew",
            json={"expires_at": past, "reason": "force expire for test"},
            headers=client_headers,
            timeout=15,
        )
        if renew.status_code != 200:
            pytest.skip(f"cannot force-expire via renew: {renew.status_code}")

        sc = requests.post(
            f"{API}/v1/staff/scan/access",
            json={"code": qr, "zone": "ENTREE"},
            headers=staff_headers,
            timeout=15,
        )
        assert sc.status_code == 403, f"expected 403 got {sc.status_code} {sc.text}"
        assert "expir" in sc.json().get("detail", "").lower()


# ---------- E.4 Audit ----------
class TestAuditTrail:
    def test_audit_per_frek_public_no_auth(self, client_headers):
        frek_id = _emit_identity(client_headers)
        # No auth header
        r = requests.get(f"{API}/v1/audit/{frek_id}", timeout=15)
        assert r.status_code == 200, r.text
        events = r.json()
        assert isinstance(events, list)
        assert len(events) >= 1
        kinds = {e["kind"] for e in events}
        # Should have identity_emit + at least 1 stage event
        assert "identity_emit" in kinds or "stage" in kinds

    def test_audit_per_frek_includes_revocation(self, client_headers):
        frek_id = _emit_identity(client_headers)
        requests.post(
            f"{API}/v1/identity/{frek_id}/revoke",
            json={"reason": "audit revocation"},
            headers=client_headers,
            timeout=15,
        )
        # tiny wait for notary block insertion (sync inside notarize_event)
        time.sleep(0.3)
        r = requests.get(f"{API}/v1/audit/{frek_id}", timeout=15)
        assert r.status_code == 200
        events = r.json()
        kinds = [e["kind"] for e in events]
        assert "revocation" in kinds, f"revocation missing in {kinds}"
        rev_event = next(e for e in events if e["kind"] == "revocation")
        assert "audit revocation" in rev_event["label"].lower()

    def test_audit_per_frek_unknown_returns_404(self):
        r = requests.get(f"{API}/v1/audit/does-not-exist-9999", timeout=15)
        assert r.status_code == 404

    def test_audit_per_frek_does_not_leak_email(self, client_headers):
        email = f"TEST_leak_{uuid.uuid4().hex[:6]}@frek-test.com"
        frek_id = _emit_identity(client_headers, email=email)
        r = requests.get(f"{API}/v1/audit/{frek_id}", timeout=15)
        assert r.status_code == 200
        body = r.text.lower()
        assert email.lower() not in body, "raw email leaked in audit response"

    def test_audit_per_frek_sorted_asc(self, client_headers):
        frek_id = _emit_identity(client_headers)
        requests.post(
            f"{API}/v1/identity/{frek_id}/revoke",
            json={"reason": "sort test"},
            headers=client_headers,
            timeout=15,
        )
        time.sleep(0.3)
        r = requests.get(f"{API}/v1/audit/{frek_id}", timeout=15)
        events = r.json()
        ts = [e.get("timestamp") or "" for e in events]
        assert ts == sorted(ts), f"events not sorted asc: {ts}"

    def test_audit_per_agent_requires_auth(self):
        r = requests.get(f"{API}/v1/audit/agent/SUPERVISEUR-01/actions", timeout=15)
        assert r.status_code in (401, 403)

    def test_audit_per_agent_with_auth(self, client_headers):
        r = requests.get(
            f"{API}/v1/audit/agent/SUPERVISEUR-01/actions",
            headers=client_headers,
            timeout=15,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_audit_per_event_requires_stats_perm(self, client_headers):
        r = requests.get(f"{API}/v1/audit/event/CC2026/recent", headers=client_headers, timeout=15)
        # kiltikonet has stats perm -> 200
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- Pre-existing test FREK-IDs from agent context ----------
class TestPreSeededIdentities:
    def test_revoked_frek_status(self):
        """40c297d5-79e9-4a8e-a177-efea1b07c204 is REVOKED per agent context."""
        r = requests.get(
            f"{API}/v1/identity/40c297d5-79e9-4a8e-a177-efea1b07c204/status",
            timeout=15,
        )
        if r.status_code == 404:
            pytest.skip("Pre-seeded revoked FREK-ID not present in this DB")
        assert r.status_code == 200
        d = r.json()
        assert d["revoked"] is True
        assert d.get("revoke_reason")

    def test_revoked_frek_audit_public(self):
        r = requests.get(
            f"{API}/v1/audit/40c297d5-79e9-4a8e-a177-efea1b07c204",
            timeout=15,
        )
        if r.status_code == 404:
            pytest.skip("Pre-seeded revoked FREK-ID not present")
        assert r.status_code == 200
        kinds = {e["kind"] for e in r.json()}
        assert "revocation" in kinds

    def test_notary_frek_audit(self):
        r = requests.get(
            f"{API}/v1/audit/8ffe44d0-ce5e-4211-8dc0-bfc0ddf1ad0a",
            timeout=15,
        )
        if r.status_code == 404:
            pytest.skip("Pre-seeded notary FREK-ID not present")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- Regression: previous endpoints ----------
class TestRegression:
    def test_chain_verify_still_valid(self):
        r = requests.get(f"{API}/v1/notary/chain/verify", timeout=30)
        assert r.status_code == 200
        assert r.json().get("valid") is True

    def test_staff_login_still_works(self):
        r = requests.post(
            f"{API}/v1/staff/login",
            json={"agent_id": "ACCES-01", "pin": "2222"},
            timeout=15,
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_token_endpoint_still_works(self, env_creds):
        r = requests.post(
            f"{API}/v1/auth/token",
            json={
                "client_id": env_creds.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026"),
                "client_secret": env_creds.get("FREK_CLIENT_KILTIKONET_SECRET", ""),
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        assert r.status_code == 200
