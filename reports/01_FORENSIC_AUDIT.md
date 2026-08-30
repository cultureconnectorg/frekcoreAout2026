# 01 — Forensic Audit — FREKCORE

**Date**: 2026-08-30
**Scope**: `cultureconnectorg/frekcoreaout2026`, branch `claude/frekcore-v1-production-b9h2q0`
**Method**: Evidence First — every claim below cites a file and, where relevant, a line number. No claim is made about behavior that was not read in the actual source.

> This audit is the prerequisite for the FREKCORE v1.0 "Master Prompt" (CVLN OS Canonical). It does **not** assume the target DDD/Domain-Application-Infrastructure layout described in that prompt exists yet — it records what actually exists today, module by module, so that the Gap Analysis (`02_GAP_ANALYSIS.md`) can be built on fact rather than assumption.

---

## 1. Repository shape (evidence: `find . -maxdepth 3`)

FREKCORE today is a **monolithic FastAPI application** (`backend/server.py`) composed of ~35 additive, flat Python packages under `backend/`, plus a separate React/Vite/Capacitor frontend (`frontend/`), a standalone hardware-attestation spec (`frek_v3/`), ecosystem contracts (`ecosystem/`), operational memory documents (`memory/`), and prior audit reports (`docs/*-audit-2026-08-24.md`).

There is **no** `domain/`, `application/`, or `infrastructure/` split. Modules are organized by *feature* (`identity_engine/`, `fk/`, `notary/`, `passport/`, `did/`, `event/`, `badges/`, `security/`, `heritage/`, `sync/`, `geo/`, `health/`, ...), each owning its own `routes.py` (+ `service.py`/`models.py` where the feature warrants it) and registered onto the single `app` in `backend/server.py` via `app.include_router(...)`. This is a legitimate, working architecture (30 modules per `memory/INVENTORY.md:29`, confirmed by directory listing) — it is simply not the DDD layering the Master Prompt specifies. Reorganizing it wholesale was explicitly out of scope for this pass (see `08_NEXT_INTEGRATION.md`) because the Master Prompt's own invariant is **"Ne jamais casser une API existante"**.

## 2. Inventory (routes / models / schemas / migrations / jobs / events / middleware / auth / crypto / storage / logs)

| Category | Evidence | Notes |
|---|---|---|
| **API routers mounted** | `backend/server.py:215-334` — 30+ `app.include_router(...)` calls | All under `/api` or `/api/v1`; Swagger disabled by default in prod (`server.py:161-168`, `FREK_PUBLIC_DOCS`) |
| **Pydantic models** | e.g. `backend/identity_engine/models.py`, `backend/fk/models.py`, `backend/notary/models.py` | Typed, Pydantic v2 (`ConfigDict`, `Literal`) — see `identity_engine/models.py:35-46` |
| **Migrations** | `backend/migrations/20260824_unique_index_preflight.py` + `.md` | One documented preflight migration exists; no migration framework (Alembic-equivalent) — indexes are created idempotently at startup (`server.py:378-419`, `_ensure_unique_sparse_index`) |
| **Background jobs** | `backend/notary/service.py` (`notary_get_anchor().start()` at `server.py:522`), `scripts/backup_scheduler.py`, `scripts/chain_watchdog.py` | Anchor loop is an in-process asyncio task; backups/watchdog are standalone scripts, not a job queue |
| **"Events"** | `backend/event/routes.py` (CC2026 scan/NFC), `backend/frek_v1/stages.py` (append-only stage log) | **Not** a generic pub/sub Event Bus — see `02_GAP_ANALYSIS.md` Bloc 7 |
| **Middlewares** | `CORSMiddleware` (`server.py:362-368`) | No request-ID/correlation-ID middleware found (grep negative, see `05_SECURITY_REPORT.md`) |
| **Auth** | `backend/frek_v1/auth.py` (OAuth2 client-credentials + permission strings), `backend/identity_engine/service.py` (WebAuthn/Passkey + HMAC session tokens), `backend/staff/routes.py` (PIN-based) | Three distinct auth mechanisms for three distinct actor types (API clients, end users, field staff) |
| **Crypto** | `backend/passport/keys.py` (Ed25519), `backend/notary/chain.py` (Ed25519-signed blocks), `backend/passport/merkle.py` (Merkle tree + canonical JSON) | Real, working primitives — see `03_ARCHITECTURE_MAP.md` |
| **Storage** | `backend/moment/storage.py` (Object Storage init, `server.py:320-324`) | Single backend; see `02_GAP_ANALYSIS.md` Phase 10 for S3/Cloudinary/IPFS abstraction status |
| **Logs** | `logging.basicConfig(...)` (`server.py:371-374`), scoped loggers per module (e.g. `logging.getLogger("frek.identity_engine.service")`) | Unstructured (text, not JSON); no request-ID correlation |

