"""FREK DID — encodages W3C standards.

- multibase 'z' = base58btc (W3C Multibase)
- multikey ed25519-pub : prefixe varint 0xed01 + 32 bytes raw
"""
import base58
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


# Ed25519 public key multicodec prefix : 0xed 0x01 (varint encoded)
ED25519_PUB_MULTICODEC = bytes([0xed, 0x01])


def public_key_multibase(pub: Ed25519PublicKey) -> str:
    """Retourne la cle publique en format multibase base58btc avec multicodec ed25519-pub.

    Format : "z" + base58btc(0xed01 || raw_pubkey_32bytes)
    Compatible W3C VC Data Integrity 1.0 cryptosuite eddsa-jcs-2022.
    """
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    multicodec = ED25519_PUB_MULTICODEC + raw
    return "z" + base58.b58encode(multicodec).decode("ascii")


def signature_multibase(signature: bytes) -> str:
    """Encode une signature Ed25519 en multibase base58btc (proofValue VC)."""
    return "z" + base58.b58encode(signature).decode("ascii")


def decode_multibase_b58btc(s: str) -> bytes:
    """Decode 'z...' multibase. Leve ValueError si autre prefix."""
    if not s or s[0] != "z":
        raise ValueError(f"unsupported multibase prefix in: {s[:5]}")
    return base58.b58decode(s[1:])
