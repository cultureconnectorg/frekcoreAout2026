"""FREK Phase 4 — Tests W3C DID + Verifiable Credentials.

Couvre :
- DID Document W3C DID Core 1.0 (id, verificationMethod Multikey, services)
- VC W3C Data Model 2.0 + DataIntegrityProof / eddsa-jcs-2022
- Verification offline (signature + integrite)
- Tampering : credentialSubject, proof, type
- Compatibilite : interopable avec wallets EUDI / eIDAS 2.0 (format de proof standard)
"""
import base64
import copy
import os
import secrets

import pytest
import requests


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
    email = f"did_pytest_{secrets.token_hex(4)}@frekcore.fr"
    r = requests.post(
        f"{API}/identity/emit",
        json={"email": email, "source": "test", "event": "CC2026"},
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    return r.json()["frek_id"]


# ---------- DID Document ----------
class TestDIDMethodSpec:
    def test_method_spec_endpoint(self):
        r = requests.get(f"{API}/did/method/spec", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert d["method"] == "frek"
        assert d["syntax"] == "did:frek:<frek_id>"
        # Compatibilite annoncee
        compat = " ".join(d.get("compatibility", []))
        assert "DID Core 1.0" in compat
        assert "EUDI" in compat or "eIDAS" in compat


class TestDIDDocument:
    def test_resolve_returns_w3c_did_document(self, emitted_frek_id):
        r = requests.get(f"{API}/did/{emitted_frek_id}", timeout=5)
        assert r.status_code == 200
        d = r.json()
        # W3C DID Core 1.0 invariants
        assert d["id"] == f"did:frek:{emitted_frek_id}"
        assert "https://www.w3.org/ns/did/v1" in d["@context"]
        # Verification method
        assert len(d["verificationMethod"]) >= 1
        vm = d["verificationMethod"][0]
        assert vm["type"] == "Multikey"
        assert vm["controller"] == d["id"]
        assert vm["publicKeyMultibase"].startswith("z")  # multibase base58btc
        # Authentication & assertionMethod referencent la VM
        assert vm["id"] in d["authentication"]
        assert vm["id"] in d["assertionMethod"]

    def test_services_present(self, emitted_frek_id):
        d = requests.get(f"{API}/did/{emitted_frek_id}", timeout=5).json()
        types = {s["type"] for s in d.get("service", [])}
        assert "FrekVerificationService" in types
        assert "FrekPassportService" in types
        assert "VerifiableCredentialService" in types

    def test_unknown_did_returns_404(self):
        r = requests.get(f"{API}/did/unknown-frek-id-xxx", timeout=5)
        assert r.status_code == 404


# ---------- Verifiable Credential ----------
class TestVerifiableCredential:
    def test_issue_vc(self, emitted_frek_id):
        r = requests.get(f"{API}/vc/{emitted_frek_id}", timeout=5)
        assert r.status_code == 200
        vc = r.json()
        # W3C VC Data Model 2.0
        assert "https://www.w3.org/ns/credentials/v2" in vc["@context"]
        assert "VerifiableCredential" in vc["type"]
        assert "FrekCulturalIdentityCredential" in vc["type"]
        # Subject
        sub = vc["credentialSubject"]
        assert sub["id"] == f"did:frek:{emitted_frek_id}"
        assert sub["frek_id"] == emitted_frek_id
        assert sub["specVersion"] == "1.0.0"
        # Proof
        proof = vc["proof"]
        assert proof["type"] == "DataIntegrityProof"
        assert proof["cryptosuite"] == "eddsa-jcs-2022"
        assert proof["proofPurpose"] == "assertionMethod"
        assert proof["verificationMethod"].startswith("did:frek:")
        assert proof["proofValue"].startswith("z")

    def test_verify_valid_vc(self, emitted_frek_id):
        vc = requests.get(f"{API}/vc/{emitted_frek_id}", timeout=5).json()
        r = requests.post(f"{API}/vc/verify", json={"credential": vc}, timeout=5).json()
        assert r["valid"] is True
        assert r["errors"] == []
        assert r["subject"]["frek_id"] == emitted_frek_id

    def test_tamper_subject_invalidates(self, emitted_frek_id):
        vc = requests.get(f"{API}/vc/{emitted_frek_id}", timeout=5).json()
        vc["credentialSubject"]["currentStage"] = "TAMPERED"
        r = requests.post(f"{API}/vc/verify", json={"credential": vc}, timeout=5).json()
        assert r["valid"] is False
        assert "signature_invalid" in r["errors"]

    def test_tamper_proof_value_invalidates(self, emitted_frek_id):
        vc = requests.get(f"{API}/vc/{emitted_frek_id}", timeout=5).json()
        # Replace proofValue with random bytes (must still be base58 multibase)
        import base58
        vc["proof"]["proofValue"] = "z" + base58.b58encode(b"\x00" * 64).decode("ascii")
        r = requests.post(f"{API}/vc/verify", json={"credential": vc}, timeout=5).json()
        assert r["valid"] is False
        assert "signature_invalid" in r["errors"]

    def test_missing_proof_invalidates(self, emitted_frek_id):
        vc = requests.get(f"{API}/vc/{emitted_frek_id}", timeout=5).json()
        del vc["proof"]
        r = requests.post(f"{API}/vc/verify", json={"credential": vc}, timeout=5).json()
        assert r["valid"] is False

    def test_unknown_frek_id_404(self):
        r = requests.get(f"{API}/vc/unknown-id", timeout=5)
        assert r.status_code == 404


# ---------- Cle de confiance partagee avec passeport ----------
class TestTrustRoot:
    def test_did_vm_uses_same_key_as_passport(self, emitted_frek_id):
        """La cle publique exposee dans DID Document doit correspondre a /passport/key."""
        from did.encoding import public_key_multibase
        from passport import keys as pkeys

        # Cle publique passport
        passport_pub = pkeys.get_public_key()
        expected_mb = public_key_multibase(passport_pub)

        # Cle dans DID Document
        did_doc = requests.get(f"{API}/did/{emitted_frek_id}", timeout=5).json()
        actual_mb = did_doc["verificationMethod"][0]["publicKeyMultibase"]

        assert actual_mb == expected_mb, "DID VM key != passport key — racine de confiance brisee"
