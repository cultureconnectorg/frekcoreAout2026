"""
FREK Attestation Protocol — Data Types
Reference Implementation v0.1
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FrekProof:
    """Structure d'une preuve FREK (L2). Immutable."""
    magic: int
    version: int
    level: int
    reserved: int
    device_id: bytes          # 16 bytes
    counter: int              # uint64
    nonce: bytes              # 16 bytes
    device_time: str          # ISO 8601, 24 chars max
    audio_hash: bytes         # 32 bytes
    fingerprint_hash: bytes   # 32 bytes
    context_hash: bytes       # 32 bytes
    firmware_hash: bytes      # 32 bytes
    pub_key: bytes            # 33 bytes (P-256 compressed)
    signature: bytes          # 64 bytes (r || s)

    def __post_init__(self):
        assert len(self.device_id) == 16, f"device_id must be 16 bytes, got {len(self.device_id)}"
        assert len(self.nonce) == 16, f"nonce must be 16 bytes, got {len(self.nonce)}"
        assert len(self.audio_hash) == 32
        assert len(self.fingerprint_hash) == 32
        assert len(self.context_hash) == 32
        assert len(self.firmware_hash) == 32
        assert len(self.pub_key) == 33
        assert len(self.signature) == 64
        assert 0 <= self.counter <= 2**64 - 1


@dataclass
class DeviceState:
    """État maintenu par le vérificateur pour un device donné."""
    device_id: bytes
    ak_pub: bytes             # 33 bytes (P-256 compressed)
    last_counter: int
    firmware_version: Optional[str] = None
    status: str = "ACTIVE"    # ACTIVE, REVOKED, SUSPENDED
    trusted_firmware_hashes: Optional[set] = None


@dataclass(frozen=True)
class VerificationResult:
    """Résultat d'une vérification."""
    accepted: bool
    code: str
    message: str
    device_id: Optional[bytes] = None
    counter: Optional[int] = None
    device_time: Optional[str] = None
    verifier_time: Optional[str] = None
    firmware_hash: Optional[str] = None


class FrekError(Exception):
    """Erreur du protocole FREK."""
    pass
