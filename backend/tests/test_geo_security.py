"""FREK Geo — P0 security regression (docs/decisions/0001-founder-decisions-2026-08-31.md).

Before this fix, every mutating /api/geo/* route (consent write, observe,
notarize) and the sensitive /trail/{frek_id} read were reachable with no
credential at all. No test file previously covered this module at all.
Proves: unauthorized calls are now rejected, legitimate (admin-keyed) calls
still work, and public-by-design routes (encode, heatmap, satellite) remain
reachable without a credential.
"""

import os
import secrets

import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/geo"

ADMIN_KEY = os.environ.get("SECRET_KEY", "")


def H_admin():
    return {"X-Admin-Key": ADMIN_KEY}


def fresh_frek():
    return f"FREK-GEO-{secrets.token_hex(3).upper()}"


class TestConsentWriteAuth:
    def test_without_admin_key_is_rejected(self):
        fid = fresh_frek()
        r = requests.post(f"{API}/consent/{fid}", json={"level": "city"}, timeout=5)
        assert r.status_code == 403
        after = requests.get(f"{API}/consent/{fid}", timeout=5).json()
        assert after.get("level", "none") == "none"

    def test_with_admin_key_still_works(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/consent/{fid}", json={"level": "city"}, headers=H_admin(), timeout=5
        )
        assert r.status_code == 200
        after = requests.get(f"{API}/consent/{fid}", timeout=5).json()
        assert after["level"] == "city"


class TestObserveConsentGate:
    def test_observe_without_consent_is_refused(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/observe",
            json={"frek_id": fid, "lat": 5.35, "lon": -4.02, "skip_reverse": True},
            timeout=5,
        ).json()
        assert r.get("recorded") is False
        assert r.get("reason") == "consent_required"

    def test_observe_records_when_consented_no_credential_needed(self):
        """Device-originated route — deliberately left reachable without a
        credential (would break the real reporting-device flow); consent is
        the real gate here, not auth."""
        fid = fresh_frek()
        requests.post(
            f"{API}/consent/{fid}", json={"level": "city"}, headers=H_admin(), timeout=5
        )
        r = requests.post(
            f"{API}/observe",
            json={"frek_id": fid, "lat": 5.35, "lon": -4.02, "skip_reverse": True},
            timeout=5,
        )
        assert r.status_code == 200
        assert r.json().get("recorded") is not False


class TestTrailReadAuth:
    def test_trail_without_admin_key_is_rejected(self):
        fid = fresh_frek()
        r = requests.get(f"{API}/trail/{fid}", timeout=5)
        assert r.status_code == 403

    def test_trail_with_admin_key_works(self):
        fid = fresh_frek()
        requests.post(
            f"{API}/consent/{fid}", json={"level": "city"}, headers=H_admin(), timeout=5
        )
        requests.post(
            f"{API}/observe",
            json={"frek_id": fid, "lat": 5.35, "lon": -4.02, "skip_reverse": True},
            timeout=5,
        )
        r = requests.get(f"{API}/trail/{fid}", headers=H_admin(), timeout=5)
        assert r.status_code == 200


class TestNotarizeAuth:
    def test_notarize_without_admin_key_is_rejected(self):
        fid = fresh_frek()
        r = requests.post(
            f"{API}/notarize",
            json={"frek_id": fid, "lat": 5.35, "lon": -4.02},
            timeout=5,
        )
        assert r.status_code == 403


class TestPublicByDesignRoutesUnaffected:
    """encode/heatmap/satellite are stateless or already-anonymous; the P0
    fix must not have accidentally locked these down too."""

    def test_encode_remains_public(self):
        r = requests.post(f"{API}/encode", json={"lat": 5.35, "lon": -4.02}, timeout=5)
        assert r.status_code == 200

    def test_heatmap_remains_public(self):
        r = requests.get(f"{API}/heatmap", timeout=5)
        assert r.status_code == 200

    def test_satellite_sources_remains_public(self):
        r = requests.get(f"{API}/satellite/sources", timeout=5)
        assert r.status_code == 200
