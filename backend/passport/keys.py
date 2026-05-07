"""FREK Passport — gestion de la cle Ed25519.

Persiste la cle privee dans /app/backend/.passport_key.pem (hors git).
Genere automatiquement au premier demarrage si absente.
"""
import base64
import os
import logging
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger("frek.passport.keys")

KEY_PATH = Path(os.environ.get("FREK_PASSPORT_KEY_PATH", "/app/backend/.passport_key.pem"))
KEY_ID = os.environ.get("FREK_PASSPORT_KEY_ID", "frek-passport-v1")

_priv: Ed25519PrivateKey | None = None
_pub: Ed25519PublicKey | None = None


def _load_or_generate() -> Ed25519PrivateKey:
    if KEY_PATH.exists():
        with open(KEY_PATH, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    # Genere
    priv = Ed25519PrivateKey.generate()
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KEY_PATH, "wb") as f:
        f.write(pem)
    try:
        os.chmod(KEY_PATH, 0o600)
    except Exception:
        pass
    logger.info(f"FREK Passport — cle Ed25519 generee dans {KEY_PATH}")
    return priv


def get_private_key() -> Ed25519PrivateKey:
    global _priv
    if _priv is None:
        _priv = _load_or_generate()
    return _priv


def get_public_key() -> Ed25519PublicKey:
    global _pub
    if _pub is None:
        _pub = get_private_key().public_key()
    return _pub


def public_key_pem() -> str:
    return get_public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def public_key_raw_b64() -> str:
    raw = get_public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


def sign(message: bytes) -> bytes:
    return get_private_key().sign(message)


def verify(signature: bytes, message: bytes) -> bool:
    from cryptography.exceptions import InvalidSignature
    try:
        get_public_key().verify(signature, message)
        return True
    except InvalidSignature:
        return False
