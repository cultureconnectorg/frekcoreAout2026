"""FREK Standards — JWK Set + DID Configuration + Manifest universel."""
import base64
import hashlib
import os
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization

from passport import keys as passport_keys
from did.document import did_for, verification_method_id

PUBLIC_BASE_URL = os.environ.get("FREK_PUBLIC_BASE_URL", "https://frekcore.com").rstrip("/")
ISSUER_DID = "did:frek:frekcore"


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def jwk_set() -> dict:
    """JWK Set RFC 7517 exposant la cle publique Ed25519 (kty=OKP, crv=Ed25519).

    Format universellement consomme par les wallets, services SSO, ITU.
    """
    pub = passport_keys.get_public_key()
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    # kid stable derive du hash de la cle (RFC 7638-ish)
    kid = hashlib.sha256(raw).hexdigest()[:16]
    return {
        "keys": [
            {
                "kty": "OKP",
                "crv": "Ed25519",
                "x": _b64url(raw),
                "use": "sig",
                "alg": "EdDSA",
                "kid": kid,
                "key_id": passport_keys.KEY_ID,
            }
        ]
    }


def did_configuration() -> dict:
    """DIF Well-Known DID Configuration v1.

    Prouve que le domaine `frekcore.com` controle bien `did:frek:frekcore`.
    Les wallets (EUDI, Microsoft Authenticator, Trinsic) verifient ce document
    pour etablir la confiance domaine→DID.

    Spec : https://identity.foundation/.well-known/resources/did-configuration/
    """
    issued = datetime.now(timezone.utc).isoformat()
    domain = PUBLIC_BASE_URL.replace("https://", "").replace("http://", "")

    # Domain Linkage Credential (VC qui prouve le lien)
    vc_subject = {
        "id": ISSUER_DID,
        "origin": PUBLIC_BASE_URL,
    }
    # Construction VC simplifiee (DI proof)
    from did.vc import _jcs, _sign_proof
    unsigned = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://identity.foundation/.well-known/did-configuration/v1",
        ],
        "id": f"urn:frek:domain-linkage:{domain}",
        "type": ["VerifiableCredential", "DomainLinkageCredential"],
        "issuer": ISSUER_DID,
        "validFrom": issued,
        "credentialSubject": vc_subject,
    }
    proof = _sign_proof_for_domain_linkage(unsigned)
    linked_vc = {**unsigned, "proof": proof}

    return {
        "@context": "https://identity.foundation/.well-known/did-configuration/v1",
        "linked_dids": [linked_vc],
    }


def _sign_proof_for_domain_linkage(unsigned_vc: dict) -> dict:
    """Reproduit la logique vc._sign_proof mais avec le DID issuer institutionnel."""
    from did.vc import _jcs
    proof_config = {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "created": datetime.now(timezone.utc).isoformat(),
        "verificationMethod": f"{ISSUER_DID}#{passport_keys.KEY_ID}",
        "proofPurpose": "assertionMethod",
    }
    vc_hash = hashlib.sha256(_jcs(unsigned_vc)).digest()
    proof_hash = hashlib.sha256(_jcs(proof_config)).digest()
    signature = passport_keys.sign(proof_hash + vc_hash)
    from did.encoding import signature_multibase
    return {**proof_config, "proofValue": signature_multibase(signature)}


# ---------- Manifest universel par ecosysteme ----------

