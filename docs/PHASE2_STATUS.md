# FREKCORE — Phase 2 Status

Statuses use exactly four labels, per the mission brief: **IMPLEMENTED**, **PARTIAL**, **PLANNED**, **NOT IMPLEMENTED**. Every row cross-references the report that carries the evidence.

## Architecture

| Capability | Status | Detail |
|---|---|---|
| DDD Domain/Application/Infrastructure layering | NOT IMPLEMENTED | Never in scope for either phase (explicit non-goal). See `reports/03_ARCHITECTURE_MAP.md`. |
| FastAPI monolith, 30+ feature packages | IMPLEMENTED | Pre-existing, re-verified. `reports/03_ARCHITECTURE_MAP.md` |

## Registry (Bloc 1)

| Capability | Status | Detail |
|---|---|---|
| 8 versioned JSON Schema namespaces | IMPLEMENTED | Phase 1, re-verified Phase 2. `backend/registry/schemas/v1/` |
| Registry REST API (list/get/validate) | IMPLEMENTED | `backend/registry/routes.py` |
| Registry instance store (persisted objects) | IMPLEMENTED (2026-08-31) | `POST/GET /api/v1/registry/objects/{namespace}` + `GET .../{namespace}/{frek_id}`, `backend/registry/routes.py`, schema-validated before insert into `registry_objects`. Live-tested: `backend/tests/test_registry_objects.py`. |

## Identity Engine

| Capability | Status | Detail |
|---|---|---|
| Generate, Resolve (WebAuthn/Passkey) | IMPLEMENTED | Pre-existing. `reports/02_GAP_ANALYSIS.md` |
| Merge, Revoke, Archive, Search | NOT IMPLEMENTED | No route exists. `reports/02_GAP_ANALYSIS.md` |
| Publishes `identity.created` event | IMPLEMENTED | New this phase. `backend/identity_engine/routes.py:36-46,124-130` |

## Events (Bloc 7)

| Capability | Status | Detail |
|---|---|---|
| Event envelope + catalog contract | IMPLEMENTED | `backend/registry/events/event_registry.json` |
| `EventPublisher`/`EventSubscriber`/`InProcessEventBus` abstraction | IMPLEMENTED | `backend/eventbus/` |
| `identity.created` producer | IMPLEMENTED | See above |
| `identity.updated`, `identity.revoked`, `object.created`, `proof.generated`, `certificate.issued` producers | NOT IMPLEMENTED | `reports/12_PHASE2_IMPLEMENTATION.md` Priority 6 |
| External broker (Kafka/RabbitMQ) | NOT IMPLEMENTED | Explicit non-goal — no evidenced need |

## Permissions (Bloc 6)

| Capability | Status | Detail |
|---|---|---|
| Role/Scope/Action/Decision model | IMPLEMENTED | `backend/permissions/` |
| Enforcement on any live route | NOT IMPLEMENTED | Model only — see `reports/12_PHASE2_IMPLEMENTATION.md` Priority 3 for why |
| Existing flat-permission-string auth (`frek_v1/auth.py`) | IMPLEMENTED | Pre-existing, still the only thing actually enforced today |

## Audit Trail

| Capability | Status | Detail |
|---|---|---|
| `AuditEvent` model + append-only recorder | IMPLEMENTED | `backend/audit_trail/` |
| Wired as a sink for any real operation | NOT IMPLEMENTED | Not wired this phase |

## Proof Engine

| Capability | Status | Detail |
|---|---|---|
| FREK-Chain hash-chaining + OpenTimestamps + Bitcoin anchoring | IMPLEMENTED | Pre-existing (`backend/notary/`). Note: not Ed25519-signed at the block level — corrected claim, see `reports/12_PHASE2_IMPLEMENTATION.md` Priority 12 |
| Passport selective disclosure (Ed25519-signed) | IMPLEMENTED | Pre-existing (`backend/passport/`) |
| Explicit `ProofState` enum + `ProofProvider` interface | IMPLEMENTED | `backend/proof_engine/` |
| Additional blockchain/anchor provider | NOT IMPLEMENTED | Explicit non-goal |

## Storage

| Capability | Status | Detail |
|---|---|---|
| Local object storage (`backend/moment/storage.py`) | IMPLEMENTED | Pre-existing |
| `StorageProvider` interface | IMPLEMENTED | `backend/storage/` |
| `LocalFilesystemStorageProvider` (real impl) | IMPLEMENTED | `backend/storage/local.py` |
| S3/Cloudinary implementations | NOT IMPLEMENTED | No evidenced need this phase |

## Observability

| Capability | Status | Detail |
|---|---|---|
| Structured request-ID/correlation-ID middleware | IMPLEMENTED (module), NOT WIRED | `backend/observability/request_id.py` |
| Prometheus metrics (HTTP, Registry, Identity, Proof, Event) | IMPLEMENTED (module), NOT WIRED | `backend/observability/metrics.py` |
| `/health/live`, `/health/deep` | IMPLEMENTED | Pre-existing |
| `GET /metrics` route | NOT IMPLEMENTED | No route added this phase |

## SDKs

| Capability | Status | Detail |
|---|---|---|
| Python SDK — Registry API | IMPLEMENTED | `sdk/python/`, 5 real end-to-end tests |
| TypeScript SDK — Registry API | IMPLEMENTED | `sdk/typescript/`, 3 tests (mocked fetch) |
| SDK coverage of Identity/Proof/other APIs | NOT IMPLEMENTED | No stable-enough evidence yet this phase |

## CI/CD

| Capability | Status | Detail |
|---|---|---|
| Lint, format-check, typecheck (scoped) | IMPLEMENTED | `.github/workflows/ci.yml` |
| Unit tests + coverage gate | IMPLEMENTED | Same, `--cov-fail-under=90`, actual 99.03% |
| Dependency/security scan | IMPLEMENTED (informational) | `pip-audit`, non-blocking, real findings |
| Docker build | PARTIAL | Genuinely attempted, expected red (documented blocker) |
| Full integration-suite run in CI | NOT IMPLEMENTED | Needs MongoDB + live server service containers, not set up this phase |

## Documentation

| Capability | Status | Detail |
|---|---|---|
| `reports/09` through `14` | IMPLEMENTED | This phase |
| `docs/interfaces/*.md` (Phase 1, 7 CVLN systems) | IMPLEMENTED, unchanged | Nothing in Phase 2 altered what those systems can consume |
| This file | IMPLEMENTED | — |
