"""FREK DID — Construction du DID Document W3C DID Core 1.0.

Methode : `did:frek:{frek_id}`
Resolution : 100% determinist a partir du frek_id et de la cle publique serveur
            (qui est la meme que celle des passeports — cle de notariat).

Compatible :
- W3C DID Core 1.0
- W3C Verification Method Multikey (cryptosuite multikey)
- eIDAS 2.0 / EUDI Wallet (importable comme issuer)
"""
import os
from typing import Optional

from passport import keys as passport_keys
from .encoding import public_key_multibase

DID_METHOD = "frek"
PUBLIC_BASE_URL = os.environ.get("FREK_PUBLIC_BASE_URL", "https://frekcore.com").rstrip("/")


def did_for(frek_id: str) -> str:
    return f"did:{DID_METHOD}:{frek_id}"


def verification_method_id(frek_id: str) -> str:
    return f"{did_for(frek_id)}#{passport_keys.KEY_ID}"


def build_did_document(frek_id: str) -> dict:
    """Genere le DID Document JSON-LD pour un FREK-ID."""
    did = did_for(frek_id)
    vm_id = verification_method_id(frek_id)
    pub_mb = public_key_multibase(passport_keys.get_public_key())

    return {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/multikey/v1",
        ],
        "id": did,
        "controller": did,
        "verificationMethod": [
            {
                "id": vm_id,
                "type": "Multikey",
                "controller": did,
                "publicKeyMultibase": pub_mb,
            }
        ],
        "authentication": [vm_id],
        "assertionMethod": [vm_id],
        "service": [
            {
                "id": f"{did}#frek-verify",
                "type": "FrekVerificationService",
                "serviceEndpoint": f"{PUBLIC_BASE_URL}/verify/{frek_id}",
            },
            {
                "id": f"{did}#frek-passport",
                "type": "FrekPassportService",
                "serviceEndpoint": f"{PUBLIC_BASE_URL}/api/v1/passport/{frek_id}",
            },
            {
                "id": f"{did}#frek-vc",
                "type": "VerifiableCredentialService",
                "serviceEndpoint": f"{PUBLIC_BASE_URL}/api/v1/vc/{frek_id}",
            },
        ],
    }


DID_METHOD_SPEC = {
    "method": "frek",
    "version": "1.0.0",
    "specification_url": f"{PUBLIC_BASE_URL}/api/v1/did/method/spec",
    "summary": (
        "did:frek est une methode DID deterministe pour les identites culturelles "
        "souveraines emises par FREKCORE. Le DID est compose du prefixe 'did:frek:' "
        "suivi du FREK-ID (UUID v4)."
    ),
    "syntax": "did:frek:<frek_id>",
    "method_specific_id": "FREK-ID, format UUID v4 RFC 4122",
    "operations": {
        "create": "FREK-ID emis via POST /api/v1/identity/emit (FREKCORE-controled, multi-tenant)",
        "read": "GET /api/v1/did/{frek_id} retourne le DID Document JSON-LD",
        "update": (
            "Le DID Document est genere a partir de la cle publique de notariat (rotation "
            "centrale annoncee via /api/v1/passport/key et /api/v1/spec). "
            "Les mises a jour de cycle de vie (revoque, expire) sont reflechies dans le VC."
        ),
        "deactivate": (
            "Une revocation FREK-ID via POST /api/v1/identity/{frek_id}/revoke est equivalente "
            "a une desactivation : le VC emis post-revocation porte un statut revoke=true."
        ),
    },
    "verification_methods": [
        {
            "type": "Multikey",
            "cryptosuite": "eddsa-jcs-2022 (W3C VC Data Integrity 1.0)",
            "key_algorithm": "Ed25519 (RFC 8032)",
        }
    ],
    "services": [
        "FrekVerificationService — page publique /verify/{frek_id}",
        "FrekPassportService — passeport souverain /api/v1/passport/{frek_id}",
        "VerifiableCredentialService — VC W3C /api/v1/vc/{frek_id}",
    ],
    "compatibility": [
        "W3C DID Core 1.0",
        "W3C VC Data Model 2.0",
        "eIDAS 2.0 / EUDI Wallet (importable comme issuer)",
    ],
    "trust_root": (
        "La cle publique du verificationMethod est la meme que celle des passeports "
        "(`/api/v1/passport/key`). C'est la racine de confiance du notariat FREKCORE."
    ),
}
