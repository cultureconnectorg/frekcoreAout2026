# 03 — Architecture Map — FREKCORE

## 1. Top-level layout

```
frekcoreAout2026/
├── backend/            FastAPI monolith (single app, ~35 feature packages)
├── frontend/            React 18 + Vite + Tailwind + Capacitor (iOS/Android)
├── frek_v3/              Hardware attestation spec + reference verifier (isolated, no backend endpoint)
├── ecosystem/            Cross-system registry.json / capabilities.json / contracts/*.md
├── memory/               Operational doctrine, audits, runbooks (source of institutional truth)
├── docs/                 Prior production-hardening audits (2026-08-24) + (new) interfaces/
├── openapi/              Exported OpenAPI artifact + regeneration script contract
├── scripts/              Ops scripts: backup, chaos tests, loadtest (Locust), OpenAPI export
├── verifier/             Standalone offline verifiers (Python/JS) mirroring backend/passport
├── reports/              (new, this session) Evidence-based audit deliverables
└── docker-compose.yml, Dockerfile   backend + MongoDB only
```

## 2. Backend module map (`backend/`, one FastAPI app: `backend/server.py`)

Every module below is wired into the single `app` in `server.py` via `app.include_router(...)`. There is no per-module sub-application or gateway.

| Module | Role (as coded) | Owns own DB collections? | Auth used |
|---|---|---|---|
| `identity_engine/` | FREK-ID + WebAuthn/Passkey, session tokens | `frek_identities`* (shared with `frek_v1`) | Session HMAC token (`X-FREK-Session`) |
| `frek_v1/` | Legacy identity protocol ("Luciole", 11 stages), OAuth2 client-credentials auth, admin/dashboard | `frek_identities`, `frek_stages`, `frek_clients`, `frek_tokens` | `Depends(require_permission(...))` |
| `fk/` | FK Cultural Object Container (7-layer ZIP: identity/creators/timeline/media/intelligence/rights/proof) | `fk_objects` (implied) | Public/anonymous for verify; write path uses session |
| `notary/` | FREK-Chain: Ed25519-signed hash-chained blocks + OpenTimestamps/Bitcoin anchoring | `notary_blocks` | Internal (`notarize_event` called by other modules) |
| `passport/` | Offline-verifiable passport: Merkle-tree selective disclosure over notarized claims | none (stateless, reads notary) | Public (verifier is offline by design) |
| `did/`, `eudi/` | W3C DID Core + Verifiable Credentials, OID4VCI (EUDI Wallet interop) | — | Public resolution endpoints |
| `event/` | **CC2026-specific** venue scan/NFC-payment event day logic (not a generic bus) | `scans`, `transactions` | `require_permission("stage")` |
| `badges/` | CC2026 event badges (14 types, zone access, NFC) | `badges` | `require_permission` |
| `jetons/` | CC2026 token economy (recharge/payment) | `transactions`, `marchands` | `require_permission` |
| `security/` | Rate limiting + anomaly audit trail | `rate_limits` (per `tests/conftest.py:33`) | Admin-only routes |
| `audit/` | Human-readable timeline aggregation across `frek_stages`/`scans`/`transactions`/`notary_blocks` | none (read-only aggregator) | `require_permission` |
| `heritage/` | Long-term preservation, versioning/history | `frek_heritage_declarations`, `frek_heritage_transfers` | session/permission |
| `sync/` | Baserow bidirectional sync | `frek_sync_mapping`, `frek_sync_log`, `frek_sync_cursor` | internal |
| `geo/` | Geolocation layer (Phase 6, "souverain") | — | `require_permission` |
| `fingerprint/` | Cultural Fingerprint Layer (device/consent/cadence/affinity) | — | — |
| `staff/` | Field-agent PWA (PIN auth, QR/NFC scanning) | `staff` | PIN + lockout (`locked_until`, `failed_attempts`) |
| `standards/` | Public manifest + JWKS + DID Configuration (`.well-known/*`) | none | public |
| `health/` | Liveness/readiness | none | public |
| `investor/` | Due-diligence "pulse" endpoint | — | — |
| `pdf_batch/` | Self-service PDF badge generation | — | — |
| `seal/` | Embeddable JS "Certified Seal" widget for partners | none | public static asset |
| `email_service/`, `services/` | AWS SES email, Stripe checkout, generic webhook dispatch | `email_logs`, `email_campaigns`, `payment_transactions` | — |
| `counter/` | "Compteur souverain universel CVLN" scoring rules | — | `/api/core/count*` |
| `core/` | CC2026 "couche evenementielle souveraine" scoring engine | — | `/api/core/*` |
| **`registry/` (new, this session)** | **FREK Registry — Bloc 1 catalog of JSON Schemas** | **none (stateless)** | **public (read); no write path — see `04_API_CONTRACT.md`** |

\* Collection names inferred from `server.py` index-creation calls (`server.py:490-573`), not from a central schema file — there is no single source of truth for the MongoDB schema today.

## 3. Cryptographic architecture (verified by reading, Bloc 4 / Proof Engine)

```
 Client                     FREKCORE
   │                           │
   │  POST /fk/create          │
   ├──────────────────────────►│  1. Build 7-layer FK object (fk/packager.py)
   │                           │  2. Hash each layer (SHA-256) → layer_hashes
   │                           │  3. root_hash = SHA-256(canonical_json(layer_hashes))
   │                           │  4. signature = Ed25519_sign(root_hash)   (passport/keys.py)
   │                           │  5. notarize_event(...) → append-only block
   │                           │       block_hash = SHA-256(prev_hash + payload_hash)  (notary/chain.py)
   │                           │  6. (async) OpenTimestamps → Bitcoin anchor (notary/anchor.py)
   │◄──────────────────────────┤  .fk ZIP returned, containing proof/frekcore-attestation.json
```

Passport selective disclosure (`passport/service.py:154-178`) lets a holder reveal a subset of claims while proving they are part of the same Merkle root as the full passport — this is a real, tested Merkle-proof implementation, not a stub.

## 4. What "FREK Registry" (Bloc 1, delivered this session) adds to this map

```
backend/registry/
├── __init__.py
├── service.py           loads + validates JSON Schemas (no DB)
├── routes.py            GET /namespaces, GET /namespaces/{ns}, POST /validate, GET /events
├── schemas/v1/
│   ├── _base.schema.json        shared envelope (frek_id, entity_type, owner_id, status, ...)
│   ├── frek.artist.schema.json
│   ├── frek.track.schema.json
│   ├── frek.album.schema.json
│   ├── frek.work.schema.json
│   ├── frek.certificate.schema.json
│   ├── frek.organization.schema.json
│   ├── frek.wallet.schema.json      (identity<->wallet LINK only — no ledger/balance fields)
│   └── frek.event.schema.json
└── events/
    └── event_registry.json          Bloc 7 catalog: envelope schema + 9 events, each with implemented:true/false + evidence
```

This module is intentionally **stateless and additive**: it does not touch any existing collection, does not require `set_db()`, and cannot regress any existing endpoint. It is mounted last in `server.py`'s router-registration sequence to keep the diff minimal and reviewable.

## 5. Deployment topology (as coded)

```
docker-compose.yml
├── mongo (image: mongo:7.0)
└── backend (Dockerfile: python:3.12-slim, uvicorn server:app --port 8001)
```

No frontend service, no reverse proxy, no separate dev/prod compose files are defined in `docker-compose.yml` — see `07_DEPLOYMENT_REPORT.md` for the full gap list against Master Prompt Phase 13 (Docker).