## 3. Modules mapped to the Master Prompt's vocabulary

| Master Prompt concept | Closest existing code | Evidence |
|---|---|---|
| Identity Engine (Bloc 2 / Phase 3) | `backend/identity_engine/` | `models.py`, `service.py` (WebAuthn ceremonies, session tokens), `routes.py` |
| Proof Engine (Bloc 4 / Phase 4) | `backend/notary/` (chain/anchoring) + `backend/passport/` (Merkle + Ed25519 receipts) | `notary/chain.py`, `notary/anchor.py`, `passport/service.py` |
| Certificate Engine (Bloc 5) | `backend/badges/` (CC2026 event badges only) | `badges/routes.py:1-2` header: "CC2026 Badges API — 14 types" — no Academy/JCC concept |
| Permission Engine (Bloc 6) | `backend/frek_v1/auth.py` + `backend/security/policies.py` | Flat permission strings per API client, not CVLN roles (Founder/Executive/Artist/...) |
| Event Bus (Bloc 7) | `backend/event/` (CC2026-specific), `backend/frek_v1/stages.py` (append-only) | No generic publish/subscribe abstraction found (`grep -rn "EventBus\|event_bus\|publish(\|subscribe("` → no matches) |
| API Contract (Bloc 8) | `scripts/export_openapi.py` + `openapi/frekcore.openapi.json` | FastAPI-generated OpenAPI, exported/checked via script; Swagger UI gated behind `FREK_PUBLIC_DOCS` |
| SDKs (Bloc 9) | None found | No `sdk/` directory, no published Python/TS/RN client package |
| Storage abstraction (Bloc 10) | `backend/moment/storage.py` | Single implementation; no adapter interface for S3/Cloudinary/IPFS |
| Observability (Bloc 11) | `backend/health/routes.py`, scoped loggers | No Prometheus (`grep -rn "prometheus"` → no matches), no request-ID middleware |
| CI/CD (Bloc 12) | — | **No `.github/workflows/` directory exists in this repository.** |
| Docs (Phase 14) | `docs/*.md`, `memory/*.md`, `ecosystem/contracts/*.md` | Rich prior audit history, but not organized as the Master Prompt's `docs/architecture, api, identity, proof, events, security, deployment, developer-guide, admin-guide, troubleshooting` set |
| CVLN interfaces (Phase 15) | `ecosystem/registry.json`, `ecosystem/capabilities.json`, `ecosystem/contracts/*.md` | Covers FREKCORE-internal components (`frek_id`, `fk`, `frek_chain`, `passport`, `heritage`, `did`, `frek_v3`) and two *external* contracts (`frekraw`, `frekansla`) — **none of Wallet/KORA/Academy/LabelOS/Laurentia/Brain/Agent Factory existed prior to this session** (delivered under `docs/interfaces/`, see `08_NEXT_INTEGRATION.md`) |
| **FREK Registry (Bloc 1)** | — | **Did not exist prior to this session.** Delivered in this session as `backend/registry/` (see `08_NEXT_INTEGRATION.md`) |

## 4. What this session verified by execution (not just reading)

- `backend/registry/` (new in this session): 10/10 unit tests pass standalone against a `TestClient(FastAPI())` mounting only `registry_router` — no MongoDB dependency. Command and result reproduced in `06_TEST_REPORT.md`.
- The full `backend/tests/` integration suite (28 files, `pytest.ini:1-2` → `asyncio_mode = auto`) requires a **live backend process on `localhost:8001` plus MongoDB** (`backend/tests/conftest.py:6-9,21`) — it is an integration suite, not unit tests, and could not be exercised in this sandbox (no `mongod`, no supervisor process). This is stated explicitly rather than fabricating a pass/fail result. See `06_TEST_REPORT.md`.
- `python3 -c "ast.parse(...)"` confirms `backend/server.py`, `backend/registry/routes.py`, `backend/registry/service.py` are syntactically valid Python after this session's edit to `server.py` (3-line additive router registration, see diff referenced in `08_NEXT_INTEGRATION.md`).

## 5. Verdict

FREKCORE is a **real, running production system** (per `memory/INVENTORY.md`, `memory/RUNBOOK.md`, `memory/SOVEREIGNTY_AUDIT.md`) that already implements a working Identity+Proof core under different names than the Master Prompt uses. It is **not** yet the CVLN-wide Registry/Identity/Proof/Event/Certificate/Permission platform described in the Master Prompt — most of Blocs 1, 5, 6, 7, 9, 11, 12 are MISSING or PARTIAL. See `02_GAP_ANALYSIS.md` for the full per-block status table.
