"""
FREK Attestation Protocol — Simulated FREK V3 Device
Reference Implementation v0.1

This module simulates a FREK V3 device for testing purposes.
It generates valid FREK proofs using ECDSA P-256.

In a real device:
- The private key would be derived from a PUF inside the Trust Domain
- The signing would happen in hardware
- The counter would be stored in NVM

Here, we simulate the same behavior with software keys for test vector generation.
"""

import secrets
import struct
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec

from frek_constants import (
    FREK_MAGIC,
    FREK_VERSION,
    LEVEL_L2_HARDWARE,
    SIZE_NONCE,
    SIZE_DEVICE_TIME,
)
from frek_types import FrekProof
from frek_crypto import (
    generate_ecdsa_keypair,
    pub_key_to_compressed,
    sha256,
    ecdsa_sign_raw,
    encode_canonical_message,
    derive_device_id,
)
from frek_parser import serialize_proof


class SimulatedFrekDevice:
    """Simulates a FREK V3 device for generating test proofs."""

    def __init__(self, firmware_hash: Optional[bytes] = None):
        # Generate device keypair (in real hardware: derived from PUF)
        self._private_key, self._public_key = generate_ecdsa_keypair()
        self.ak_pub = pub_key_to_compressed(self._public_key)
        self.device_id = derive_device_id(self.ak_pub)

        # Device state
        self.counter = 0
        self.firmware_hash = firmware_hash or sha256(b"frek_v3_fw_v1.0.0")

        # RTC simulation (starts at current time)
        self._base_time = datetime.now(timezone.utc)

    def get_identity(self) -> dict:
        """Return device identity (equivalent to GET_IDENTITY command)."""
        return {
            "device_id": self.device_id,
            "ak_pub": self.ak_pub,
            "firmware_hash": self.firmware_hash,
            "protocol_version": FREK_VERSION,
        }

    def generate_proof(
        self,
        audio_buffer: bytes,
        fingerprint_vector: bytes,
        context_metadata: bytes,
        nonce: Optional[bytes] = None,
    ) -> bytes:
        """
        Generate a FREK L2 proof.

        Args:
            audio_buffer: Raw audio data (simulated)
            fingerprint_vector: Extracted fingerprint features
            context_metadata: Contextual metadata JSON/bytes
            nonce: External nonce for challenge-response mode.
                   If None, generates internal nonce (autonomous mode).
        """
        # Increment counter (simulates NVM counter)
        self.counter += 1

        # Generate or use nonce
        if nonce is None:
            nonce = secrets.token_bytes(SIZE_NONCE)

        # Compute hashes
        audio_hash = sha256(audio_buffer)
        fingerprint_hash = sha256(fingerprint_vector)
        context_hash = sha256(context_metadata)

        # Device time
        device_time = datetime.now(timezone.utc).isoformat()

        # Build proof structure (without signature)
        proof = FrekProof(
            magic=FREK_MAGIC,
            version=FREK_VERSION,
            level=LEVEL_L2_HARDWARE,
            reserved=0x00,
            device_id=self.device_id,
            counter=self.counter,
            nonce=nonce,
            device_time=device_time,
            audio_hash=audio_hash,
            fingerprint_hash=fingerprint_hash,
            context_hash=context_hash,
            firmware_hash=self.firmware_hash,
            pub_key=self.ak_pub,
            signature=b"\x00" * 64,  # placeholder
        )

        # Compute canonical message hash
        message_hash = encode_canonical_message(
            version=proof.version,
            level=proof.level,
            device_id=proof.device_id,
            counter=proof.counter,
            nonce=proof.nonce,
            device_time=proof.device_time,
            audio_hash=proof.audio_hash,
            fingerprint_hash=proof.fingerprint_hash,
            context_hash=proof.context_hash,
            firmware_hash=proof.firmware_hash,
            pub_key=proof.pub_key,
        )

        # Sign with private key (in real hardware: AK inside Trust Domain)
        signature = ecdsa_sign_raw(self._private_key, message_hash)

        # Return complete proof with signature
        proof_with_sig = FrekProof(
            magic=proof.magic,
            version=proof.version,
            level=proof.level,
            reserved=proof.reserved,
            device_id=proof.device_id,
            counter=proof.counter,
            nonce=proof.nonce,
            device_time=proof.device_time,
            audio_hash=proof.audio_hash,
            fingerprint_hash=proof.fingerprint_hash,
            context_hash=proof.context_hash,
            firmware_hash=proof.firmware_hash,
            pub_key=proof.pub_key,
            signature=signature,
        )

        return serialize_proof(proof_with_sig)
