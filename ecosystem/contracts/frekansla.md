# Integration Contract — FREKANSLA

**Status:** `external_specified` (contract only, no implementation in this repo)

**Role:** Specialized branch of the FREK ecosystem for **audio / DSP / fingerprint certification**.

---

## Purpose

FREKANSLA is a specialized system for:
- perceptual audio fingerprinting
- DSP-level analysis
- audio provenance certification

FREKCORE delegates audio-specific certification to FREKANSLA when the FK object is audio.

---

## Integration flow

```
FREKCORE (FK.audio)               FREKANSLA
   │                                  │
   │ POST /ansla/fingerprint (audio)  │
   ├─────────────────────────────────>│
   │                                  │
   │  fingerprint + audio_proof       │
   │<─────────────────────────────────┤
   │                                  │
   │ Attach to FK.certifications[]    │
   ▼
FK.audio.fingerprint_ref="frekansla:xxx"
```

---

## Contract shape

### Request

```json
{
  "audio_ref": {
    "sha256": "hex",
    "duration_sec": 123.45,
    "sample_rate": 48000,
    "channels": 2
  },
  "identity_ref": {
    "frek_id": "id-...",
    "issuer": "frekcore"
  },
  "object_ref": {
    "type": "fk",
    "frek_id": "fk-..."
  }
}
```

### Response

```json
{
  "fingerprint_id": "ansla-xxxx",
  "issuer": "frekansla",
  "issuer_version": "string",
  "algorithm": "perceptual_hash_v1|chromaprint|other",
  "fingerprint": "base64 or vector",
  "cryptographic_proof": {
    "signature": "base64",
    "public_key": "base64"
  },
  "timestamp": "ISO 8601 UTC"
}
```

---

## Errors expected

- `NOT_INSTALLED` — FREKANSLA absent (current default)
- `NOT_CONFIGURED`
- `NOT_AVAILABLE`
- `UNSUPPORTED_FORMAT`

---

## Current status

**FREKANSLA is NOT present.** No audio DSP code is embedded in FREKCORE.

FREKCORE stores raw audio hashes and metadata only — never simulates fingerprinting.
