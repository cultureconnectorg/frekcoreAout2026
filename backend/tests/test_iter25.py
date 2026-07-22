"""Iteration 25 regression tests:
- /identity/init and /identity/{id}/register/begin
- /moment/sign
- /fk/create with keep=true
- /fk/{id}/download with and without ?compat=zip
- /fk/verify
"""
import io
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://culture-chain.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api/v1"


@pytest.fixture(scope="module")
def created_fk_id():
    """Create a FK with keep=true and return its frek_id."""
    files = {'files': ('note.txt', b'hello iter25', 'text/plain')}
    data = {
        'title': 'TEST_iter25_FK',
        'object_type': 'song',
        'primary_creator_name': 'TEST_creator',
        'description': 'iter25 regression',
        'keep': 'true',
        'return_json': 'true',
    }
    r = requests.post(f"{API}/fk/create", data=data, files=files, timeout=45)
    assert r.status_code == 200, f"fk/create failed {r.status_code} {r.text[:200]}"
    payload = r.json()
    frek_id = payload["info"]["frek_id"]
    assert frek_id
    assert payload["info"].get("kept") is True, "kept flag should be true"
    return frek_id


# ---- Identity ----
class TestIdentity:
    def test_identity_init(self):
        r = requests.post(f"{API}/identity/init", json={"session_id": None, "identity_type": "individual"}, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert "frek_id" in data
        assert isinstance(data["frek_id"], str) and len(data["frek_id"]) > 4

    def test_identity_register_begin(self):
        # init identity first
        r_init = requests.post(f"{API}/identity/init", json={"identity_type": "individual"}, timeout=15)
        assert r_init.status_code == 200
        frek_id = r_init.json()["frek_id"]

        r = requests.post(f"{API}/identity/{frek_id}/register/begin", json={}, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        # PublicKeyCredentialCreationOptions
        assert "challenge" in data
        assert "rp" in data or "rpId" in data or "user" in data


# ---- Moment sign ----
class TestMomentSign:
    def test_moment_sign(self):
        payload = {
            'title': 'TEST_iter25_moment',
            'context': 'iter25 regression',
            'session_id': uuid.uuid4().hex,
        }
        r = requests.post(f"{API}/moment/sign", json=payload, timeout=45)
        assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
        data = r.json()
        assert "frek_id" in data


# ---- FK create + download compat ----
class TestFK:
    def test_fk_create_and_download_default(self, created_fk_id):
        r = requests.get(f"{API}/fk/{created_fk_id}/download", timeout=30)
        assert r.status_code == 200, r.text[:200]
        assert r.headers.get("content-type") == "application/vnd.frek.culture+zip"
        cd = r.headers.get("content-disposition", "")
        assert ".fk" in cd and ".fk.zip" not in cd, f"expected .fk but got {cd}"

    def test_fk_download_compat_zip(self, created_fk_id):
        r = requests.get(f"{API}/fk/{created_fk_id}/download", params={"compat": "zip"}, timeout=30)
        assert r.status_code == 200, r.text[:200]
        assert r.headers.get("content-type") == "application/zip", r.headers
        cd = r.headers.get("content-disposition", "")
        assert ".fk.zip" in cd, f"expected .fk.zip in Content-Disposition, got {cd}"

    def test_fk_download_unknown_id(self):
        r = requests.get(f"{API}/fk/FREK-DOES-NOT-EXIST-XYZ/download", timeout=15)
        assert r.status_code == 404

    def test_fk_verify_roundtrip(self, created_fk_id):
        dl = requests.get(f"{API}/fk/{created_fk_id}/download", timeout=30)
        assert dl.status_code == 200
        fk_bytes = dl.content
        assert len(fk_bytes) > 0

        files = {'file': ('roundtrip.fk', fk_bytes, 'application/vnd.frek.culture+zip')}
        r = requests.post(f"{API}/fk/verify", files=files, timeout=30)
        assert r.status_code == 200, r.text[:200]
        report = r.json()
        assert report.get("valid") is True, f"verify report invalid: {report.get('summary')}"

    def test_fk_detail_available(self, created_fk_id):
        r = requests.get(f"{API}/fk/detail/{created_fk_id}", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["frek_id"] == created_fk_id
        assert d.get("kept") is True
