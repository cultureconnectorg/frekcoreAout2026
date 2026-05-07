"""FREK Certified Seal — tests endpoints embeddable."""
import os
import re

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"


class TestSealEndpoints:
    def test_seal_js_served(self):
        r = requests.get(f"{API}/seal.js", timeout=5)
        assert r.status_code == 200
        assert "javascript" in r.headers.get("content-type", "")
        assert r.headers.get("Cache-Control", "").startswith("public")
        # CORS ouvert pour partenaires
        assert r.headers.get("Access-Control-Allow-Origin") == "*"

    def test_seal_js_has_public_key_injected(self):
        """La cle publique doit etre injectee a la place du placeholder."""
        r = requests.get(f"{API}/seal.js", timeout=5)
        body = r.text
        assert "%%FREK_PUBLIC_KEY_B64%%" not in body, "placeholder non remplace"
        # Extrait la valeur injectee
        m = re.search(r'FREK_PUB_B64\s*=\s*"([^"]+)"', body)
        assert m, "FREK_PUB_B64 introuvable dans seal.js"
        injected = m.group(1)
        # Doit correspondre a /passport/key
        key_resp = requests.get(f"{API}/passport/key", timeout=5).json()
        assert injected == key_resp["public_key_raw_b64"]

    def test_seal_js_logic_present(self):
        """Le script doit contenir les helpers crypto et le rendu SVG."""
        r = requests.get(f"{API}/seal.js", timeout=5)
        body = r.text
        for marker in ["Ed25519", "merkle_root", "data-frek-id", "<svg", "FREKCORE", "CERTIFIED"]:
            assert marker in body, f"marker manquant: {marker}"

    def test_seal_demo_served(self):
        r = requests.get(f"{API}/seal/demo", timeout=5)
        assert r.status_code == 200
        assert "html" in r.headers.get("content-type", "")
        assert "FREK Certified Seal" in r.text
