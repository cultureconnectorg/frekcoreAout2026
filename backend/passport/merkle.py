"""FREK Passport — Merkle tree pour disclosure selective.

Chaque claim devient une feuille hashee :
    leaf = SHA256( canonical_json({"key", "value", "nonce"}) )

L'arbre est binaire ; les feuilles impaires sont dupliquees a droite.
Une preuve de disclosure = liste de (sibling_hash, side) du leaf vers la racine.

Verification offline : recompute leaf, fold avec siblings, compare a merkle_root.
"""
import hashlib
import json
import os
from typing import Any


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def claim_leaf_hex(key: str, value: Any, nonce: str) -> str:
    return sha256_hex(canonical_json({"key": key, "nonce": nonce, "value": value}))


def gen_nonce_hex() -> str:
    return os.urandom(16).hex()


def _hash_pair_hex(left: str, right: str) -> str:
    return sha256_hex(bytes.fromhex(left) + bytes.fromhex(right))


def build_tree(leaves_hex: list[str]) -> list[list[str]]:
    """Retourne tous les niveaux [feuilles, ..., racine].
    Feuille seule => racine = la feuille.
    """
    if not leaves_hex:
        raise ValueError("merkle: empty leaves")
    levels = [list(leaves_hex)]
    while len(levels[-1]) > 1:
        cur = levels[-1]
        nxt: list[str] = []
        i = 0
        while i < len(cur):
            l = cur[i]
            r = cur[i + 1] if i + 1 < len(cur) else cur[i]  # duplicate last if odd
            nxt.append(_hash_pair_hex(l, r))
            i += 2
        levels.append(nxt)
    return levels


def merkle_root(leaves_hex: list[str]) -> str:
    return build_tree(leaves_hex)[-1][0]


def merkle_path(leaves_hex: list[str], index: int) -> list[dict]:
    """Retourne la liste des siblings (hex, side='left'|'right') de bas en haut."""
    levels = build_tree(leaves_hex)
    path: list[dict] = []
    idx = index
    for level in levels[:-1]:
        if idx % 2 == 0:
            sib_idx = idx + 1 if idx + 1 < len(level) else idx  # duplicate for odd
            path.append({"hash": level[sib_idx], "side": "right"})
        else:
            path.append({"hash": level[idx - 1], "side": "left"})
        idx //= 2
    return path


def verify_path(leaf_hex: str, path: list[dict], expected_root: str) -> bool:
    cur = leaf_hex
    for step in path:
        sib = step["hash"]
        side = step["side"]
        if side == "left":
            cur = _hash_pair_hex(sib, cur)
        elif side == "right":
            cur = _hash_pair_hex(cur, sib)
        else:
            return False
    return cur == expected_root
