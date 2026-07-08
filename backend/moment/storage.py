"""
FREKCORE Moment — Object Storage wrapper.

Stockage optionnel des medias signes. Uploadable depuis /moment/sign-media
quand l'utilisateur choisit "Signer et conserver". La preuve cryptographique
(hash SHA-256) reste independante du binaire : le media peut disparaitre
sans casser la preuve.

Doctrine :
- Le hash est signe. Le fichier binaire est optionnel.
- Aucune donnee sensible dans le path (pas d'email, pas d'IP).
- App-prefix "frekcore" pour eviter les collisions de bucket.
"""
import os
import hashlib
import logging
from typing import Optional, Tuple

import requests

logger = logging.getLogger("frek.moment.storage")

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "frekcore"

_storage_key: Optional[str] = None


def init_storage() -> Optional[str]:
    """Initialise la cle de session Object Storage. Idempotent.

    Retourne None si EMERGENT_LLM_KEY est absent (mode degrade : signature
    reste possible, mais aucun upload ne fonctionnera).
    """
    global _storage_key
    if _storage_key:
        return _storage_key

    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        logger.warning("EMERGENT_LLM_KEY absent — Object Storage desactive.")
        return None

    try:
        resp = requests.post(
            f"{STORAGE_URL}/init",
            json={"emergent_key": emergent_key},
            timeout=30,
        )
        resp.raise_for_status()
        _storage_key = resp.json()["storage_key"]
        logger.info("FREK Moment Object Storage — session initialisee")
        return _storage_key
    except Exception as e:
        logger.error(f"Object Storage init failed: {e}")
        return None


def is_available() -> bool:
    """True si le stockage est operationnel."""
    return init_storage() is not None


def sha256_bytes(data: bytes) -> str:
    """SHA-256 hex d'un blob binaire."""
    return hashlib.sha256(data).hexdigest()


def build_path(frek_id: str, ext: str) -> str:
    """Construit un path deterministe base sur le frek_id.

    Format: frekcore/moments/{frek_id}.{ext}
    """
    safe_ext = ext.lower().lstrip(".")[:6] or "bin"
    return f"{APP_NAME}/moments/{frek_id}.{safe_ext}"


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload un blob. Retourne {"path": "...", "size": N, "etag": "..."}.
    Leve une exception si le stockage est indisponible.
    """
    key = init_storage()
    if not key:
        raise RuntimeError("Object Storage indisponible")

    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str) -> Tuple[bytes, str]:
    """Recupere un blob. Retourne (bytes, content_type)."""
    key = init_storage()
    if not key:
        raise RuntimeError("Object Storage indisponible")

    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


# Limites v1
MAX_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
ALLOWED_MIME = {
    # Photos
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    # Audio
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/aac": "aac",
    "audio/flac": "flac",
}


def validate_media(content_type: str, size: int) -> Tuple[bool, str]:
    """Verifie taille + type. Retourne (ok, reason_if_not)."""
    if size > MAX_SIZE_BYTES:
        return False, f"Fichier trop lourd ({size} octets, max {MAX_SIZE_BYTES})"
    if content_type not in ALLOWED_MIME:
        return False, f"Type non supporte : {content_type}"
    return True, ""


def extension_for(content_type: str) -> str:
    return ALLOWED_MIME.get(content_type, "bin")


def media_kind(content_type: str) -> str:
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("audio/"):
        return "audio"
    return "unknown"
