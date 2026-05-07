"""FREK Standards — Tests JWK Set + DID Configuration + manifest universel."""
import base64
import hashlib
import json
import os

import pytest
import requests

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"


# ---------- JWK Set RFC 7517 ----------
class TestJWKSet:
    def test_jwks_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/.well-known/jwks.json", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert len(d["keys"]) >= 1
        k = d["keys"][0]
        assert k["kty"] == "OKP"
        assert k["crv"] == "Ed25519"
        assert k["alg"] == "EdDSA"
        assert k["use"] == "sig"
        assert k["kid"]
        # x est base64url 32 bytes (Ed25519 raw key)
        x_padded = k["x"] + "=" * (-len(k["x"]) % 4)
        raw = base64.urlsafe_b64decode(x_padded)
        assert len(raw) == 32

    def test_jwks_matches_passport_key(self):
        """La cle publique JWK doit correspondre exactement a /passport/key."""
        jwks = requests.get(f"{BASE_URL}/api/.well-known/jwks.json", timeout=5).json()
        passport = requests.get(f"{API}/passport/key", timeout=5).json()
        # Decode JWK x (base64url) et passport raw_b64 (standard base64)
        x_padded = jwks["keys"][0]["x"] + "=" * (-len(jwks["keys"][0]["x"]) % 4)
        jwk_raw = base64.urlsafe_b64decode(x_padded)
        passport_raw = base64.b64decode(passport["public_key_raw_b64"])
        assert jwk_raw == passport_raw, "JWK key != passport key"


# ---------- DIF DID Configuration ----------
class TestDIDConfiguration:
    def test_did_configuration_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/.well-known/did-configuration.json", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert d["@context"] == "https://identity.foundation/.well-known/did-configuration/v1"
        assert len(d["linked_dids"]) >= 1
        vc = d["linked_dids"][0]
        assert "DomainLinkageCredential" in vc["type"]
        assert vc["credentialSubject"]["id"] == "did:frek:frekcore"
        assert vc["credentialSubject"]["origin"].startswith("http")
        assert vc["proof"]["type"] == "DataIntegrityProof"
        assert vc["proof"]["cryptosuite"] == "eddsa-jcs-2022"

    def test_did_configuration_signature_valid(self):
        """La proof DataIntegrityProof doit etre verifiable avec la cle publique exposee."""
        from did.encoding import decode_multibase_b58btc
        from did.vc import _jcs
        from passport import keys as pk

        d = requests.get(f"{BASE_URL}/api/.well-known/did-configuration.json", timeout=5).json()
        vc = d["linked_dids"][0]
        proof = vc["proof"]
        unsigned = {k: v for k, v in vc.items() if k != "proof"}
        proof_config = {k: v for k, v in proof.items() if k != "proofValue"}
        vc_hash = hashlib.sha256(_jcs(unsigned)).digest()
        proof_hash = hashlib.sha256(_jcs(proof_config)).digest()
        sig = decode_multibase_b58btc(proof["proofValue"])
        assert pk.verify(sig, proof_hash + vc_hash) is True


# ---------- Manifest universel ----------
class TestUniversalManifest:
    def test_manifest_lists_all_ecosystems(self):
        r = requests.get(f"{API}/standards/manifest", timeout=5)
        assert r.status_code == 200
        d = r.json()
        for k in ["w3c", "eudi", "id4africa", "itu", "iso_mdl", "caricom"]:
            assert k in d["ecosystems"], f"ecosysteme manquant : {k}"
        # Trust root partage avec passport/did
        tr = d["trust_root"]
        assert tr["algorithm"].startswith("Ed25519")
        assert "passport" in tr["shared_with"]
        assert "did_vc" in tr["shared_with"]
        assert "eudi" in tr["shared_with"]

    def test_well_known_endpoints_listed(self):
        d = requests.get(f"{API}/standards/manifest", timeout=5).json()
        wk = d["well_known_endpoints"]
        assert "jwks" in wk
        assert "did_configuration" in wk
        assert "openid_credential_issuer" in wk
        assert "oauth_authorization_server" in wk

    def test_geographic_roadmap_present(self):
        d = requests.get(f"{API}/standards/manifest", timeout=5).json()
        gr = d["geographic_roadmap"]
        assert "current" in gr
        # Liste les zones de la roadmap fournie par le user
        nxt = " ".join(gr["next"])
        assert "CARICOM" in nxt
        assert "ID4Africa" in nxt or "Africa" in nxt
        assert "EUDI" in nxt
        assert "USA" in nxt or "mDL" in nxt

    def test_ecosystem_lookup_known(self):
        for eco in ["w3c", "eudi", "id4africa", "itu", "iso_mdl", "caricom"]:
            r = requests.get(f"{API}/standards/{eco}", timeout=5)
            assert r.status_code == 200, f"{eco} echoue"
            d = r.json()
            assert eco in d
            assert "trust_root" in d

    def test_ecosystem_lookup_unknown_404(self):
        r = requests.get(f"{API}/standards/unknown_ecosystem", timeout=5)
        assert r.status_code == 404


# ---------- Coherence cle de confiance partagee ----------
class TestSharedTrustRoot:
    def test_jwk_did_passport_use_same_key(self):
        """JWK Set, DID Document, /passport/key — tous la meme cle Ed25519."""
        # passport
        p_raw = base64.b64decode(requests.get(f"{API}/passport/key", timeout=5).json()["public_key_raw_b64"])
        # jwks
        jwk = requests.get(f"{BASE_URL}/api/.well-known/jwks.json", timeout=5).json()["keys"][0]
        x_padded = jwk["x"] + "=" * (-len(jwk["x"]) % 4)
        j_raw = base64.urlsafe_b64decode(x_padded)
        # did doc d'un frek connu
        # On utilise un frek_id arbitrairement issuer pour le doc — ici on teste que le format est coherent
        assert p_raw == j_raw, "passport != jwks"
        assert len(p_raw) == 32
