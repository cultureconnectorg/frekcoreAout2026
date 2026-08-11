"""
FREK Attestation Protocol — Binary Parser / Serializer
Reference Implementation v0.1

Format binaire L2 (283 bytes fixed):
  [0]     MAGIC         1 byte
  [1]     VERSION       1 byte
  [2]     LEVEL         1 byte
  [3]     RESERVED      1 byte
  [4:20]  DEVICE_ID     16 bytes
  [20:28] COUNTER       8 bytes (uint64 BE)
  [28:44] NONCE         16 bytes
  [44:68] DEVICE_TIME   24 bytes (UTF-8, null-padded)
  [68:100]  AUDIO_HASH        32 bytes
  [100:132] FINGERPRINT_HASH  32 bytes
  [132:164] CONTEXT_HASH      32 bytes
  [164:196] FIRMWARE_HASH     32 bytes
  [196:229] PUB_KEY           33 bytes (P-256 compressed)
  [229:293] SIGNATURE         64 bytes (r || s)
"""

import struct
from frek_constants import SIZE_PROOF_L2, SIZE_DEVICE_TIME
from frek_types import FrekProof


def parse_proof(data: bytes) -> FrekProof:
    """Parse a binary FREK Proof into a FrekProof object."""
    if len(data) != SIZE_PROOF_L2:
        raise ValueError(f"Invalid proof size: expected {SIZE_PROOF_L2}, got {len(data)}")

    magic = data[0]
    version = data[1]
    level = data[2]
    reserved = data[3]

    device_id = data[4:20]
    counter = struct.unpack(">Q", data[20:28])[0]
    nonce = data[28:44]

    # Trim null padding from device_time
    device_time = data[44:68].decode("utf-8").rstrip("\x00")

    audio_hash = data[68:100]
    fingerprint_hash = data[100:132]
    context_hash = data[132:164]
    firmware_hash = data[164:196]
    pub_key = data[196:229]
    signature = data[229:293]

    return FrekProof(
        magic=magic,
        version=version,
        level=level,
        reserved=reserved,
        device_id=device_id,
        counter=counter,
        nonce=nonce,
        device_time=device_time,
        audio_hash=audio_hash,
        fingerprint_hash=fingerprint_hash,
        context_hash=context_hash,
        firmware_hash=firmware_hash,
        pub_key=pub_key,
        signature=signature,
    )


def serialize_proof(proof: FrekProof) -> bytes:
    """Serialize a FrekProof object into binary format."""
    # Pad device_time to 24 bytes
    time_bytes = proof.device_time.encode("utf-8")
    if len(time_bytes) < SIZE_DEVICE_TIME:
        time_bytes = time_bytes + b"\x00" * (SIZE_DEVICE_TIME - len(time_bytes))
    else:
        time_bytes = time_bytes[:SIZE_DEVICE_TIME]

    return (
        struct.pack(">BBBB", proof.magic, proof.version, proof.level, proof.reserved) +
        proof.device_id +
        struct.pack(">Q", proof.counter) +
        proof.nonce +
        time_bytes +
        proof.audio_hash +
        proof.fingerprint_hash +
        proof.context_hash +
        proof.firmware_hash +
        proof.pub_key +
        proof.signature
    )
