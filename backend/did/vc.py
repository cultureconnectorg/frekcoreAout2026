"""FREK Verifiable Credential — W3C VC Data Model 2.0 + Data Integrity Proof.

Format : DataIntegrityProof / cryptosuite=eddsa-jcs-2022 (RFC 8785 JCS, lightweight).

Aucune dependance JSON-LD lourde (pas de pyld). La canonicalisation JCS suffit a la
verification offline + aux wallets EUDI compatibles eddsa-jcs-2022.
"""
import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from passport import keys as passport_keys
from .document import did_for, verification_method_id
from .encoding import signature_multibase, decode_multibase_b58btc


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jcs(obj) -> bytes:
    """JSON Canonicalization Scheme RFC 8785 — version pragmatique :
    - cles triees alphabetiquement
    - separateurs minimaux
    - pas d'espace
    - pas d'unicode normalization (notre data est UUID/ASCII)
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _build_credential_subject(identity: dict, chain_anchor: Optional[dict]) -> dict:
    frek_id = identity["frek_id"]
    subject = {
        "id": did_for(frek_id),
        "frek_id": frek_id,
        "type": "FrekCulturalIdentity",
        "currentStage": identity.get("current_stage", "GENESIS"),
        "stagesCompleted": identity.get("stages_completed") or [],
        "eventId": identity.get("event"),
        "source": identity.get("source"),
        "specVersion": "1.0.0",
        "revoked": bool(identity.get("revoked", False)),
    }
    if identity.get("expires_at"):
        subject["expiresAt"] = identity["expires_at"]
    if chain_anchor:
        subject["chainAnchor"] = {
            "height": chain_anchor.get("height"),
            "blockHash": chain_anchor.get("block_hash"),
            "btcAnchored": bool(chain_anchor.get("btc_anchored", False)),
        }
    return subject


def _sign_proof(unsigned_vc: dict) -> dict:
    """Construit la proof DataIntegrityProof / eddsa-jcs-2022.

    Algorithme (W3C VC DI 1.0, eddsa-jcs-2022) :
        proofConfig = proof sans proofValue
        c14n = JCS(unsigned_vc) + JCS(proofConfig) ... (simplifie : on hash le bundle JCS du VC + proofConfig)
        message = sha256(c14n_vc) || sha256(c14n_proof)
        signature = Ed25519(message)
        proofValue = multibase(signature)
    """
    proof_config = {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "created": _now_iso(),
        "verificationMethod": verification_method_id(unsigned_vc["credentialSubject"]["frek_id"]),
        "proofPurpose": "assertionMethod",
    }
    # Hash du document VC + hash du proof config, concatenes, signes
    vc_hash = hashlib.sha256(_jcs(unsigned_vc)).digest()
    proof_hash = hashlib.sha256(_jcs(proof_config)).digest()
    signature = passport_keys.sign(proof_hash + vc_hash)
    return {**proof_config, "proofValue": signature_multibase(signature)}


def build_credential(identity: dict, chain_anchor: Optional[dict] = None) -> dict:
    """Assemble un VC complet signe pour un FREK-ID."""
    frek_id = identity["frek_id"]
    issuer_did = "did:frek:frekcore"  # Issuer institutionnel (FREKCORE)
    issuance = _now_iso()

    unsigned = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://frekcore.com/contexts/frek/v1",
        ],
        "id": f"urn:frek:vc:{frek_id}:{issuance}",
        "type": ["VerifiableCredential", "FrekCulturalIdentityCredential"],
        "issuer": issuer_did,
        "validFrom": issuance,
        "credentialSubject": _build_credential_subject(identity, chain_anchor),
    }
    proof = _sign_proof(unsigned)
    return {**unsigned, "proof": proof}


def verify_credential(vc: dict) -> dict:
    """Verifie un VC FREK signe en eddsa-jcs-2022. Retourne {valid, errors, subject}.

    Verification 100% offline avec la cle publique du serveur (memes garanties que les
    passeports — meme racine de confiance).
    """
    errors: list[str] = []
    proof = vc.get("proof")
    if not proof:
        return {"valid": False, "errors": ["missing proof"], "subject": None}
    if proof.get("type") != "DataIntegrityProof":
        errors.append("proof_type_unsupported")
    if proof.get("cryptosuite") != "eddsa-jcs-2022":
        errors.append("cryptosuite_unsupported")

    proof_value = proof.get("proofValue")
    if not proof_value:
        return {"valid": False, "errors": errors + ["missing proofValue"], "subject": None}

    # Reconstruction du message signe
    proof_config = {k: v for k, v in proof.items() if k != "proofValue"}
    unsigned = {k: v for k, v in vc.items() if k != "proof"}
    vc_hash = hashlib.sha256(_jcs(unsigned)).digest()
    proof_hash = hashlib.sha256(_jcs(proof_config)).digest()

    try:
        sig = decode_multibase_b58btc(proof_value)
        if not passport_keys.verify(sig, proof_hash + vc_hash):
            errors.append("signature_invalid")
    except Exception as e:
        errors.append(f"signature_decode_error:{str(e)[:80]}")

    # Type checks
    if "VerifiableCredential" not in (vc.get("type") or []):
        errors.append("type_missing_VerifiableCredential")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "subject": vc.get("credentialSubject"),
        "issuer": vc.get("issuer"),
        "validFrom": vc.get("validFrom"),
    }
