"""FREK EUDI — Issuer metadata + OAuth server metadata.

Conforme :
- OpenID4VCI Draft 13 (`/.well-known/openid-credential-issuer`)
- RFC 8414 OAuth 2.0 Authorization Server Metadata
"""
import os

PUBLIC_BASE_URL = os.environ.get("FREK_PUBLIC_BASE_URL", "https://frekcore.com").rstrip("/")
ISSUER_DID = "did:frek:frekcore"

CREDENTIAL_CONFIG_ID = "FrekCulturalIdentityCredential_jsonld"


def issuer_metadata() -> dict:
    """OpenID4VCI issuer metadata.

    Expose les types de VC supportes + endpoints. Les wallets EUDI utilisent
    ce manifest pour decouvrir comment dialoguer avec FREKCORE.
    """
    return {
        "credential_issuer": PUBLIC_BASE_URL,
        "authorization_servers": [PUBLIC_BASE_URL],
        "credential_endpoint": f"{PUBLIC_BASE_URL}/api/v1/eudi/credential",
        "token_endpoint": f"{PUBLIC_BASE_URL}/api/v1/eudi/token",
        "credential_offer_endpoint": "openid-credential-offer://",
        "display": [
            {
                "name": "FREKCORE — Notaire Culturel Tech",
                "locale": "fr-FR",
                "logo": {
                    "uri": f"{PUBLIC_BASE_URL}/frek-logo.png",
                    "alt_text": "FREK",
                },
                "background_color": "#0a1520",
                "text_color": "#ffffff",
            },
            {
                "name": "FREKCORE — Cultural Identity Notary",
                "locale": "en-US",
                "logo": {"uri": f"{PUBLIC_BASE_URL}/frek-logo.png", "alt_text": "FREK"},
            },
        ],
        "credential_configurations_supported": {
            CREDENTIAL_CONFIG_ID: {
                "format": "ldp_vc",
                "scope": "FrekCulturalIdentityCredential",
                "cryptographic_binding_methods_supported": ["did:frek", "did:key", "jwk"],
                "credential_signing_alg_values_supported": ["EdDSA"],
                "proof_types_supported": {
                    "jwt": {"proof_signing_alg_values_supported": ["EdDSA", "ES256"]},
                    "ldp_vp": {"proof_signing_alg_values_supported": ["EdDSA"]},
                },
                "credential_definition": {
                    "@context": [
                        "https://www.w3.org/ns/credentials/v2",
                        f"{PUBLIC_BASE_URL}/contexts/frek/v1",
                    ],
                    "type": ["VerifiableCredential", "FrekCulturalIdentityCredential"],
                    "credentialSubject": {
                        "frek_id": {"display": [{"name": "FREK-ID", "locale": "fr-FR"}]},
                        "currentStage": {"display": [{"name": "Stage Luciole", "locale": "fr-FR"}]},
                        "eventId": {"display": [{"name": "Evenement", "locale": "fr-FR"}]},
                        "specVersion": {"display": [{"name": "Version standard", "locale": "fr-FR"}]},
                    },
                },
                "display": [
                    {
                        "name": "Identite culturelle FREK",
                        "locale": "fr-FR",
                        "description": "Passeport culturel souverain notarise sur Bitcoin",
                        "background_color": "#0a1520",
                        "text_color": "#2cc4f5",
                    },
                    {
                        "name": "FREK Cultural Identity",
                        "locale": "en-US",
                        "description": "Sovereign cultural passport notarized on Bitcoin",
                    },
                ],
            },
            "FrekCulturalIdentityCredential_sdjwt": {
                "format": "vc+sd-jwt",
                "scope": "FrekCulturalIdentityCredential",
                "vct": "FrekCulturalIdentityCredential",
                "cryptographic_binding_methods_supported": ["did:frek", "jwk"],
                "credential_signing_alg_values_supported": ["EdDSA"],
                "proof_types_supported": {
                    "jwt": {"proof_signing_alg_values_supported": ["EdDSA", "ES256"]},
                },
                "claims": {
                    "frek_id": {"display": [{"name": "FREK-ID", "locale": "fr-FR"}]},
                    "currentStage": {"display": [{"name": "Stage Luciole", "locale": "fr-FR"}]},
                    "eventId": {"display": [{"name": "Evenement", "locale": "fr-FR"}]},
                    "specVersion": {"display": [{"name": "Version standard", "locale": "fr-FR"}]},
                },
                "display": [
                    {
                        "name": "FREK Cultural Identity (SD-JWT)",
                        "locale": "fr-FR",
                        "description": "Format mobile / offline / selective disclosure native",
                    }
                ],
            },
        },
    }


def oauth_authorization_server_metadata() -> dict:
    """RFC 8414 — minimal pour pre-authorized code flow OID4VCI."""
    return {
        "issuer": PUBLIC_BASE_URL,
        "token_endpoint": f"{PUBLIC_BASE_URL}/api/v1/eudi/token",
        "token_endpoint_auth_methods_supported": ["none"],  # pre-auth flow
        "grant_types_supported": [
            "urn:ietf:params:oauth:grant-type:pre-authorized_code",
        ],
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "pre-authorized_grant_anonymous_access_supported": True,
    }
