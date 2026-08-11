"""
FREK Attestation Protocol — Golden Test Vectors
Reference Implementation v0.1

Test suite SANS dépendance externe (pas de pytest requis).
"""

import secrets
import traceback
from frek_constants import FREK_MAGIC, FREK_VERSION, LEVEL_L2_HARDWARE
from frek_crypto import sha256, derive_device_id
from frek_parser import parse_proof, serialize_proof
from frek_registry import DeviceRegistry
from frek_verifier import FrekVerifier
from frek_device_sim import SimulatedFrekDevice


# ── Helpers ─────────────────────────────────────────────────

def make_registry_and_device():
    device = SimulatedFrekDevice()
    identity = device.get_identity()
    registry = DeviceRegistry()
    registry.register(
        device_id=identity["device_id"],
        ak_pub=identity["ak_pub"],
        trusted_firmware_hashes={identity["firmware_hash"]},
    )
    return registry, device


def make_proof(device, nonce=None):
    if nonce is None:
        nonce = secrets.token_bytes(16)
    audio = b"test_audio_48kHz_mono_2048samples"
    fingerprint = b"test_fingerprint_mfcc_13bands"
    context = b'{\"location\":\"Studio_A\",\"gain\":12.5}'
    return device.generate_proof(audio, fingerprint, context, nonce=nonce), nonce


def flip_byte(data, offset):
    modified = bytearray(data)
    modified[offset] ^= 0x01
    return bytes(modified)


# ── Tests ───────────────────────────────────────────────────

def test_valid_proof():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    result = verifier.verify(proof, expected_nonce=nonce)
    assert result.accepted is True, f"Expected ACCEPT, got {result.code}: {result.message}"
    assert result.code == "ACCEPT"
    print("  ✅ test_valid_proof")


def test_signature_modified():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    modified = flip_byte(proof, 229)
    result = verifier.verify(modified, expected_nonce=nonce)
    assert result.accepted is False and result.code == "INVALID_SIGNATURE"
    print("  ✅ test_signature_modified")


def test_audio_hash_modified():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    modified = flip_byte(proof, 68)
    result = verifier.verify(modified, expected_nonce=nonce)
    assert result.accepted is False and result.code == "INVALID_SIGNATURE"
    print("  ✅ test_audio_hash_modified")


def test_nonce_mismatch():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, _ = make_proof(device)

    wrong_nonce = secrets.token_bytes(16)
    result = verifier.verify(proof, expected_nonce=wrong_nonce)
    assert result.accepted is False and result.code == "NONCE_MISMATCH"
    print("  ✅ test_nonce_mismatch")


def test_replay_same_counter():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    result1 = verifier.verify(proof, expected_nonce=nonce)
    assert result1.accepted is True

    result2 = verifier.verify(proof, expected_nonce=nonce)
    assert result2.accepted is False and result2.code == "REPLAY"
    print("  ✅ test_replay_same_counter")


def test_replay_older_counter():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof1, nonce1 = make_proof(device)

    result1 = verifier.verify(proof1, expected_nonce=nonce1)
    assert result1.accepted is True

    proof2, nonce2 = make_proof(device)
    result2 = verifier.verify(proof2, expected_nonce=nonce2)
    assert result2.accepted is True

    result3 = verifier.verify(proof1, expected_nonce=nonce1)
    assert result3.accepted is False and result3.code == "REPLAY"
    print("  ✅ test_replay_older_counter")


def test_unknown_device():
    registry = DeviceRegistry()
    verifier = FrekVerifier(registry)
    device = SimulatedFrekDevice()
    nonce = secrets.token_bytes(16)
    proof = device.generate_proof(b"x", b"y", b"z", nonce=nonce)

    result = verifier.verify(proof, expected_nonce=nonce)
    assert result.accepted is False and result.code == "UNKNOWN_DEVICE"
    print("  ✅ test_unknown_device")


def test_identity_mismatch():
    registry = DeviceRegistry()
    device1 = SimulatedFrekDevice()
    identity1 = device1.get_identity()
    registry.register(device_id=identity1["device_id"], ak_pub=identity1["ak_pub"])

    device2 = SimulatedFrekDevice()
    nonce = secrets.token_bytes(16)
    proof2 = device2.generate_proof(b"x", b"y", b"z", nonce=nonce)

    modified = bytearray(proof2)
    modified[4:20] = device1.device_id

    verifier = FrekVerifier(registry)
    result = verifier.verify(bytes(modified), expected_nonce=nonce)
    assert result.accepted is False and result.code == "IDENTITY_MISMATCH"
    print("  ✅ test_identity_mismatch")


def test_firmware_rejected():
    registry = DeviceRegistry()
    device = SimulatedFrekDevice()
    identity = device.get_identity()
    registry.register(
        device_id=identity["device_id"],
        ak_pub=identity["ak_pub"],
        trusted_firmware_hashes={sha256(b"other_firmware")},
    )

    nonce = secrets.token_bytes(16)
    proof = device.generate_proof(b"x", b"y", b"z", nonce=nonce)

    verifier = FrekVerifier(registry)
    result = verifier.verify(proof, expected_nonce=nonce)
    assert result.accepted is False and result.code == "FIRMWARE_REJECTED"
    print("  ✅ test_firmware_rejected")


def test_bad_magic():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    modified = flip_byte(proof, 0)
    result = verifier.verify(modified, expected_nonce=nonce)
    assert result.accepted is False and result.code == "MALFORMED"
    print("  ✅ test_bad_magic")


