"""
FREK Attestation Protocol — Cryptographic Primitives
Reference Implementation v0.1

Implements:
- SHA-256
- HKDF-SHA-256 (RFC 5869)
- ECDSA P-256 (secp256r1) with raw signatures (r || s, 64 bytes)
- Canonical message encoding for FREK proofs
"""

import hashlib
import hmac
import struct
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    decode_dss_signature,
    encode_dss_signature,
)
from cryptography.exceptions import InvalidSignature

from frek_constants import (
    FREK_DOMAIN,
    SIZE_VERSION,
    SIZE_LEVEL,
    SIZE_DEVICE_ID,
    SIZE_COUNTER,
    SIZE_NONCE,
    SIZE_DEVICE_TIME,
    SIZE_HASH,
    SIZE_PUBKEY_COMPRESSED,
)


def sha256(data: bytes) -> bytes:
    """SHA-256."""
    return hashlib.sha256(data).digest()


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    """HMAC-SHA-256."""
    return hmac.new(key, data, hashlib.sha256).digest()


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """HKDF-Extract per RFC 5869."""
    if salt is None or len(salt) == 0:
        salt = bytes(32)
    return hmac_sha256(salt, ikm)


def hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    """HKDF-Expand per RFC 5869."""
    n = (length + 31) // 32
    if n > 255:
        raise ValueError("HKDF-Expand length too large")
    t = b""
    t_prev = b""
    for i in range(1, n + 1):
        t_prev = hmac_sha256(prk, t_prev + info + bytes([i]))
        t += t_prev
    return t[:length]


def hkdf_sha256(salt: bytes, ikm: bytes, info: bytes, length: int) -> bytes:
    """Full HKDF-SHA-256."""
    prk = hkdf_extract(salt, ikm)
    return hkdf_expand(prk, info, length)


# ── ECDSA P-256 Raw Format ──────────────────────────────────

ECDSA_CURVE = ec.SECP256R1()


def generate_ecdsa_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """Generate a new P-256 keypair."""
    private_key = ec.generate_private_key(ECDSA_CURVE)
    public_key = private_key.public_key()
    return private_key, public_key


def pub_key_to_compressed(pub: ec.EllipticCurvePublicKey) -> bytes:
    """Serialize public key to 33-byte compressed format."""
    return pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )


def pub_key_from_compressed(data: bytes) -> ec.EllipticCurvePublicKey:
    """Deserialize 33-byte compressed public key."""
    return ec.EllipticCurvePublicKey.from_encoded_point(ECDSA_CURVE, data)


def ecdsa_sign_raw(private_key: ec.EllipticCurvePrivateKey, message_hash: bytes) -> bytes:
    """
    Sign a SHA-256 message hash and return raw signature (r || s, 64 bytes).
    """
    signature_der = private_key.sign(message_hash, ec.ECDSA(Prehashed(hashes.SHA256())))
    r, s = decode_dss_signature(signature_der)
    return int_to_bytes_32(r) + int_to_bytes_32(s)


def ecdsa_verify_raw(pub_key: ec.EllipticCurvePublicKey, message_hash: bytes, signature_raw: bytes) -> bool:
    """
    Verify a raw signature (r || s, 64 bytes) against a SHA-256 message hash.
    Returns True if valid, False otherwise.
    """
    if len(signature_raw) != 64:
        return False
    r = int.from_bytes(signature_raw[:32], "big")
    s = int.from_bytes(signature_raw[32:], "big")
    signature_der = encode_dss_signature(r, s)
    try:
        pub_key.verify(signature_der, message_hash, ec.ECDSA(Prehashed(hashes.SHA256())))
        return True
    except InvalidSignature:
        return False


def int_to_bytes_32(x: int) -> bytes:
    """Convert integer to 32-byte big-endian, padding with zeros."""
    return x.to_bytes(32, "big")


# ── Device ID Derivation ─────────────────────────────────────

def derive_device_id(ak_pub: bytes) -> bytes:
    """
    DEVICE_ID = Truncate(SHA-256(AK_pub), 16)
    """
    return sha256(ak_pub)[:16]


# ── Canonical Message Encoding ─────────────────────────────────

def encode_canonical_message(
    version: int,
    level: int,
    device_id: bytes,
    counter: int,
    nonce: bytes,
    device_time: str,
    audio_hash: bytes,
    fingerprint_hash: bytes,
    context_hash: bytes,
    firmware_hash: bytes,
    pub_key: bytes,
) -> bytes:
    """
    Encode the canonical message for signing/verification.

    MESSAGE = SHA-256(
        DOMAIN ||
        VERSION ||
        LEVEL ||
        DEVICE_ID ||
        COUNTER ||
        NONCE ||
        DEVICE_TIME ||
        AUDIO_HASH ||
        FINGERPRINT_HASH ||
        CONTEXT_HASH ||
        FIRMWARE_HASH ||
        AK_PUB
    )

    All multi-byte integers are big-endian.
    DEVICE_TIME is UTF-8 encoded and padded/truncated to exactly 24 bytes.
    """
    # Pad/truncate device_time to exactly 24 bytes
    time_bytes = device_time.encode("utf-8")
    if len(time_bytes) < SIZE_DEVICE_TIME:
        time_bytes = time_bytes + b"\x00" * (SIZE_DEVICE_TIME - len(time_bytes))
    else:
        time_bytes = time_bytes[:SIZE_DEVICE_TIME]

    msg = (
        FREK_DOMAIN +
        struct.pack(">B", version) +
        struct.pack(">B", level) +
        device_id +
        struct.pack(">Q", counter) +
        nonce +
        time_bytes +
        audio_hash +
        fingerprint_hash +
        context_hash +
        firmware_hash +
        pub_key
    )
    return sha256(msg)


# Need serialization import for compressed point
from cryptography.hazmat.primitives import serialization
