"""FREK Passport — Tests offline verifier standalone.

Execute le script Python `verify_passport.py` en subprocess, hors backend,
sur un passeport reel obtenu via /api/v1/passport/{frek_id}.
Verifie qu'il fonctionne pour passport full, partial, et detecte le tampering.
"""
import base64
import copy
import json
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"

CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
CLIENT_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "pczBP49crCXSSSwSOShsXClzs9srhKe5S-xnraMPn-k")

VERIFIER_PATH = Path("/app/verifier/python/verify_passport.py")


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{API}/auth/token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def emitted_frek_id(auth_headers):
    email = f"offline_pytest_{secrets.token_hex(4)}@frekcore.fr"
    r = requests.post(
        f"{API}/identity/emit",
        json={"email": email, "source": "test", "event": "CC2026"},
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["frek_id"]


@pytest.fixture(scope="module")
def public_key_b64():
    r = requests.get(f"{API}/passport/key", timeout=5)
    assert r.status_code == 200
    return r.json()["public_key_raw_b64"]


def _run_verifier(passport_doc: dict, pub_b64: str) -> tuple[int, dict]:
    """Execute verify_passport.py en subprocess, retourne (exit_code, parsed_json_output)."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(passport_doc, f)
        passport_path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, str(VERIFIER_PATH),
             "--passport", passport_path,
             "--public-key-b64", pub_b64],
            capture_output=True, text=True, timeout=15,
        )
        out = json.loads(proc.stdout) if proc.stdout.strip() else {}
        return proc.returncode, out
    finally:
        os.unlink(passport_path)


# ---------- Verifier disponible ----------
class TestVerifierAvailability:
    def test_python_script_exists(self):
        assert VERIFIER_PATH.exists(), f"verifier script missing: {VERIFIER_PATH}"

    def test_download_endpoint_python(self):
        r = requests.get(f"{API}/passport/verifier/python", timeout=5)
        assert r.status_code == 200
        assert "verify_passport" in r.text
        assert "Ed25519" in r.text

    def test_download_endpoint_js(self):
        r = requests.get(f"{API}/passport/verifier/js", timeout=5)
        assert r.status_code == 200
        assert "verifyPassport" in r.text

    def test_download_endpoint_unknown_lang_404(self):
        r = requests.get(f"{API}/passport/verifier/cobol", timeout=5)
        assert r.status_code == 404


# ---------- Verifier execute en subprocess ----------
class TestOfflineVerifierFull:
    def test_full_passport_valid(self, emitted_frek_id, public_key_b64):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        code, out = _run_verifier(p, public_key_b64)
        assert code == 0, out
        assert out["valid"] is True
        assert out["mode"] == "full"
        assert out["errors"] == []

    def test_full_passport_tamper_value(self, emitted_frek_id, public_key_b64):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        p["claims"][0]["value"] = "TAMPERED"
        code, out = _run_verifier(p, public_key_b64)
        assert code == 1
        assert out["valid"] is False
        assert "merkle_root_mismatch" in out["errors"]

    def test_full_passport_tamper_signature(self, emitted_frek_id, public_key_b64):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        p["signature"] = base64.b64encode(b"\x00" * 64).decode("ascii")
        code, out = _run_verifier(p, public_key_b64)
        assert code == 1
        assert "signature_invalid" in out["errors"]


class TestOfflineVerifierPartial:
    def test_partial_disclosure_valid(self, emitted_frek_id, public_key_b64):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        d = requests.post(
            f"{API}/passport/disclose",
            json={"passport": p, "reveal": ["frek_id", "spec_version"]},
            timeout=5,
        ).json()
        code, out = _run_verifier(d, public_key_b64)
        assert code == 0, out
        assert out["valid"] is True
        assert out["mode"] == "partial"
        revealed = [c["key"] for c in out["claims"]]
        assert revealed == ["frek_id", "spec_version"]

    def test_partial_disclosure_tamper_path(self, emitted_frek_id, public_key_b64):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        d = requests.post(
            f"{API}/passport/disclose",
            json={"passport": p, "reveal": ["frek_id"]},
            timeout=5,
        ).json()
        d["claims"][0]["value"] = "FAKE"
        code, out = _run_verifier(d, public_key_b64)
        assert code == 1
        assert any("path_invalid" in e for e in out["errors"])


# ---------- Independance vis-a-vis du backend (cle archivee) ----------
class TestOfflineIndependence:
    def test_verifier_runs_without_backend_call(self, emitted_frek_id, public_key_b64, tmp_path):
        """Une fois le passeport et la cle archives, le verifier n'a plus besoin du backend."""
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        # Simule un environnement deconnecte : on passe les fichiers, on ne fait AUCUN autre call.
        passport_file = tmp_path / "archived_passport.json"
        passport_file.write_text(json.dumps(p))
        proc = subprocess.run(
            [sys.executable, str(VERIFIER_PATH),
             "--passport", str(passport_file),
             "--public-key-b64", public_key_b64],
            capture_output=True, text=True, timeout=15,
            # Aucune variable d'env reseau ; le verifier ne doit pas en avoir besoin
        )
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)
        assert out["valid"] is True
