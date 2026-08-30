# 12 — Phase 2 Implementation

Maps every Phase 2 priority to what was actually built, with evidence. Priorities not built are marked explicitly, with the reason — never silently skipped.

## Priority 1 — CI/CD → **DELIVERED**

`.github/workflows/ci.yml`, 7 jobs:

| Job | Blocking? | What it does |
|---|---|---|
| `lint-format-typecheck` | Yes | flake8 + black --check + mypy over this phase's 7 modules |
| `lint-full-repo-informational` | No (`continue-on-error`) | flake8 over the whole `backend/` (1121 pre-existing findings, informational) |
| `unit-tests` | Yes | canonical `pytest` (21→57 unit tests across the session) + coverage (`--cov-fail-under=90`, actual 99.03%) |
| `dependency-audit` | No | `pip-audit -r requirements-ci.txt` (real findings, see `11_SECURITY_PHASE2.md`) |
| `sdk-python` | Yes | real end-to-end SDK test against `registry_router` |
| `sdk-typescript` | Yes | `tsc --noEmit` + `node --test` |
| `docker-build` | No | genuinely attempts `docker build`, expected red (private dependency, documented inline) |

Every non-blocking job has an inline comment explaining exactly why, per "document why, never simulate success". No step fakes a pass.

## Priority 2 — Test Infrastructure → **DELIVERED**

Canonical command: `cd backend && pip install -r requirements-ci.txt && pytest` → 57 passed, 335 deselected, exit 0. Full root-cause writeup: `reports/10_TEST_INFRASTRUCTURE.md`. Real fixes applied:
- `backend/tests/conftest.py`: reordered `_purge_rate_limits()` to check `MONGO_URL`/`DB_NAME` before importing `pymongo`; added `pytest_collection_modifyitems` to auto-mark `integration`.
- `backend/tests/test_security_hardening.py`: hardcoded `/app/...` paths replaced with paths resolved relative to the repo root, with graceful `None`/localhost fallback instead of crashing collection.
- `backend/pytest.ini`: `unit`/`integration` markers registered, `addopts = -m "not integration" --ignore=tests/test_ecosystem.py` (the one file that cannot collect anywhere without the private `emergentintegrations` package).
- `backend/tests/test_fk.py`, `test_production_hardening_static.py`, `test_registry.py`: tagged `pytestmark = pytest.mark.unit` after individually proving each runs standalone with no network call.

## Priority 3 — Permission Engine → **DELIVERED (model only, not wired)**

`backend/permissions/` — `Role`/`ScopeType`/`Action` enums exactly matching the mission brief's tables, `Subject`/`RoleGrant`/`ResourceRef`/`DecisionRequest`/`Decision` models, `decide()` pure function, `ROLE_CAPABILITIES` table, `audit_integration.py` completing the chain into an `AuditEvent`. 8 tests (`tests/test_permissions.py`), 100% coverage.

**Explicitly not wired into `backend/frek_v1/auth.py` or any route.** Reasoning: `frek_v1/auth.py`'s flat-permission-string model is what the seeded API clients (`kiltikonet-cc2026`, `cvl-brain` — real, referenced in `server.py:456-471`) depend on today. Swapping the enforcement layer live, in a sandbox where the 335 integration tests cannot be run (`10_TEST_INFRASTRUCTURE.md`), would risk silently locking out those clients with no way to verify the blast radius before pushing. This is the single largest, most consequential decision in this phase — documented here rather than made silently in either direction.

## Priority 4 — Audit Trail → **DELIVERED (module only, not wired)**

`backend/audit_trail/` — `AuditEvent` (actor, FREK-ID, timestamp, request ID, correlation ID, action, resource, result, reason — the mission brief's exact minimum field list) + `InMemoryAuditRecorder`. Append-only enforced by class shape (`test_recorder_exposes_no_mutation_or_deletion_method` asserts the public API is exactly `{record, all_events}`). 5 tests, 100% coverage. Not wired into any route — same reasoning as Priority 3 (no live sink to write to without touching `server.py`'s DB wiring, which was kept out of scope for this pass).

## Priority 5 — Event Bus Abstraction → **DELIVERED**

