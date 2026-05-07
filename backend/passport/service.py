"""FREK Passport — service de construction et verification.

Architecture :
- build_passport(frek_id) charge l'identite + dernier block notarise + construit le passeport signe
- disclose(passport, fields) genere un sous-passeport avec preuves Merkle
- verify(doc) valide la signature ET les chemins Merkle (full ou partial)

Format passport.json (full) :
{
  "envelope": {
    "spec_version": "1.0.0",
    "passport_version": 1,
    "key_id": "frek-passport-v1",
    "frek_id": "...",
    "issued_at": "iso8601",
    "claims_count": N,
    "merkle_root": "hex"
  },
  "signature": "base64",  # Ed25519 sur canonical_json(envelope)
  "claims": [ { "key": "...", "value": ..., "nonce": "hex" }, ... ],
  "disclosure": "full"
}

Format disclosure (selective) :
{
  "envelope": { ... },         # identique a la full
  "signature": "base64",       # identique
  "claims": [ { "key", "value", "nonce", "merkle_path": [...] } ],
  "disclosure": "partial"
}
"""
import base64
import logging
from datetime import datetime, timezone
from typing import Any

from . import keys
from .merkle import (
    canonical_json,
    claim_leaf_hex,
    gen_nonce_hex,
    merkle_path,
    merkle_root,
    verify_path,
)

logger = logging.getLogger("frek.passport.service")

PASSPORT_VERSION = 1
SPEC_VERSION = "1.0.0"

# Liste ordonnee des cles de claims emises par le serveur (deterministe).
# L'ordre est important : il fixe l'index Merkle pour chaque claim.
DEFAULT_CLAIM_KEYS = [
    "frek_id",
    "issued_at",
    "spec_version",
    "current_stage",
    "stages_completed",
    "event_id",
    "source",
    "expires_at",
    "revoked",
    "chain_height",
    "chain_block_hash",
    "btc_anchored",
]

db = None


def set_db(database):
    global db
    db = database


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _build_claims(identity: dict) -> list[dict]:
    """Construit les claims en respectant l'ordre DEFAULT_CLAIM_KEYS."""
    # Lookup chain anchor (dernier block) — best-effort, peut etre None si chain vide
    chain_height = None
    chain_block_hash = None
    btc_anchored = False
    if db is not None:
        try:
            last = await db.notary_blocks.find_one(
                {}, {"_id": 0, "height": 1, "block_hash": 1, "btc_anchored": 1},
                sort=[("height", -1)],
            )
            if last:
                chain_height = last.get("height")
                chain_block_hash = last.get("block_hash")
                btc_anchored = bool(last.get("btc_anchored", False))
        except Exception:
            pass

    raw_values = {
        "frek_id": identity["frek_id"],
        "issued_at": _now_iso(),
        "spec_version": SPEC_VERSION,
        "current_stage": identity.get("current_stage", "GENESIS"),
        "stages_completed": identity.get("stages_completed") or [],
        "event_id": identity.get("event"),
        "source": identity.get("source"),
        "expires_at": identity.get("expires_at"),
        "revoked": bool(identity.get("revoked", False)),
        "chain_height": chain_height,
        "chain_block_hash": chain_block_hash,
        "btc_anchored": btc_anchored,
    }

    claims = []
    for k in DEFAULT_CLAIM_KEYS:
        claims.append({"key": k, "value": raw_values.get(k), "nonce": gen_nonce_hex()})
    return claims


def _build_envelope(frek_id: str, issued_at: str, claims: list[dict], root: str) -> dict:
    return {
        "spec_version": SPEC_VERSION,
        "passport_version": PASSPORT_VERSION,
        "key_id": keys.KEY_ID,
        "frek_id": frek_id,
        "issued_at": issued_at,
        "claims_count": len(claims),
        "merkle_root": root,
    }


def _sign_envelope(envelope: dict) -> str:
    return base64.b64encode(keys.sign(canonical_json(envelope))).decode("ascii")


async def build_passport(identity: dict) -> dict:
    """Construit un passeport complet (full disclosure) signe."""
    claims = await _build_claims(identity)
    leaves = [claim_leaf_hex(c["key"], c["value"], c["nonce"]) for c in claims]
    root = merkle_root(leaves)
    # issued_at doit etre dans l'enveloppe ; on prend celui du claim issued_at
    issued_at = next((c["value"] for c in claims if c["key"] == "issued_at"), _now_iso())
    envelope = _build_envelope(identity["frek_id"], issued_at, claims, root)
    signature = _sign_envelope(envelope)
    return {
        "envelope": envelope,
        "signature": signature,
        "claims": claims,
        "disclosure": "full",
    }


def disclose(passport: dict, reveal_keys: list[str]) -> dict:
    """A partir d'un passport full, retourne un sous-passeport avec preuves Merkle.

    Les claims non revele ne sont pas inclus mais leur empreinte reste dans la racine
    via les siblings du chemin Merkle.
    """
    if passport.get("disclosure") != "full":
        raise ValueError("disclose: requires a full passport")
    claims = passport["claims"]
    leaves = [claim_leaf_hex(c["key"], c["value"], c["nonce"]) for c in claims]
    revealed = []
    for k in reveal_keys:
        idx = next((i for i, c in enumerate(claims) if c["key"] == k), None)
        if idx is None:
            raise ValueError(f"disclose: claim '{k}' inconnu")
        path = merkle_path(leaves, idx)
        c = claims[idx]
        revealed.append({"key": c["key"], "value": c["value"], "nonce": c["nonce"], "merkle_path": path})
    return {
        "envelope": passport["envelope"],
        "signature": passport["signature"],
        "claims": revealed,
        "disclosure": "partial",
    }


def verify(doc: dict) -> dict:
    """Verifie un passeport (full ou partial). Retourne {valid, claims, errors}.

    Ne necessite que la cle publique pour la signature ; le reste est cryptographique pur.
    """
    errors: list[str] = []
    envelope = doc.get("envelope")
    sig_b64 = doc.get("signature")
    claims = doc.get("claims") or []
    if not envelope or not sig_b64:
        return {"valid": False, "errors": ["missing envelope or signature"], "claims": []}

    # 1. Signature
    try:
        sig = base64.b64decode(sig_b64)
        if not keys.verify(sig, canonical_json(envelope)):
            errors.append("signature_invalid")
    except Exception as e:
        errors.append(f"signature_decode_error: {e}")

    # 2. Merkle (selon mode)
    expected_root = envelope.get("merkle_root")
    mode = doc.get("disclosure", "full")
    if mode == "full":
        # Recompute root from all claims
        leaves = [claim_leaf_hex(c["key"], c["value"], c["nonce"]) for c in claims]
        if not leaves:
            errors.append("no_claims")
        else:
            actual = merkle_root(leaves)
            if actual != expected_root:
                errors.append("merkle_root_mismatch")
            if envelope.get("claims_count") != len(claims):
                errors.append("claims_count_mismatch")
    else:
        # Partial : chaque claim doit fournir un merkle_path valide
        for c in claims:
            if "merkle_path" not in c:
                errors.append(f"claim_{c.get('key')}_missing_path")
                continue
            leaf = claim_leaf_hex(c["key"], c["value"], c["nonce"])
            if not verify_path(leaf, c["merkle_path"], expected_root):
                errors.append(f"claim_{c.get('key')}_path_invalid")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "envelope": envelope,
        "claims": [{"key": c["key"], "value": c["value"]} for c in claims],
        "mode": mode,
    }
