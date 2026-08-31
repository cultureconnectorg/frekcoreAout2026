"""Identity Engine lifecycle (P1: revoke/update/archive) — regression tests.

docs/architecture/FREK_ID_RECONCILIATION.md scoped these as
holder-initiated-by-default with an admin-key override, not a copy of
frek_v1's client-initiated revoke. This file proves: unauthorized calls are
rejected, admin-key calls work, idempotency holds, revoke is immutable
(update refused after), and register/begin's ownership fix (found while
building this) still lets a fresh anonymous identity claim its first
Passkey without a session.

Full end-to-end coverage of register/begin's "adding a SECOND credential
requires the holder's session" branch needs a real WebAuthn ceremony to get
an identity into a credentialed state first — this suite, like the existing
test_identity_engine.py, does not simulate one (no virtual authenticator
available here). That specific branch is verified by direct code review
instead (backend/identity_engine/routes.py's register_begin/complete),
recorded here rather than silently left untested with no explanation.
"""
import os

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1/identity"

ADMIN_KEY = os.environ.get("SECRET_KEY", "")


def H_admin():
    return {"X-Admin-Key": ADMIN_KEY}


@pytest.fixture()
def fresh_identity():
    r = requests.post(f"{API}/init", json={"identity_type": "individual"}, timeout=5)
    assert r.status_code == 200, r.text
    return r.json()


class TestRevoke:
    def test_revoke_without_credential_is_rejected(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.post(f"{API}/{fid}/revocation", json={}, timeout=5)
        assert r.status_code == 403

    def test_revoke_with_wrong_admin_key_is_rejected(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.post(
            f"{API}/{fid}/revocation",
            json={},
            headers={"X-Admin-Key": "not-the-real-key"},
            timeout=5,
        )
        assert r.status_code == 403

    def test_revoke_with_admin_key_works_and_is_idempotent(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r1 = requests.post(f"{API}/{fid}/revocation", json={"reason": "test"}, headers=H_admin(), timeout=5)
        assert r1.status_code == 200, r1.text
        assert r1.json()["status"] == "revoked"

        # Public view reflects the new status
        pub = requests.get(f"{API}/{fid}", timeout=5).json()
        assert pub["status"] == "revoked"

        # Second revoke is idempotent, not an error
        r2 = requests.post(f"{API}/{fid}/revocation", json={}, headers=H_admin(), timeout=5)
        assert r2.status_code == 200
        assert "Deja revoque" in r2.json()["message"]

    def test_revoke_is_immutable_update_refused_after(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        requests.post(f"{API}/{fid}/revocation", json={}, headers=H_admin(), timeout=5)
        r = requests.patch(
            f"{API}/{fid}", json={"display_name": "new name"}, headers=H_admin(), timeout=5
        )
        assert r.status_code == 409

    def test_revoke_unknown_frek_id_returns_404(self):
        r = requests.post(f"{API}/id-000000000000-0000/revocation", json={}, headers=H_admin(), timeout=5)
        assert r.status_code == 404


class TestUpdate:
    def test_update_without_credential_is_rejected(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.patch(f"{API}/{fid}", json={"display_name": "x"}, timeout=5)
        assert r.status_code == 403

    def test_update_display_name_with_admin_key(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.patch(
            f"{API}/{fid}", json={"display_name": "Laurentia"}, headers=H_admin(), timeout=5
        )
        assert r.status_code == 200, r.text
        assert r.json()["display_name"] == "Laurentia"

    def test_update_metadata_with_admin_key(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.patch(
            f"{API}/{fid}", json={"metadata": {"locale": "fr"}}, headers=H_admin(), timeout=5
        )
        assert r.status_code == 200, r.text

    def test_update_empty_body_is_a_no_op(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.patch(f"{API}/{fid}", json={}, headers=H_admin(), timeout=5)
        assert r.status_code == 200


class TestArchive:
    def test_archive_without_credential_is_rejected(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.post(f"{API}/{fid}/archive", json={}, timeout=5)
        assert r.status_code == 403

    def test_archive_with_admin_key_works_and_is_idempotent(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r1 = requests.post(f"{API}/{fid}/archive", json={"reason": "unused"}, headers=H_admin(), timeout=5)
        assert r1.status_code == 200, r1.text
        assert r1.json()["status"] == "archived"

        pub = requests.get(f"{API}/{fid}", timeout=5).json()
        assert pub["status"] == "archived"

        r2 = requests.post(f"{API}/{fid}/archive", json={}, headers=H_admin(), timeout=5)
        assert r2.status_code == 200
        assert "Deja archivee" in r2.json()["message"]

    def test_archive_after_revoke_is_refused(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        requests.post(f"{API}/{fid}/revocation", json={}, headers=H_admin(), timeout=5)
        r = requests.post(f"{API}/{fid}/archive", json={}, headers=H_admin(), timeout=5)
        assert r.status_code == 409


class TestRegisterBeginStillBootstraps:
    """The ownership fix must not have broken claiming a brand-new,
    zero-credential identity — that is register/begin's real bootstrap
    purpose and must stay open."""

    def test_fresh_anonymous_identity_can_still_start_registration(self, fresh_identity):
        fid = fresh_identity["frek_id"]
        r = requests.post(f"{API}/{fid}/register/begin", json={}, timeout=5)
        assert r.status_code == 200, r.text
        assert "challenge" in r.json()
