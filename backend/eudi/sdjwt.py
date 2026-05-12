"""FREK SD-JWT VC — Format vc+sd-jwt (IETF draft-ietf-oauth-sd-jwt-vc-08+).

Phase 4.6 — ajoute le format SD-JWT VC en COMPLEMENT de `ldp_vc`.

INVARIANTS respectes :
- Reutilise la cle Ed25519 existante (passport.keys)
- Aucun changement sur les routes /.well-known/* (issuer metadata declare les 2 formats)
- Aucune regression sur les 256 tests existants
- Le flow OID4VCI existant continue de servir ldp_vc par defaut

Structure SD-JWT VC :
    <JWT base64url>~<disclosure1>~<disclosure2>~...~

JWT payload :
    {
        "iss": "did:frek:frekcore",
        "vct": "FrekCulturalIdentityCredential",
        "iat": <unix>,
        "_sd_alg": "sha-256",
        "_sd": [<digest_base64url>, ...],  // claims selectivement revelables
        ...claims_plats              // claims toujours visibles (frek_id par ex.)
    }

Disclosure = base64url(json([salt_base64url, claim_name, claim_value]))
Digest    = base64url(sha256(disclosure_base64url_string))
"""
import base64
import hashlib
import json
import os
import secrets
import time
from typing import Any, Iterable, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from passport import keys as passport_keys

ISSUER_DID = "did:frek:frekcore"
CREDENTIAL_TYPE = "FrekCulturalIdentityCredential"


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _jcs(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _make_disclosure(name: str, value: Any) -> tuple[str, str]:
    """Retourne (disclosure_string_b64url, digest_b64url)."""
    salt = _b64url(secrets.token_bytes(16))
    arr = [salt, name, value]
    disclosure_str = _b64url(json.dumps(arr, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    digest = _b64url(hashlib.sha256(disclosure_str.encode("ascii")).digest())
    return disclosure_str, digest


def issue_sd_jwt_vc(identity: dict, chain_anchor: Optional[dict] = None) -> dict:
    """Construit un VC SD-JWT signe Ed25519 (EdDSA).

    Retourne {"format":"vc+sd-jwt", "credential": "<jwt>~<disc1>~<disc2>~..."}.
    Le holder peut ensuite presenter un sous-ensemble en omettant des disclosures.
    """
    frek_id = identity["frek_id"]

    # Claims selectivement revelables (le holder choisit ce qu'il revele)
    disclosable = {
        "currentStage": identity.get("current_stage", "GENESIS"),
        "stagesCompleted": identity.get("stages_completed") or [],
        "eventId": identity.get("event"),
        "source": identity.get("source"),
        "expiresAt": identity.get("expires_at"),
        "revoked": bool(identity.get("revoked", False)),
    }
    if chain_anchor:
        disclosable["chainAnchor"] = {
            "height": chain_anchor.get("height"),
            "blockHash": chain_anchor.get("block_hash"),
            "btcAnchored": bool(chain_anchor.get("btc_anchored", False)),
        }

    disclosures = []
    digests = []
    for name, value in disclosable.items():
        if value is None:
            continue
        disc_str, digest = _make_disclosure(name, value)
        disclosures.append(disc_str)
        digests.append(digest)

    # Header JWT (kid pointe vers le DID + verificationMethod)
    header = {
        "alg": "EdDSA",
        "typ": "vc+sd-jwt",
        "kid": f"{ISSUER_DID}#{passport_keys.KEY_ID}",
    }
    payload = {
        "iss": ISSUER_DID,
        "vct": CREDENTIAL_TYPE,
        "iat": int(time.time()),
        "frek_id": frek_id,                 # claim toujours visible
        "specVersion": "1.0.0",             # claim toujours visible
        "_sd_alg": "sha-256",
        "_sd": sorted(digests),             # tri pour determinisme
    }

    signing_input = f"{_b64url(_jcs(header))}.{_b64url(_jcs(payload))}"
    signature = passport_keys.sign(signing_input.encode("ascii"))
    jwt = f"{signing_input}.{_b64url(signature)}"

    sd_jwt = jwt + "~" + "~".join(disclosures) + "~"
    return {"format": "vc+sd-jwt", "credential": sd_jwt}


def verify_sd_jwt_vc(sd_jwt: str) -> dict:
    """Verifie un SD-JWT VC : signature Ed25519 + integrite des digests.

    Retourne {valid, errors, claims, mode}. mode='full' si toutes les disclosures
    presentes, 'partial' sinon.
    """
    errors: list[str] = []
    if not sd_jwt or "~" not in sd_jwt:
        return {"valid": False, "errors": ["malformed_sd_jwt"], "claims": {}, "mode": "unknown"}

    parts = sd_jwt.split("~")
    jwt = parts[0]
    # Le dernier '~' produit un element vide ; les disclosures sont entre.
    raw_disclosures = [p for p in parts[1:] if p]

    jwt_segments = jwt.split(".")
    if len(jwt_segments) != 3:
        return {"valid": False, "errors": ["malformed_jwt"], "claims": {}, "mode": "unknown"}
    header_b64, payload_b64, sig_b64 = jwt_segments

    # Signature
    try:
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        signature = _b64url_decode(sig_b64)
        if not passport_keys.verify(signature, signing_input):
            errors.append("signature_invalid")
    except Exception as e:
        errors.append(f"signature_decode_error:{str(e)[:80]}")

    # Payload
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception as e:
        return {"valid": False, "errors": [f"payload_decode:{e}"], "claims": {}, "mode": "unknown"}

    sd_digests = set(payload.get("_sd", []))

    # Verifie les disclosures fournies
    revealed_claims = {}
    for d in raw_disclosures:
        digest = _b64url(hashlib.sha256(d.encode("ascii")).digest())
        if digest not in sd_digests:
            errors.append(f"disclosure_digest_unknown:{digest[:10]}")
            continue
        try:
            arr = json.loads(_b64url_decode(d))
            if not isinstance(arr, list) or len(arr) != 3:
                errors.append("disclosure_shape")
                continue
            _salt, name, value = arr
            revealed_claims[name] = value
        except Exception as e:
            errors.append(f"disclosure_decode:{str(e)[:60]}")

    # Mode : si toutes les disclosures sont revelees => full, sinon partial
    mode = "full" if len(raw_disclosures) == len(sd_digests) else "partial"

    # Claims plats (non SD)
    flat = {k: v for k, v in payload.items() if k not in ("_sd", "_sd_alg")}
    flat.update(revealed_claims)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "claims": flat,
        "mode": mode,
    }
