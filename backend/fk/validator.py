"""FK Validator — verification OFFLINE d'un .fk.

Le validateur ne depend d'aucune DB ni service externe. Il ouvre le ZIP,
recalcule tous les hashes, verifie la signature Ed25519 avec la cle publique
embarquee, et retourne un rapport de validation exhaustif.

Test de survie fondamental : un .fk valide sur une machine, doit rester valide
sur toute autre machine, sans acces au serveur FREKCORE d'origine.
"""
import base64
import io
import json
import logging
import zipfile
from typing import Dict, Any, List, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .packager import sha256_hex, sha256_of_json, canonical_json

logger = logging.getLogger("frek.fk.validator")


REQUIRED_ENTRIES = [
    "manifest.fk.json",
    "metadata/identity.json",
    "metadata/creators.json",
    "metadata/timeline.json",
    "media/media.json",
    "intelligence/intelligence.json",
    "rights/ownership.json",
    "proof/frekcore-attestation.json",
]

LAYER_FILES = {
    "manifest": "manifest.fk.json",
    "identity": "metadata/identity.json",
    "creators": "metadata/creators.json",
    "timeline": "metadata/timeline.json",
    "media": "media/media.json",
    "intelligence": "intelligence/intelligence.json",
    "rights": "rights/ownership.json",
}


def _load_layer(zf: zipfile.ZipFile, path: str) -> Dict[str, Any]:
    return json.loads(zf.read(path).decode("utf-8"))


def _load_pubkey(pem_str: str) -> Ed25519PublicKey:
    return serialization.load_pem_public_key(pem_str.encode("ascii"))


def validate_fk(fk_bytes: bytes) -> Dict[str, Any]:
    """Verifie un .fk offline. Retourne un rapport complet."""
    report: Dict[str, Any] = {
        "valid": False,
        "checks": [],
        "frek_id": None,
        "title": None,
        "object_type": None,
        "created_at": None,
        "creator": None,
        "media_count": 0,
        "signature_algo": None,
        "public_key_raw_b64": None,
        "block_hash": None,
        "errors": [],
    }

    def _check(name: str, ok: bool, detail: str = ""):
        report["checks"].append({"check": name, "ok": ok, "detail": detail})
        if not ok:
            report["errors"].append(f"{name}: {detail}")

    # 1. ZIP valide
    try:
        zf = zipfile.ZipFile(io.BytesIO(fk_bytes), "r")
        _check("zip_valid", True)
    except zipfile.BadZipFile as e:
        _check("zip_valid", False, str(e))
        return report

    # 2. Entrees obligatoires
    names = set(zf.namelist())
    missing = [e for e in REQUIRED_ENTRIES if e not in names]
    _check("required_entries", len(missing) == 0,
           f"manquants: {missing}" if missing else "toutes presentes")
    if missing:
        return report

    # 3. Load layers
    try:
        layers = {k: _load_layer(zf, p) for k, p in LAYER_FILES.items()}
        proof = _load_layer(zf, "proof/frekcore-attestation.json")
        _check("layers_parseable", True)
    except Exception as e:
        _check("layers_parseable", False, str(e))
        return report

    report["frek_id"] = layers["identity"].get("frek_id")
    report["title"] = layers["identity"].get("title")
    report["object_type"] = layers["identity"].get("object_type")
    report["created_at"] = layers["manifest"].get("created_at")
    report["creator"] = (layers["creators"].get("primary_creator") or {}).get("name")
    report["media_count"] = len(layers["media"].get("items") or [])
    report["signature_algo"] = proof.get("signature_algo")
    report["public_key_raw_b64"] = proof.get("public_key_raw_b64")
    report["block_hash"] = (proof.get("block") or {}).get("block_hash") if proof.get("block") else None

    # 4. Coherence FREK-ID entre couches
    fid = layers["manifest"].get("frek_id")
    ids = {
        "manifest": fid,
        "identity": layers["identity"].get("frek_id"),
        "proof": proof.get("frek_id"),
    }
    _check("frek_id_consistent", len(set(ids.values())) == 1, f"ids={ids}")

    # 5. Hashes des couches recalcules
    computed_hashes = {
        name: sha256_of_json(obj) for name, obj in layers.items()
    }
    stored_hashes = proof.get("layer_hashes") or {}
    for name in LAYER_FILES.keys():
        stored = stored_hashes.get(name)
        computed = computed_hashes.get(name)
        _check(f"layer_hash_{name}",
               stored == computed,
               f"stored={stored}, computed={computed}" if stored != computed else "ok")

    # 6. Root hash recalcule
    computed_root = sha256_of_json(stored_hashes)
    _check("root_hash",
           computed_root == proof.get("root_hash"),
           f"stored={proof.get('root_hash')}, computed={computed_root}")

    # 7. Signature Ed25519
    try:
        pub_pem = proof.get("public_key_pem", "")
        signature_b64 = proof.get("signature", "")
        pubkey = _load_pubkey(pub_pem)
        sig = base64.b64decode(signature_b64)
        pubkey.verify(sig, proof["root_hash"].encode("utf-8"))
        _check("signature_valid", True, "Ed25519 OK")
    except InvalidSignature:
        _check("signature_valid", False, "signature Ed25519 invalide")
    except Exception as e:
        _check("signature_valid", False, f"erreur signature: {e}")

    # 8. Media binaires : chaque item declare est present et hash matche
    media_ok = True
    media_details: List[str] = []
    for item in layers["media"].get("items") or []:
        path = item.get("path")
        expected_sha = item.get("sha256")
        expected_size = item.get("size")
        if path not in names:
            media_ok = False
            media_details.append(f"{path}: absent du ZIP")
            continue
        data = zf.read(path)
        if len(data) != expected_size:
            media_ok = False
            media_details.append(f"{path}: taille {len(data)} != {expected_size}")
        elif sha256_hex(data) != expected_sha:
            media_ok = False
            media_details.append(f"{path}: hash SHA-256 mismatch")
    _check("media_integrity", media_ok,
           "; ".join(media_details) if media_details else "tous les medias OK")

    zf.close()

    # Verdict final : toutes les checks doivent etre OK
    report["valid"] = all(c["ok"] for c in report["checks"])
    return report


def summary(report: Dict[str, Any]) -> str:
    """Resume texte compact pour affichage."""
    if report["valid"]:
        return (
            f"OK — FK '{report['title']}' ({report['frek_id']}) "
            f"signe par {report['creator']} — {report['media_count']} media(s)"
        )
    return f"INVALIDE — {'; '.join(report['errors'][:3])}"
