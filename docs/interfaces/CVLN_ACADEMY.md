# Interface: CVLN Academy

**Role of FREKCORE**: Student/Person identity resolver + Certificate proof/signature contract. No course content, no JCC-credit computation, no Qualiopi compliance workflow.

## What FREKCORE exposes today

| Capability | Route | Evidence |
|---|---|---|
| Resolve the identity of a student/holder | `GET /api/v1/identity/me`, `GET /api/v1/identity/{id}/objects` | `memory/INVENTORY.md:50-54` |
| Sign an arbitrary claim set with Ed25519 + Merkle selective disclosure (reusable for a diploma) | `backend/passport/service.py:137-178` | `build_passport`/`disclose`/`verify` |
| Notarize an issuance event | `POST /api/v1/notary/notarize` | `backend/notary/routes.py` |

**Note**: `backend/badges/` (CC2026 "14 badge types") is a *different* system — event-day access badges, not Academy diplomas. Do not confuse the two; see `reports/01_FORENSIC_AUDIT.md` §3.

## What this session added (Bloc 1 / Bloc 5 contract)

`frek.certificate` namespace (`backend/registry/schemas/v1/frek.certificate.schema.json`):

```json
{
  "frek_id": "id-...",
  "entity_type": "frek.certificate",
  "status": "active",
  "created_at": "2026-08-30T00:00:00Z",
  "title": "Certification Culture Connect — Module 3",
  "holder_id": "id-abcdef012345-ab12",
  "issuer": "CVLN Academy",
  "issued_at": "2026-08-30T00:00:00Z",
  "expires_at": null,
  "jcc_credits": 12,
  "verification_url": "https://verify.cvln.org/id-abcdef012345-ab12",
  "qr_payload": "...",
  "signature": "base64-ed25519-signature"
}
```

Fields match the Master Prompt's Bloc 5 list exactly: FREK-ID, JCC credit, CVLN signature, QR verification, issuer, expiration. Academy is responsible for computing `jcc_credits` and course completion; FREKCORE only validates the resulting record's shape (`POST /api/v1/registry/validate`) and can sign it via the existing Passport primitives.

## Explicitly out of scope (belongs in CVLN Academy's own repository)

- Course/module content and progress tracking.
- JCC credit computation rules, Qualiopi audit workflow.
- The `certificate.issued` event (catalogued as `implemented: false`) has no producer in FREKCORE today.

## Proposed next step (PROPOSED, NOT IMPLEMENTED)

A `POST /api/v1/certificates/issue` endpoint that validates against `frek.certificate`, signs the envelope via `passport.service.build_passport`-style Ed25519 signing, and emits `certificate.issued`. Not built this session — it is the natural Bloc 5 "Certificate Engine" follow-up once the Registry has a persistence layer.
