# Integration Contract — FREKRAW

**Status:** `external_specified` (contract only, no implementation in this repo)

**Role:** Specialized branch of the FREK ecosystem for **record certification**.

> **IMPORTANT — Doctrine reminder:**
> FREKRAW is **NOT** a programming language. It is a **record certification protocol**.
> Do not fuse with FREKCORE, FREKANSLA, FREK V3, a compiler, or a runtime.

---

## Purpose

When FREKCORE (or a FK object) needs a *record* to be certified beyond the standard FREKCORE attestation (existence, integrity, origin), FREKCORE delegates to FREKRAW through this contract.

---

## Integration flow

```
FREKCORE                          FREKRAW
   │                                 │
   │ POST /raw/certify (record ref)  │
   ├────────────────────────────────>│
   │                                 │
   │           certification result  │
   │<────────────────────────────────┤
   │                                 │
   │ Attach to FK.certifications[]   │
   ▼
FK object updated with issuer="frekraw"
```

---

## Contract shape

### Request (FREKCORE → FREKRAW)

```json
{
  "record_id": "string, opaque to FREKCORE",
  "identity_ref": {
    "frek_id": "id-xxxxxxxxxxxx-xxxx",
    "issuer": "frekcore"
  },
  "object_ref": {
    "type": "fk|moment|other",
    "frek_id": "id-...",
    "root_hash": "hex"
  },
  "timestamp": "ISO 8601 UTC",
  "requested_by": "frekcore@1.0"
}
```

### Response (FREKRAW → FREKCORE)

```json
{
  "certification_id": "raw-xxxx",
  "issuer": "frekraw",
  "issuer_version": "string",
  "record_ref": "string",
  "type": "record_certification",
  "timestamp": "ISO 8601 UTC",
  "cryptographic_proof": {
    "algorithm": "string (declared by FREKRAW)",
    "signature": "base64",
    "public_key": "base64"
  },
  "verification_method": "url or protocol descriptor"
}
```

---

## Errors expected

- `NOT_INSTALLED` — FREKRAW not present in this environment (current default)
- `NOT_CONFIGURED` — FREKRAW present but missing credentials
- `NOT_AVAILABLE` — FREKRAW temporarily down
- `REJECTED` — Record cannot be certified

---

## Current status in this repository

**FREKRAW is NOT present.** Any call to a hypothetical FREKRAW endpoint returns:

```json
{
  "status": "not_installed",
  "component": "frekraw",
  "hint": "Specialized external branch. Contract only in /app/ecosystem/contracts/frekraw.md"
}
```

FREKCORE **must not** invent responses, simulate signatures, or embed FREKRAW code.

---

## Attaching a FREKRAW certification to a FK

When FREKRAW is later available, its certification is added to `FK.certifications[]`:

```json
{
  "issuer": "frekraw",
  "type": "record_certification",
  "version": "x.y.z",
  "timestamp": "...",
  "cryptographic_proof": "...",
  "verification_method": "..."
}
```

The FK object remains valid without FREKRAW certification — the specialized certification is **additive**, not replacing FREKCORE attestation.