def test_unsupported_version():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    modified = flip_byte(proof, 1)
    result = verifier.verify(modified, expected_nonce=nonce)
    assert result.accepted is False and result.code in ("UNSUPPORTED_VERSION", "INVALID_SIGNATURE")
    print("  ✅ test_unsupported_version")


def test_truncated_proof():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    truncated = proof[:200]
    result = verifier.verify(truncated, expected_nonce=nonce)
    assert result.accepted is False and result.code == "MALFORMED"
    print("  ✅ test_truncated_proof")


def test_bitflip_all_fields():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    fields = [
        ("VERSION", 1, 1),
        ("LEVEL", 2, 1),
        ("DEVICE_ID", 4, 16),
        ("COUNTER", 20, 8),
        ("NONCE", 28, 16),
        ("DEVICE_TIME", 44, 24),
        ("AUDIO_HASH", 68, 32),
        ("FINGERPRINT_HASH", 100, 32),
        ("CONTEXT_HASH", 132, 32),
        ("FIRMWARE_HASH", 164, 32),
        ("PUB_KEY", 196, 33),
    ]

    for name, offset, length in fields:
        modified = flip_byte(proof, offset)
        result = verifier.verify(modified, expected_nonce=nonce)
        assert result.accepted is False, f"Bit-flip on {name} should fail, got {result.code}"

    print("  ✅ test_bitflip_all_fields (11 fields)")


def test_counter_window():
    registry = DeviceRegistry()
    device = SimulatedFrekDevice()
    identity = device.get_identity()
    registry.register(device_id=identity["device_id"], ak_pub=identity["ak_pub"])

    # Set device counter high enough to exceed MAX_COUNTER_WINDOW (1000)
    # when compared to registry last_counter (0)
    device.counter = 100001  # gap = 100001 > 1000

    nonce = secrets.token_bytes(16)
    proof = device.generate_proof(b"x", b"y", b"z", nonce=nonce)

    verifier = FrekVerifier(registry)
    result = verifier.verify(proof, expected_nonce=nonce)
    assert result.accepted is False and result.code == "COUNTER_GAP_TOO_LARGE"
    print("  ✅ test_counter_window")


def test_revoked_device():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, nonce = make_proof(device)

    registry.revoke(device.device_id)
    result = verifier.verify(proof, expected_nonce=nonce)
    assert result.accepted is False and result.code == "DEVICE_REVOKED"
    print("  ✅ test_revoked_device")


def test_autonomous_mode():
    registry, device = make_registry_and_device()
    verifier = FrekVerifier(registry)
    proof, _ = make_proof(device)

    result = verifier.verify(proof, expected_nonce=None)
    assert result.accepted is True
    print("  ✅ test_autonomous_mode")


# ── Golden Vector Export ────────────────────────────────────

def export_golden_vectors():
    device = SimulatedFrekDevice()
    identity = device.get_identity()

    nonce = bytes.fromhex("A83F9E2B1C4D5E6F7A8B9C0D1E2F3A4B")
    audio = b"test_audio_buffer_48kHz_mono"
    fingerprint = b"test_fingerprint_mfcc_13bands"
    context = b'{\"location\":\"Studio_A\",\"gain\":12.5}'

    proof = device.generate_proof(audio, fingerprint, context, nonce=nonce)
    parsed = parse_proof(proof)

    print("\n" + "=" * 60)
    print("FREK GOLDEN TEST VECTOR")
    print("=" * 60)
    print(f"Device ID:     {identity['device_id'].hex()}")
    print(f"AK_pub:        {identity['ak_pub'].hex()}")
    print(f"Firmware Hash: {identity['firmware_hash'].hex()}")
    print(f"Nonce:         {nonce.hex()}")
    print(f"Proof ({len(proof)} bytes):")
    print(proof.hex())
    print("=" * 60)
    print(f"  MAGIC:        0x{parsed.magic:02X}")
    print(f"  VERSION:      {parsed.version}")
    print(f"  LEVEL:        {parsed.level}")
    print(f"  DEVICE_ID:    {parsed.device_id.hex()}")
    print(f"  COUNTER:      {parsed.counter}")
    print(f"  NONCE:        {parsed.nonce.hex()}")
    print(f"  DEVICE_TIME:  {parsed.device_time}")
    print(f"  AUDIO_HASH:   {parsed.audio_hash.hex()}")
    print(f"  FPRINT_HASH:  {parsed.fingerprint_hash.hex()}")
    print(f"  CONTEXT_HASH: {parsed.context_hash.hex()}")
    print(f"  FIRMWARE:     {parsed.firmware_hash.hex()}")
    print(f"  AK_PUB:       {parsed.pub_key.hex()}")
    print(f"  SIGNATURE:    {parsed.signature.hex()}")
    print("=" * 60)

    return proof, identity


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_valid_proof,
        test_signature_modified,
        test_audio_hash_modified,
        test_nonce_mismatch,
        test_replay_same_counter,
        test_replay_older_counter,
        test_unknown_device,
        test_identity_mismatch,
        test_firmware_rejected,
        test_bad_magic,
        test_unsupported_version,
        test_truncated_proof,
        test_bitflip_all_fields,
        test_counter_window,
        test_revoked_device,
        test_autonomous_mode,
    ]

    passed = 0
    failed = 0

    print("Running FREK Reference Verifier Tests...")
    print("=" * 60)

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("\nAll tests passed. Exporting Golden Vector...")
        export_golden_vectors()
    else:
        print(f"\n{failed} test(s) failed. Golden vector not exported.")