def manifest_universal() -> dict:
    """Manifest declaratif global. Liste tous les standards supportes + endpoints."""
    return {
        "name": "FREKCORE",
        "version": "1.0.0",
        "description": "Standard global d'identite culturelle souveraine. Notaire culturel tech.",
        "issuer_did": ISSUER_DID,
        "public_base_url": PUBLIC_BASE_URL,
        "ecosystems": {
            "w3c": {
                "did_core": {
                    "version": "1.0",
                    "method": "did:frek",
                    "method_spec_url": f"{PUBLIC_BASE_URL}/api/v1/did/method/spec",
                    "did_configuration_url": f"{PUBLIC_BASE_URL}/.well-known/did-configuration.json",
                },
                "vc_data_model": {
                    "version": "2.0",
                    "credential_types": ["FrekCulturalIdentityCredential"],
                    "proof_format": "DataIntegrityProof / eddsa-jcs-2022",
                    "issue_endpoint": f"{PUBLIC_BASE_URL}/api/v1/vc/{{frek_id}}",
                    "verify_endpoint": f"{PUBLIC_BASE_URL}/api/v1/vc/verify",
                },
            },
            "eudi": {
                "name": "EUDI Wallet (UE / eIDAS 2.0)",
                "oid4vci": {
                    "draft_version": "13+",
                    "issuer_metadata_url": f"{PUBLIC_BASE_URL}/.well-known/openid-credential-issuer",
                    "oauth_metadata_url": f"{PUBLIC_BASE_URL}/.well-known/oauth-authorization-server",
                    "credential_offer_endpoint": f"{PUBLIC_BASE_URL}/api/v1/eudi/credential-offer/{{frek_id}}",
                    "supported_grants": ["urn:ietf:params:oauth:grant-type:pre-authorized_code"],
                },
                "compliance": ["W3C DID 1.0", "W3C VC 2.0", "OID4VCI Draft 13", "RFC 8414"],
                "geographic_scope": "27 Etats membres UE + EEE",
            },
            "id4africa": {
                "name": "ID4Africa / AFCFTA Identity",
                "compatibility": [
                    "W3C DID Core 1.0 (universellement importable par les ecosystemes africains compatibles)",
                    "W3C VC Data Model 2.0 (verification offline cruciale pour zones a connectivite limitee)",
                    "JWK Set RFC 7517 (compatible OID-Connect, mobile money APIs)",
                ],
                "key_features_for_africa": [
                    "Verification 100% offline avec cle publique archive (verifier offline Python + JS)",
                    "Disclosure selective Merkle (data minimization GDPR/AfCFTA)",
                    "Pas de registre central blockchain proprietaire — Bitcoin via OTS = neutre",
                    "Open spec, multi-tenant event_id permet usage souverain par chaque etat",
                ],
                "geographic_scope": "55 Etats UA, AFCFTA single market",
            },
            "itu": {
                "name": "ITU-T standards (pays en developpement)",
                "alignment": [
                    "ITU-T X.1252 (Identity management framework)",
                    "ITU-T X.509 PKI (compatibilite via JWK Set + DID Document)",
                    "NIST SP 800-63-3 IAL2/AAL2 ready (Ed25519 signature + multi-factor staff PIN)",
                ],
            },
            "iso_mdl": {
                "name": "ISO mDL (mobile driving license, preparation US roadmap)",
                "status": "compatible_via_extension",
                "notes": (
                    "Le format VC W3C peut etre converti en mDOC ISO 18013-5 via un transcodeur. "
                    "Phase 6 (US) : implementer endpoint /api/v1/mdoc/{frek_id} retournant CBOR mDL."
                ),
            },
            "caricom": {
                "name": "CARICOM Single ICT Space",
                "status": "ready",
                "notes": (
                    "FREKCORE est deploye dans la zone Caraibes (CC2026 Cayenne). "
                    "Spec ouverte permet l'adoption par les 15 etats CARICOM sans negociation centrale."
                ),
            },
        },
        "well_known_endpoints": {
            "jwks": f"{PUBLIC_BASE_URL}/.well-known/jwks.json",
            "did_configuration": f"{PUBLIC_BASE_URL}/.well-known/did-configuration.json",
            "openid_credential_issuer": f"{PUBLIC_BASE_URL}/.well-known/openid-credential-issuer",
            "oauth_authorization_server": f"{PUBLIC_BASE_URL}/.well-known/oauth-authorization-server",
        },
        "trust_root": {
            "algorithm": "Ed25519 (RFC 8032)",
            "key_id": passport_keys.KEY_ID,
            "public_key_endpoint": f"{PUBLIC_BASE_URL}/api/v1/passport/key",
            "jwk_set_endpoint": f"{PUBLIC_BASE_URL}/.well-known/jwks.json",
            "shared_with": ["passport", "did_vc", "eudi", "seal", "domain_linkage"],
        },
        "geographic_roadmap": {
            "current": "CC2026 — Cayenne / Guyane Francaise (Caraibes/AmSud)",
            "next": ["CARICOM (15 etats)", "ID4Africa (55 etats)", "EUDI (27 etats UE)", "USA mDL"],
            "horizon": "IPO 2028",
        },
    }
