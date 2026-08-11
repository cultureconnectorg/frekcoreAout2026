# Integration Contract — FREK V3 Hardware

**Status:** `specified_isolated` (reference implementation at `/app/frek_v3/`, isolated from backend)

**Role:** Hardware root of trust — PUF-derived Attestation Key, ECDSA P-256 signatures.

---

## Purpose

FREK V3 provides **hardware-anchored proofs** (Level L2) that FREKCORE can verify to certify that a proof came from a genuine FREKCORE hardware device.

---

## Current state in this repository

Located at **`/app/frek_v3/`** (parallel to `/app/backend/`, NOT inside).

- `docs/` — 12 specifications frozen
- `reference_verifier/` — Python reference verifier (immutable)
- **16/16 Golden Test Vectors passing**
- **No backend endpoint** — verifier is a standalone tool, not a service

Phases:
- **Phase 1 (done):** Python reference verifier + specifications
- **Phase 2 (future):** Rust re-implementation, bit-exact
- **Phase 3 (future):** Backend adapter `/api/v1/frek_v3/verify`
- **Phase 4 (future):** FPGA prototype (Zynq/Cyclone)
- **Phase 5 (future):** ASIC (silicon hardware)

---

## Future integration flow (Phase 3+)

```
User device (FREK V3 hardware)
    │
    │ FREK Proof (315 bytes, ECDSA P-256, r||s)
    ▼
FREKCORE backend endpoint /api/v1/frek_v3/verify
    │
    │ Uses Rust re-implementation of /app/frek_v3/reference_verifier
    ▼
VerificationResult {accepted, code, device_id, counter}
    │
    │ On accept: attach to FK.certifications[]
    ▼
FK.certifications += {issuer: "frek_v3", level: "L2", device_id: hex}
```

---

## Contract shape (planned)

### Request (device → FREKCORE, planned)

Binary proof:
- MAGIC (1 byte) = 0x46
- VERSION (1 byte) = 0x01
- LEVEL (1 byte) = 0x02 (L2 hardware)
- RESERVED (1 byte)
- DEVICE_ID (16 bytes)
- COUNTER (8 bytes uint64)
- NONCE (16 bytes)
- DEVICE_TIME (24 bytes ISO 8601)
- AUDIO_HASH (32 bytes)
- FINGERPRINT_HASH (32 bytes)
- CONTEXT_HASH (32 bytes)
- FIRMWARE_HASH (32 bytes)
- PUB_KEY (33 bytes P-256 compressed)
- SIGNATURE (64 bytes r||s)
- **Total: 315 bytes**

### Response (planned)

```json
{
  "accepted": true,
  "code": "ACCEPT",
  "device_id": "hex 32 chars",
  "counter": 1234,
  "device_time": "ISO 8601",
  "verifier_time": "ISO 8601",
  "firmware_hash": "hex 64 chars"
}
```

Error codes: `INVALID_SIGNATURE`, `REPLAY`, `UNKNOWN_DEVICE`, `IDENTITY_MISMATCH`, `FIRMWARE_REJECTED`, `MALFORMED`, `UNSUPPORTED_VERSION`, `NONCE_MISMATCH`, `REVOKED`.

---

## Rules

- **DO NOT** copy `/app/frek_v3/` code into `/app/backend/`
- **DO NOT** modify the reference verifier — it is the mathematical ground truth
- **DO NOT** create fake endpoints simulating hardware — hardware must exist first
- Testing this contract runs the reference verifier's 16 tests via pytest
