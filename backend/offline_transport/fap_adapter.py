"""D4 -- FAP (FREK Attestation Protocol) device-attestation reuse.

`frek_v3/reference_verifier/` is a real, complete, independently tested
reference implementation (see models.py's module docstring). This file
is the first thing in `backend/` that actually calls it
(`docs/architecture/FAP_PROOF_ENGINE_RECONCILIATION.md` confirmed it was
otherwise fully isolated). It reuses FAP's own parser, canonical message
encoding, and ECDSA verification pipeline verbatim -- nothing
cryptographic is reimplemented here.

`frek_v3/reference_verifier/`'s own modules use bare, non-relative
imports (confirmed by reading them) and are consumed by their own test
suite the same way: with the package directory itself on `sys.path`.
`_ensure_fap_importable()` follows that exact, already-established
consumption pattern -- a scoped, idempotent `sys.path` insert, not a new
packaging scheme invented for this module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

_FAP_DIR = Path(__file__).resolve().parents[2] / "frek_v3" / "reference_verifier"


def _ensure_fap_importable() -> None:
    path_str = str(_FAP_DIR)
    if _FAP_DIR.is_dir() and path_str not in sys.path:
        sys.path.insert(0, path_str)


def verify_fap_proof(proof_hex: str, known_devices: Dict[str, dict]) -> Dict[str, Any]:
    """Verifies a raw FAP L2 proof against a set of known devices,
    reusing FAP's own real `FrekVerifier` end to end.

    `known_devices` is `{device_id_hex: {"ak_pub_hex": ..., "status":
    ..., "last_counter": ..., "trusted_firmware_hashes_hex": [...]}}` --
    the caller (routes.py) is responsible for loading this from durable
    storage (`db.fap_devices`) and persisting the updated
    `last_counter` back; this function stays pure I/O-wise beyond the
    verification call itself, matching the reference verifier's own
    design (it takes a `DeviceRegistry` object, never touches a
    database).

    Returns a plain dict (never FAP's own dataclass, so callers never
    need to import frek_v3 types themselves) with at least `accepted`,
    `code`, `message`, and -- on success -- `device_id_hex`, `counter`,
    `device_time`, `verifier_time`.
    """
    _ensure_fap_importable()
    import frek_registry  # type: ignore  # noqa: E402
    import frek_verifier  # type: ignore  # noqa: E402

    try:
        proof_bytes = bytes.fromhex(proof_hex)
    except ValueError:
        return {
            "accepted": False,
            "code": "MALFORMED",
            "message": "proof_hex is not valid hex",
        }

    registry = frek_registry.DeviceRegistry()
    for device_id_hex, info in known_devices.items():
        firmware_hashes = info.get("trusted_firmware_hashes_hex")
        registry.register(
            device_id=bytes.fromhex(device_id_hex),
            ak_pub=bytes.fromhex(info["ak_pub_hex"]),
            trusted_firmware_hashes=(
                {bytes.fromhex(h) for h in firmware_hashes} if firmware_hashes else None
            ),
        )
        state = registry.get(bytes.fromhex(device_id_hex))
        if state is not None:
            state.status = info.get("status", "ACTIVE")
            state.last_counter = info.get("last_counter", 0)

    verifier = frek_verifier.FrekVerifier(registry)
    result = verifier.verify(proof_bytes)

    out: Dict[str, Any] = {
        "accepted": result.accepted,
        "code": result.code,
        "message": result.message,
    }
    if result.device_id is not None:
        out["device_id_hex"] = result.device_id.hex()
    if result.counter is not None:
        out["counter"] = result.counter
    if result.device_time is not None:
        out["device_time"] = result.device_time
    if result.verifier_time is not None:
        out["verifier_time"] = result.verifier_time
    return out


def generate_test_proof(
    *,
    audio_buffer: bytes = b"test-audio",
    fingerprint_vector: bytes = b"test-fingerprint",
    context_metadata: bytes = b"{}",
) -> Optional[Dict[str, Any]]:
    """Test/dev helper only: generates one real, validly-signed FAP
    proof via FAP's own `SimulatedFrekDevice` (the reference
    implementation's own test-vector generator -- never a second,
    lookalike signer). Returns None if `frek_v3/` is not present in
    this checkout. Used by this module's own test suite to exercise
    `verify_fap_proof` against a genuine proof, not a hand-rolled stub.
    """
    _ensure_fap_importable()
    if not _FAP_DIR.is_dir():
        return None
    import frek_device_sim  # type: ignore  # noqa: E402

    device = frek_device_sim.SimulatedFrekDevice()
    identity = device.get_identity()
    proof_bytes = device.generate_proof(
        audio_buffer, fingerprint_vector, context_metadata
    )
    return {
        "proof_hex": proof_bytes.hex(),
        "device_id_hex": identity["device_id"].hex(),
        "ak_pub_hex": identity["ak_pub"].hex(),
        "firmware_hash_hex": identity["firmware_hash"].hex(),
    }
