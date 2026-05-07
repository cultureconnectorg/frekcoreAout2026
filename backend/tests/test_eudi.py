"""FREK EUDI Plugin — Tests OID4VCI flow complet.

Couvre :
- Issuer metadata (.well-known/openid-credential-issuer)
- OAuth metadata (.well-known/oauth-authorization-server)
- Pre-authorized code flow : create offer -> token -> credential
- Single-use du code (deuxieme appel echoue)
- Token expire / invalide
"""
import os
import secrets
import urllib.parse
import json

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"

CLIENT_ID = os.environ.get("FREK_CLIENT_KILTIKONET_ID", "kiltikonet-cc2026")
CLIENT_SECRET = os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", "pczBP49crCXSSSwSOShsXClzs9srhKe5S-xnraMPn-k")


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{API}/auth/token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=10,
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def emitted_frek_id(auth_headers):
    email = f"eudi_pytest_{secrets.token_hex(4)}@frekcore.fr"
    r = requests.post(
        f"{API}/identity/emit",
        json={"email": email, "source": "test", "event": "CC2026"},
        headers=auth_headers, timeout=10,
    )
    return r.json()["frek_id"]


# ---------- Issuer metadata ----------
class TestIssuerMetadata:
    def test_openid_credential_issuer(self):
        r = requests.get(f"{BASE_URL}/api/.well-known/openid-credential-issuer", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert d["credential_issuer"]
        assert d["credential_endpoint"]
        assert d["token_endpoint"]
        assert "FrekCulturalIdentityCredential_jsonld" in d["credential_configurations_supported"]
        cfg = d["credential_configurations_supported"]["FrekCulturalIdentityCredential_jsonld"]
        assert cfg["format"] == "ldp_vc"
        assert "EdDSA" in cfg["credential_signing_alg_values_supported"]
        assert "did:frek" in cfg["cryptographic_binding_methods_supported"]

    def test_oauth_metadata(self):
        r = requests.get(f"{BASE_URL}/api/.well-known/oauth-authorization-server", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert d["issuer"]
        assert "urn:ietf:params:oauth:grant-type:pre-authorized_code" in d["grant_types_supported"]


# ---------- Credential offer ----------
class TestCredentialOffer:
    def test_create_offer_returns_qr_data(self, emitted_frek_id):
        r = requests.post(f"{API}/eudi/credential-offer/{emitted_frek_id}", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert d["credential_offer"]
        assert d["credential_offer_uri_deep_link"].startswith("openid-credential-offer://")
        assert "credential_offer=" in d["credential_offer_uri_deep_link"]
        # Pre-auth code present
        grants = d["credential_offer"]["grants"]
        assert "urn:ietf:params:oauth:grant-type:pre-authorized_code" in grants
        code = grants["urn:ietf:params:oauth:grant-type:pre-authorized_code"]["pre-authorized_code"]
        assert len(code) > 20

    def test_create_offer_unknown_id_404(self):
        r = requests.post(f"{API}/eudi/credential-offer/unknown-id", timeout=5)
        assert r.status_code == 404


# ---------- Flow complet ----------
class TestFullFlow:
    def _full_flow(self, frek_id):
        # 1. Create offer
        offer = requests.post(f"{API}/eudi/credential-offer/{frek_id}", timeout=5).json()
        code = offer["credential_offer"]["grants"][
            "urn:ietf:params:oauth:grant-type:pre-authorized_code"
        ]["pre-authorized_code"]

        # 2. Exchange code for token
        token_r = requests.post(
            f"{API}/eudi/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code",
                "pre-authorized_code": code,
            },
            timeout=5,
        )
        assert token_r.status_code == 200, token_r.text
        token = token_r.json()
        assert token["token_type"] == "Bearer"
        assert token["expires_in"] > 0

        # 3. Fetch credential
        cred_r = requests.post(
            f"{API}/eudi/credential",
            json={"format": "ldp_vc"},
            headers={"Authorization": f"Bearer {token['access_token']}"},
            timeout=5,
        )
        assert cred_r.status_code == 200, cred_r.text
        return cred_r.json(), code, token["access_token"]

    def test_pre_authorized_code_flow_end_to_end(self, emitted_frek_id):
        result, _, _ = self._full_flow(emitted_frek_id)
        assert result["format"] == "ldp_vc"
        vc = result["credential"]
        assert "VerifiableCredential" in vc["type"]
        assert "FrekCulturalIdentityCredential" in vc["type"]
        assert vc["credentialSubject"]["frek_id"] == emitted_frek_id
        assert vc["proof"]["type"] == "DataIntegrityProof"
        assert vc["proof"]["cryptosuite"] == "eddsa-jcs-2022"

    def test_pre_authorized_code_single_use(self, emitted_frek_id):
        _, code, _ = self._full_flow(emitted_frek_id)
        # Reutiliser le code => 400
        r = requests.post(
            f"{API}/eudi/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code",
                "pre-authorized_code": code,
            },
            timeout=5,
        )
        assert r.status_code == 400

    def test_invalid_grant_type(self, emitted_frek_id):
        r = requests.post(
            f"{API}/eudi/token",
            data={"grant_type": "authorization_code", "pre-authorized_code": "x"},
            timeout=5,
        )
        assert r.status_code == 400

    def test_invalid_token_returns_401(self):
        r = requests.post(
            f"{API}/eudi/credential",
            json={"format": "ldp_vc"},
            headers={"Authorization": "Bearer fake-token"},
            timeout=5,
        )
        assert r.status_code == 401

    def test_credential_unsupported_format(self, emitted_frek_id):
        # Fresh offer + token
        offer = requests.post(f"{API}/eudi/credential-offer/{emitted_frek_id}", timeout=5).json()
        code = offer["credential_offer"]["grants"][
            "urn:ietf:params:oauth:grant-type:pre-authorized_code"
        ]["pre-authorized_code"]
        token = requests.post(
            f"{API}/eudi/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code",
                "pre-authorized_code": code,
            },
            timeout=5,
        ).json()["access_token"]
        # Format invalide
        r = requests.post(
            f"{API}/eudi/credential",
            json={"format": "vc+sd-jwt"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        assert r.status_code == 400

    def test_vc_verifies_with_existing_endpoint(self, emitted_frek_id):
        """Le VC issu via OID4VCI doit valider sur /api/v1/vc/verify."""
        result, _, _ = self._full_flow(emitted_frek_id)
        vc = result["credential"]
        v = requests.post(f"{API}/vc/verify", json={"credential": vc}, timeout=5).json()
        assert v["valid"] is True
        assert v["errors"] == []
