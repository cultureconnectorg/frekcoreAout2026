#!/usr/bin/env python3
"""FREK Passport — Verifier offline standalone.

Ne depend QUE de la lib `cryptography` (PyPI). Aucun appel reseau.
Verifie un passport.json (full ou partial) a partir d'une cle publique Ed25519.

Usage :
    python verify_passport.py --passport passport.json --public-key key.pem
    python verify_passport.py --passport passport.json --public-key-b64 "Crgw..."

Sortie JSON :
    {"valid": true, "mode": "full"|"partial", "errors": [], "claims": [...]}

Exit code : 0 si valid=true, 1 sinon.

Specification : voir /api/v1/spec/v1.0.0 section passport.
"""
import argparse
import base64
import hashlib
import json
import sys
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def claim_leaf_hex(c: dict) -> str:
    payload = canonical_json({"key": c["key"], "nonce": c["nonce"], "value": c["value"]})
    return hashlib.sha256(payload).hexdigest()


def hash_pair_hex(left: str, right: str) -> str:
    return hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()


def merkle_root_from_leaves(leaves: list[str]) -> str:
    cur = list(leaves)
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            l = cur[i]
            r = cur[i + 1] if i + 1 < len(cur) else cur[i]
            nxt.append(hash_pair_hex(l, r))
        cur = nxt
    return cur[0]


def verify_merkle_path(leaf: str, path: list[dict], expected_root: str) -> bool:
    cur = leaf
    for step in path:
        sib = step["hash"]
        side = step["side"]
        if side == "left":
            cur = hash_pair_hex(sib, cur)
        elif side == "right":
            cur = hash_pair_hex(cur, sib)
        else:
            return False
    return cur == expected_root


def load_public_key(pem_path: str | None, raw_b64: str | None) -> Ed25519PublicKey:
    if pem_path:
        with open(pem_path, "rb") as f:
            return serialization.load_pem_public_key(f.read())
    if raw_b64:
        return Ed25519PublicKey.from_public_bytes(base64.b64decode(raw_b64))
    raise SystemExit("error: --public-key or --public-key-b64 required")


def verify_passport(doc: dict, pub: Ed25519PublicKey) -> dict:
    errors: list[str] = []
    envelope = doc.get("envelope")
    sig_b64 = doc.get("signature")
    claims = doc.get("claims") or []
    mode = doc.get("disclosure", "full")

    if not envelope or not sig_b64:
        return {"valid": False, "mode": mode, "errors": ["missing envelope or signature"], "claims": []}

    # 1. Signature Ed25519 sur canonical_json(envelope)
    try:
        sig = base64.b64decode(sig_b64)
        pub.verify(sig, canonical_json(envelope))
    except (InvalidSignature, Exception) as e:
        errors.append("signature_invalid" if isinstance(e, InvalidSignature) else f"signature_decode_error: {e}")

    expected_root = envelope.get("merkle_root")

    if mode == "full":
        if envelope.get("claims_count") != len(claims):
            errors.append("claims_count_mismatch")
        leaves = [claim_leaf_hex(c) for c in claims]
        if not leaves:
            errors.append("no_claims")
        elif merkle_root_from_leaves(leaves) != expected_root:
            errors.append("merkle_root_mismatch")
    else:
        for c in claims:
            if "merkle_path" not in c:
                errors.append(f"claim_{c.get('key')}_missing_path")
                continue
            leaf = claim_leaf_hex(c)
            if not verify_merkle_path(leaf, c["merkle_path"], expected_root):
                errors.append(f"claim_{c.get('key')}_path_invalid")

    return {
        "valid": len(errors) == 0,
        "mode": mode,
        "errors": errors,
        "envelope": envelope,
        "claims": [{"key": c["key"], "value": c["value"]} for c in claims],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="FREK Passport — offline verifier")
    ap.add_argument("--passport", required=True, help="Chemin vers passport.json (full ou partial)")
    ap.add_argument("--public-key", help="Chemin vers cle publique PEM")
    ap.add_argument("--public-key-b64", help="Cle publique raw 32-bytes en base64")
    args = ap.parse_args()

    with open(args.passport, "r", encoding="utf-8") as f:
        doc = json.load(f)
    pub = load_public_key(args.public_key, args.public_key_b64)

    result = verify_passport(doc, pub)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
