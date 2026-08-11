"""
FREK Attestation Protocol — Reference Verifier
Reference Implementation v0.1

Implements the full verification pipeline:
  FREK Proof → Parser → Structural Validation → Device Lookup →
  Signature Verification → Counter Check → Nonce Check →
  Firmware Check → ACCEPT / REJECT

Separation of concerns:
  - Cryptographic validity (signature, hashes) → deterministic
  - Policy acceptability (counter, nonce, firmware, status) → stateful
"""

from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec

from frek_constants import (
    FREK_MAGIC,
    FREK_VERSION,
    LEVEL_L2_HARDWARE,
    MAX_COUNTER_WINDOW,
)
from frek_types import FrekProof, DeviceState, VerificationResult
from frek_crypto import (
    pub_key_from_compressed,
    ecdsa_verify_raw,
    encode_canonical_message,
    derive_device_id,
)
from frek_parser import parse_proof
from frek_registry import DeviceRegistry


class FrekVerifier:
    """Reference verifier for FREK Attestation Protocol."""

    def __init__(self, registry: DeviceRegistry):
        self.registry = registry

    def verify(
        self,
        proof_bytes: bytes,
        expected_nonce: Optional[bytes] = None,
    ) -> VerificationResult:
        """
        Verify a FREK Proof.

        Args:
            proof_bytes: Raw binary proof (283 bytes for L2)
            expected_nonce: Nonce expected for challenge-response mode.
                            If None, nonce uniqueness is not checked (autonomous mode).

        Returns:
            VerificationResult with accepted=True/False and detailed code.
        """
        verifier_time = datetime.now(timezone.utc).isoformat()

        # ── Step 1: Parse ─────────────────────────────────────
        try:
            proof = parse_proof(proof_bytes)
        except Exception as e:
            return VerificationResult(
                accepted=False,
                code="MALFORMED",
                message=f"Failed to parse proof: {e}",
                verifier_time=verifier_time,
            )

        # ── Step 2: Structural Validation ────────────────────────
        if proof.magic != FREK_MAGIC:
            return self._reject("MALFORMED", "Invalid MAGIC", proof, verifier_time)

        if proof.version != FREK_VERSION:
            return self._reject(
                "UNSUPPORTED_VERSION",
                f"Version {proof.version} not supported (expected {FREK_VERSION})",
                proof, verifier_time,
            )

        if proof.level != LEVEL_L2_HARDWARE:
            return self._reject(
                "LEVEL_NOT_SUPPORTED",
                f"Level {proof.level} not supported by this verifier",
                proof, verifier_time,
            )

        if proof.reserved != 0x00:
            return self._reject("MALFORMED", "Reserved field must be 0x00", proof, verifier_time)

        # ── Step 3: Device Identity Check ────────────────────────
        # Verify that DEVICE_ID matches AK_pub
        computed_device_id = derive_device_id(proof.pub_key)
        if computed_device_id != proof.device_id:
            return self._reject(
                "IDENTITY_MISMATCH",
                "DEVICE_ID does not match derived ID from AK_pub",
                proof, verifier_time,
            )

        # ── Step 4: Registry Lookup ────────────────────────────
        device_state = self.registry.get(proof.device_id)
        if device_state is None:
            return self._reject(
                "UNKNOWN_DEVICE",
                "Device not registered",
                proof, verifier_time,
            )

        if device_state.status == "REVOKED":
            return self._reject(
                "DEVICE_REVOKED",
                "Device has been revoked",
                proof, verifier_time,
            )

        if device_state.status == "SUSPENDED":
            return self._reject(
                "DEVICE_SUSPENDED",
                "Device is suspended",
                proof, verifier_time,
            )

        # ── Step 5: AK_pub Consistency ───────────────────────────
        if device_state.ak_pub != proof.pub_key:
            return self._reject(
                "IDENTITY_MISMATCH",
                "AK_pub in proof does not match registered AK_pub",
                proof, verifier_time,
            )

        # ── Step 6: Cryptographic Signature Verification ─────────
        try:
            pub_key = pub_key_from_compressed(proof.pub_key)
        except Exception as e:
            return self._reject(
                "INVALID_PUBKEY",
                f"Failed to parse public key: {e}",
                proof, verifier_time,
            )

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

        if not ecdsa_verify_raw(pub_key, message_hash, proof.signature):
            return self._reject(
                "INVALID_SIGNATURE",
                "ECDSA signature verification failed",
                proof, verifier_time,
            )

        # ── Step 7: Counter / Replay Check ──────────────────────
        if proof.counter <= device_state.last_counter:
            return self._reject(
                "REPLAY",
                f"Counter {proof.counter} <= last known {device_state.last_counter}",
                proof, verifier_time,
            )

        if proof.counter > device_state.last_counter + MAX_COUNTER_WINDOW:
            return self._reject(
                "COUNTER_GAP_TOO_LARGE",
                f"Counter gap {proof.counter - device_state.last_counter} exceeds max {MAX_COUNTER_WINDOW}",
                proof, verifier_time,
            )

        # ── Step 8: Nonce Check ────────────────────────────────
        if expected_nonce is not None:
            if proof.nonce != expected_nonce:
                return self._reject(
                    "NONCE_MISMATCH",
                    "Nonce does not match expected value",
                    proof, verifier_time,
                )

        # ── Step 9: Firmware Check (optional policy) ───────────
        if device_state.trusted_firmware_hashes is not None:
            if proof.firmware_hash not in device_state.trusted_firmware_hashes:
                return self._reject(
                    "FIRMWARE_REJECTED",
                    "Firmware hash not in trusted whitelist",
                    proof, verifier_time,
                )

        # ── Step 10: ACCEPT ─────────────────────────────────────
        # Update state
        self.registry.update_counter(proof.device_id, proof.counter)

        return VerificationResult(
            accepted=True,
            code="ACCEPT",
            message="Proof is cryptographically valid and policy-compliant",
            device_id=proof.device_id,
            counter=proof.counter,
            device_time=proof.device_time,
            verifier_time=verifier_time,
            firmware_hash=proof.firmware_hash.hex(),
        )

    def _reject(
        self,
        code: str,
        message: str,
        proof: FrekProof,
        verifier_time: str,
    ) -> VerificationResult:
        """Helper to construct a rejection result."""
        return VerificationResult(
            accepted=False,
            code=code,
            message=message,
            device_id=proof.device_id,
            counter=proof.counter,
            device_time=proof.device_time,
            verifier_time=verifier_time,
            firmware_hash=proof.firmware_hash.hex() if proof.firmware_hash else None,
        )
