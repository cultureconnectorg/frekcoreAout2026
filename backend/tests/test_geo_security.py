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
import sys
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/geo"

ADMIN_KEY = os.environ.get("SECRET_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def H_admin():
    return {"X-Admin-Key": ADMIN_KEY}


def H_holder(token):
    return {"X-FREK-Session": token}


def fresh_frek():
    return f"FREK-GEO-{secrets.token_hex(3).upper()}"


@pytest.fixture()
def holder_session():
    from identity_engine import service as identity_service

    r = requests.post(
        f"{BASE_URL}/api/v1/identity/init",
        json={"identity_type": "individual"},
        timeout=5,
    )
    assert r.status_code == 200, r.text
    frek_id = r.json()["frek_id"]
    token = identity_service.issue_session_token(frek_id)
    return frek_id, token


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


# ---------- P1: real per-holder authorization ----------
# docs/architecture/FREK_ID_RECONCILIATION.md #3 / reports/FREKCORE_COMPLETION_BACKLOG.md
# P1 #3 — mirrors test_fingerprint.py::TestHolderAuth for geo's own three
# widened routes (consent write, trail read, notarize).
class TestHolderAuth:
    def test_consent_write_with_own_holder_session_works(self, holder_session):
        frek_id, token = holder_session
        r = requests.post(
            f"{API}/consent/{frek_id}",
            json={"level": "city"},
            headers=H_holder(token),
            timeout=5,
        )
        assert r.status_code == 200, r.text

    def test_consent_write_with_holder_session_for_a_different_frek_id_is_rejected(
        self, holder_session
    ):
        _frek_id, token = holder_session
        r = requests.post(
            f"{API}/consent/{fresh_frek()}",
            json={"level": "city"},
            headers=H_holder(token),
            timeout=5,
        )
        assert r.status_code == 403

    def test_consent_write_via_linked_object_works(self, holder_session):
        _frek_id, token = holder_session
        external_id = fresh_frek()
        link = requests.post(
            f"{BASE_URL}/api/v1/identity/link-object",
            json={"object_id": external_id},
            headers=H_holder(token),
            timeout=5,
        )
        assert link.status_code == 200, link.text
        r = requests.post(
            f"{API}/consent/{external_id}",
            json={"level": "city"},
            headers=H_holder(token),
            timeout=5,
        )
        assert r.status_code == 200, r.text

    def test_trail_with_own_holder_session_works(self, holder_session):
        frek_id, token = holder_session
        requests.post(
            f"{API}/consent/{frek_id}",
            json={"level": "city"},
            headers=H_holder(token),
            timeout=5,
        )
        requests.post(
            f"{API}/observe",
            json={"frek_id": frek_id, "lat": 5.35, "lon": -4.02, "skip_reverse": True},
            timeout=5,
        )
        r = requests.get(f"{API}/trail/{frek_id}", headers=H_holder(token), timeout=5)
        assert r.status_code == 200, r.text

    def test_notarize_with_own_holder_session_works(self, holder_session):
        """Unlike fingerprint's /match, /notarize is single-subject — a
        holder self-attesting their own presence is coherent, so this
        route (unlike /match) WAS widened — see geo/routes.py's
        geo_notarize() docstring."""
        frek_id, token = holder_session
        requests.post(
            f"{API}/consent/{frek_id}",
            json={"level": "precise"},
            headers=H_holder(token),
            timeout=5,
        )
        r = requests.post(
            f"{API}/notarize",
            json={"frek_id": frek_id, "lat": 5.35, "lon": -4.02},
            headers=H_holder(token),
            timeout=5,
        )
        assert r.status_code == 200, r.text


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
