"""FREK Passport — Phase 3 souverainete porteur.

Tests :
 - Cle publique Ed25519 exposee
 - Construction d'un passeport complet signe
 - Verification full
 - Disclosure selective + verification partial
 - Tampering : signature, valeur, claim_count, racine merkle
 - Verification offline (sans backend) avec la cle publique
"""
import base64
import copy
import os
import secrets

import pytest
import requests

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"

CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
CLIENT_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "")


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
    email = f"passport_pytest_{secrets.token_hex(4)}@frekcore.fr"
    r = requests.post(
        f"{API}/identity/emit",
        json={"email": email, "source": "test", "event": "CC2026"},
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["frek_id"]


# ---------- Cle publique ----------
class TestPublicKey:
    def test_key_endpoint(self):
        r = requests.get(f"{API}/passport/key", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert d["algorithm"] == "Ed25519"
        assert d["key_id"] == "frek-passport-v1"
        assert "BEGIN PUBLIC KEY" in d["public_key_pem"]
        assert len(base64.b64decode(d["public_key_raw_b64"])) == 32  # Ed25519 = 32 bytes


# ---------- Passeport complet ----------
class TestFullPassport:
    def test_export_full(self, emitted_frek_id):
        r = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5)
        assert r.status_code == 200
        p = r.json()
        env = p["envelope"]
        assert env["frek_id"] == emitted_frek_id
        assert env["spec_version"] == "1.0.0"
        assert env["passport_version"] == 1
        assert env["claims_count"] == len(p["claims"]) == 12
        assert p["disclosure"] == "full"
        # Each claim has key/value/nonce
        for c in p["claims"]:
            assert "key" in c and "nonce" in c

    def test_export_unknown_returns_404(self):
        r = requests.get(f"{API}/passport/unknown-frek-id", timeout=5)
        assert r.status_code == 404

    def test_verify_full_valid(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        v = requests.post(f"{API}/passport/verify", json={"document": p}, timeout=5).json()
        assert v["valid"] is True
        assert v["mode"] == "full"
        assert v["errors"] == []

    def test_each_call_produces_fresh_passport(self, emitted_frek_id):
        """Nonces frais => signature differente, mais meme contenu certifie."""
        p1 = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        p2 = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        assert p1["signature"] != p2["signature"]
        assert p1["envelope"]["merkle_root"] != p2["envelope"]["merkle_root"]
        # Mais les valeurs metiers (frek_id, stage, etc.) sont identiques
        v1 = {c["key"]: c["value"] for c in p1["claims"]}
        v2 = {c["key"]: c["value"] for c in p2["claims"]}
        for k in ["frek_id", "current_stage", "event_id", "spec_version", "revoked"]:
            assert v1[k] == v2[k]


# ---------- Disclosure selective ----------
class TestSelectiveDisclosure:
    def test_disclose_subset(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        d = requests.post(
            f"{API}/passport/disclose",
            json={"passport": p, "reveal": ["frek_id", "current_stage", "spec_version"]},
            timeout=5,
        ).json()
        assert d["disclosure"] == "partial"
        keys = [c["key"] for c in d["claims"]]
        assert keys == ["frek_id", "current_stage", "spec_version"]
        for c in d["claims"]:
            assert "merkle_path" in c

    def test_verify_partial_valid(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        d = requests.post(
            f"{API}/passport/disclose",
            json={"passport": p, "reveal": ["frek_id"]},
            timeout=5,
        ).json()
        v = requests.post(f"{API}/passport/verify", json={"document": d}, timeout=5).json()
        assert v["valid"] is True
        assert v["mode"] == "partial"
        # Seul le claim revele apparait dans le resultat
        revealed_keys = [c["key"] for c in v["claims"]]
        assert revealed_keys == ["frek_id"]

    def test_disclose_unknown_claim_400(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        r = requests.post(
            f"{API}/passport/disclose",
            json={"passport": p, "reveal": ["claim_inexistant"]},
            timeout=5,
        )
        assert r.status_code == 400


# ---------- Tampering ----------
class TestTampering:
    def test_tamper_signature(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        p["signature"] = base64.b64encode(b"\x00" * 64).decode("ascii")
        v = requests.post(f"{API}/passport/verify", json={"document": p}, timeout=5).json()
        assert v["valid"] is False
        assert "signature_invalid" in v["errors"]

    def test_tamper_claim_value_full(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        p["claims"][0]["value"] = "FAKE_VALUE"
        v = requests.post(f"{API}/passport/verify", json={"document": p}, timeout=5).json()
        assert v["valid"] is False
        assert "merkle_root_mismatch" in v["errors"]

    def test_tamper_claim_value_partial(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        d = requests.post(
            f"{API}/passport/disclose",
            json={"passport": p, "reveal": ["frek_id", "current_stage"]},
            timeout=5,
        ).json()
        d["claims"][0]["value"] = "FAKE_FREK"
        v = requests.post(f"{API}/passport/verify", json={"document": d}, timeout=5).json()
        assert v["valid"] is False
        assert any("path_invalid" in e for e in v["errors"])

    def test_tamper_envelope_invalidates_signature(self, emitted_frek_id):
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()
        p["envelope"]["frek_id"] = "tampered-frek-id"
        v = requests.post(f"{API}/passport/verify", json={"document": p}, timeout=5).json()
        assert v["valid"] is False
        assert "signature_invalid" in v["errors"]


# ---------- Verification offline avec cle publique uniquement ----------
class TestOfflineVerification:
    def test_offline_verify_with_public_key(self, emitted_frek_id):
        """Reproduit ce qu'un verificateur tiers ferait : cle publique + lib cryptographique."""
        # 1. Recupere la cle publique une fois pour toute
        pub_b64 = requests.get(f"{API}/passport/key", timeout=5).json()["public_key_raw_b64"]
        pub_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))

        # 2. Recupere un passeport
        p = requests.get(f"{API}/passport/{emitted_frek_id}", timeout=5).json()

        # 3. Verifie la signature OFFLINE (pas d'appel reseau au backend)
        import hashlib
        import json as j

        envelope_canon = j.dumps(p["envelope"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        sig = base64.b64decode(p["signature"])
        try:
            pub_key.verify(sig, envelope_canon)
            sig_ok = True
        except InvalidSignature:
            sig_ok = False
        assert sig_ok is True

        # 4. Recompute merkle root OFFLINE
        def leaf(c):
            payload = j.dumps({"key": c["key"], "nonce": c["nonce"], "value": c["value"]},
                              sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            return hashlib.sha256(payload).hexdigest()

        leaves = [leaf(c) for c in p["claims"]]
        # Build root
        cur = leaves
        while len(cur) > 1:
            nxt = []
            for i in range(0, len(cur), 2):
                l = cur[i]
                r = cur[i + 1] if i + 1 < len(cur) else cur[i]
                nxt.append(hashlib.sha256(bytes.fromhex(l) + bytes.fromhex(r)).hexdigest())
            cur = nxt
        assert cur[0] == p["envelope"]["merkle_root"]