`backend/eventbus/` — `EventEnvelope` (event_id, event_type, event_version, occurred_at, producer, subject, correlation_id, causation_id, payload, schema_version — exactly the mission brief's field list), `EventPublisher`/`EventSubscriber` Protocols, `InProcessEventBus` (the only implementation, explicitly documented as swappable for a future broker adapter without changing producer code). 6 tests, 100% coverage, including `test_envelope_matches_registry_schema` — a contract test asserting the Pydantic model and the JSON Schema served at `GET /api/v1/registry/events` never drift apart.

The Phase 1 event envelope schema (`backend/registry/events/event_registry.json`) was **corrected** this phase to match this richer field set (`data`→`payload`, `frek_id`→`subject`, added `producer`/`causation_id`) — safe because no producer depended on the old shape yet (this phase's `identity.created` producer is the first, see Priority 6).

## Priority 6 — Event Producers → **PARTIALLY DELIVERED (1 of 6 named events, honestly)**

Only `identity.created` was wired to a real producer, because `identity_engine` is the one module in the brief's minimum list that genuinely exists and has a genuinely safe insertion point:

- `backend/identity_engine/routes.py`: 18 lines added (a defensive `try/except`-guarded import + a defensive `try/except`-guarded publish call after `db.frek_persons.insert_one(identity)`). A publish failure can never break the identity-creation response — proven by `test_identity_engine_publish_wrapper_survives_a_broken_bus`.
- `backend/registry/events/event_registry.json`'s `identity.created` entry flipped `implemented: false → true`, with evidence citing the exact lines and tests.
- The other 5 (`identity.updated`, `identity.revoked`, `object.created`, `proof.generated`, `certificate.issued`) remain `implemented: false` or `PARTIAL` — **no code was written to make them true**, because (per the brief's own instruction) "NE JAMAIS marquer une capacité comme implémentée simplement parce que son schéma existe": `identity.updated`/`identity.revoked` have no corresponding route in `identity_engine/routes.py` (confirmed by re-reading it this phase); `object.created` would touch `backend/fk/routes.py` (not touched this phase, no time to safely verify); `certificate.issued` has no producing module at all (confirmed, see `02_GAP_ANALYSIS.md` Bloc 5).

## Priority 7 — SDK → **DELIVERED (Registry API only, both languages)**

`sdk/python/frekcore_sdk` (5 real end-to-end tests against the live `registry_router` via `TestClient`) and `sdk/typescript` (3 tests against a mocked `fetch`, `tsc --noEmit` clean). Both wrap **only** `/api/v1/registry/*` — the one API family with strong stability evidence from Phase 1+2. No method exists for an endpoint that wasn't independently verified to exist and behave as documented. See each SDK's `README.md` for the explicit scope statement.

## Priority 8 — API Versioning → **AUDITED, no change needed**

All new HTTP-facing code (`backend/registry/routes.py`, already existing before this phase) is mounted at `/api/v1/registry/*`, consistent with the existing convention documented in `reports/04_API_CONTRACT.md`. `backend/eventbus/`, `backend/permissions/`, `backend/audit_trail/`, `backend/proof_engine/`, `backend/storage/`, `backend/observability/` expose no HTTP routes at all this phase, so there is nothing to version yet. No existing route was touched, renamed, or deprecated.

## Priority 9 — Observability → **DELIVERED (module only, not wired)**

`backend/observability/` — `RequestIdMiddleware` (contextvar-backed request/correlation ID, tested via a real `TestClient` against an isolated app) + `metrics.py` (7 Prometheus counters/histograms named exactly after the brief's minimum list: HTTP requests, latency, errors, Registry/Identity/Proof/Event operations — using a dedicated `CollectorRegistry`, not the process-global default, so importing it never side-effects other modules). 5 tests, 100% coverage. Not wired into `server.py` — wiring `RequestIdMiddleware` is a literal one-line `app.add_middleware(...)` change, deliberately left out of this phase's diff to keep `server.py`'s change surface to the one Priority-6 edit that was actually tested end-to-end.

## Priority 10 — Security Hardening → **DELIVERED (audit)**

See `reports/11_SECURITY_PHASE2.md`.

## Priority 11 — Database Safety → **AUDITED, no change made**

Re-verified from Phase 1 (`reports/01_FORENSIC_AUDIT.md`): `backend/server.py:378-419`'s `_ensure_unique_sparse_index()` refuses to silently drop/recreate an incompatible index and refuses to create a unique index over pre-existing duplicates (raises, points at `backend/migrations/20260824_unique_index_preflight.py`). This is a real, working safety mechanism, unchanged and unbroken by this phase. No new collection or index was added by any Phase 2 module (none of the 7 new packages call `db.*` at all — verified by grep: `grep -rn "db\." backend/{registry,eventbus,permissions,audit_trail,proof_engine,storage,observability}/` → no matches outside comments).

## Priority 12 — Proof Engine Readiness → **DELIVERED**

`backend/proof_engine/` — `ProofState` enum with the brief's exact 6 states (fingerprint, local proof, signed proof, timestamp proof, OpenTimestamps, external anchoring), `ProofReceipt`, `ProofProvider` Protocol, and `proof_state_from_notary_block()` — a real adapter over `backend/notary`'s actual `BlockResponse` shape. Building this adapter **found and corrected a real documentation defect**: `ecosystem/registry.json`'s `frek_chain` entry claimed "Ed25519 signed blocks", but `backend/notary/*.py` contains no `sign`/`Ed25519` reference and `BlockResponse` has no `signature` field — corrected in `ecosystem/registry.json` with an inline note. 7 tests, 100% coverage. No blockchain/anchoring integration was added or changed — `backend/notary/anchor.py` is untouched.

## Priority 13 — Storage Abstraction → **DELIVERED (interface + one real implementation)**

`backend/storage/` — `StorageProvider` Protocol mirroring `backend/moment/storage.py`'s real `put_object`/`get_object` shape, plus `LocalFilesystemStorageProvider` (genuine local-disk I/O, path-traversal-protected, tested with real files under `tmp_path`). **No S3/Cloudinary stub was added** — per the brief's explicit warning against unused providers, and because this phase found no real, evidenced need for one beyond what `moment/storage.py` already does locally. 5 tests, 100% coverage.

## Priority 14 — Contract Tests → **PARTIALLY DELIVERED**

Real contract tests shipped this phase:
- `test_envelope_matches_registry_schema` (eventbus) — Pydantic model vs. JSON Schema.
- `test_get_schema_for_each_namespace_is_valid_json_schema` / `test_service_all_namespace_schemas_are_valid_draft202012` (registry, Phase 1, still passing).
- SDK end-to-end tests (Python) are themselves API-contract tests — they fail if `registry_router`'s actual response shape ever drifts from what the SDK expects.

**Not delivered**: an automated cross-language contract test tying the TypeScript SDK's expectations to the live server (it currently only checks against a hand-copied fixture — see `sdk/typescript/test/registryClient.test.ts`'s own comment); OpenAPI-schema contract verification (`scripts/export_openapi.py --check` could not be run — it imports `server.py`, blocked by the same `emergentintegrations` issue, see `10_TEST_INFRASTRUCTURE.md`); permission-decision determinism is exercised but not formally property-tested (no `hypothesis` dependency added — judged not worth a new dependency for this phase's scope).

## Priority 15 — Documentation → **DELIVERED**

This report set (`reports/09` through `14`) plus `docs/PHASE2_STATUS.md` (IMPLEMENTED/PARTIAL/PLANNED/NOT IMPLEMENTED per capability). `docs/interfaces/*.md` (Phase 1) were not modified — nothing in Phase 2 changed what those 7 CVLN systems can consume.

## Files changed (complete list)

**Modified** (11 files, existing code — every diff kept minimal and reviewed line-by-line):
`.gitignore`, `ecosystem/registry.json`, `backend/identity_engine/routes.py` (+18 lines, 0 removed), `backend/pytest.ini`, `backend/tests/conftest.py`, `backend/tests/test_fk.py` (+5, marker only), `backend/tests/test_production_hardening_static.py` (+5, marker only), `backend/tests/test_registry.py` (+5, marker only), `backend/tests/test_security_hardening.py`, `backend/registry/routes.py` / `service.py` (black reformat only, Phase 1 code untouched in behavior), `backend/registry/events/event_registry.json`.

**New** (58 files — see `git status`): `.github/workflows/ci.yml`; `backend/{eventbus,permissions,audit_trail,proof_engine,storage,observability}/` (7 packages incl. registry which already existed); `backend/requirements-ci.txt`; `backend/tests/test_{eventbus,permissions,audit_trail,proof_engine,storage,observability}.py`; `sdk/python/` (SDK + tests); `sdk/typescript/` (SDK + tests); `reports/09` through `14`; `docs/PHASE2_STATUS.md`.

## Test count progression

| Point in time | Unit tests | Coverage |
|---|---|---|
| Phase 1 end | 10 (`test_registry.py` only) | not measured repo-wide |
| Phase 2 end | 57 (registry, eventbus, permissions, audit_trail, proof_engine, storage, observability) + 5 (Python SDK) + 3 (TypeScript SDK) = **65** | 99.03% across the 7 backend modules with dedicated tests |

All 65 verified passing in this session (transcripts in `10_TEST_INFRASTRUCTURE.md` and this report).
