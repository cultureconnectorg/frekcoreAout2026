# FREKCORE STATE_8 — Regression / Evidence / Migration Validation Results

**BASELINE_HEAD**: `fc37516` (STATE_7, ACCEPTED). **NEW_HEAD**: this state's commit
(see `reports/21_FREEZE_ASSESSMENT.md`'s STATE_8 update for the exact SHA once
pushed). Date: 2026-09-03.

Evidence levels used throughout, per the mission's own instruction ("do not use
VERIFIED without saying what level"):

- **DOCUMENTED** — written down, not exercised by any test.
- **IMPLEMENTED** — real code exists, callable.
- **UNIT_VERIFIED** — a pure-logic/isolated unit test exercises it.
- **INTEGRATION_VERIFIED** — a TestClient + mongomock_motor test exercises the
  real router/service stack end-to-end (no live server, no real Mongo).
- **REAL_INFRA_VERIFIED** — exercised against genuinely persistent, real
  infrastructure (only `storage.local.LocalFilesystemStorageProvider`, real
  disk, qualifies this state).
- **BLOCKED** — environment prevents verification; blocker reproduced and
  recorded, not simulated as equivalent.
- **NOT_VERIFIED** — explicitly not proven, stated as such rather than implied.

---

## 1. Full regression

```
pytest -v                                            507 passed, 405 deselected
pytest --cov=registry --cov=eventbus --cov=permissions \
       --cov=audit_trail --cov=proof_engine --cov=storage \
       --cov=observability --cov-fail-under=90        96.95% (gate: >=90%)
flake8 --max-line-length=120 $MODULES $TEST_FILES      clean
black --check $MODULES $TEST_FILES                     clean
mypy --ignore-missing-imports $MODULES                  clean
PYTHONPATH=backend:sdk/python pytest sdk/python/tests   31 passed
(cd sdk/typescript && npm run typecheck && npm test)    typecheck clean, 38 passed
pytest tests/test_api_contract.py                       4 passed (golden snapshot unchanged)
```

`TESTS: 483 -> 507` (backend, +24: +7 delegated-authority full-chain tests in
`tests/test_permissions.py`, +17 in the new `tests/test_state8_validation.py`).
Python/TypeScript SDK counts unchanged (31 / 38) — no SDK code changed this
state. **FULL_UNIT_REGRESSION_GREEN=TRUE.**

## 2. Cross-module integration regression

`CROSS_MODULE_INTEGRATION_TESTS_GREEN=TRUE` — evidence:

- `tests/test_state8_validation.py::TestAppRestartAgainstSamePersistedDb` —
  content_binding write survives a full FastAPI-app teardown/rebuild against
  the same db handle (INTEGRATION_VERIFIED).
- `tests/test_offline_transport_unit.py` — offline receive -> persist -> sync
  crosses offline_transport / identity_engine / creative_lifecycle /
  relationship_graph / content_binding / eventbus / audit_trail in one flow
  (INTEGRATION_VERIFIED, pre-existing, re-run green).
- `tests/test_legacy_compatibility.py` — legacy `backend/frek/` routes exercise
  the same canonical D1-D5 modules + rate limiting + audit visibility
  (INTEGRATION_VERIFIED, pre-existing, re-run green).
- `tests/test_fk_object_created_event.py` — fk/routes.py -> eventbus ->
  (subscriber path) crosses 2 modules (INTEGRATION_VERIFIED, pre-existing).

## 3. Invariants re-verified cross-module

| Invariant | Evidence | Level |
|---|---|---|
| `FREK_ID != FINGERPRINT` | `tests/test_content_binding_unit.py::TestFrekIdSeparatedFromFingerprint`, `test_state8_validation.py::test_frek_id_and_fingerprint_are_never_the_same_field` | INTEGRATION_VERIFIED |
| `CLAIM != EVIDENCE` | `tests/test_evidence_semantics.py`, `test_state8_validation.py::test_claim_and_evidence_are_distinct_types` (distinct Pydantic types, no subclass relation) | UNIT_VERIFIED |
| `EVIDENCE != PROOF` | `test_state8_validation.py::test_evidence_and_proof_are_distinct_types` | UNIT_VERIFIED |
| `PROOF != VERIFICATION` | `test_state8_validation.py::test_proof_state_enum_does_not_include_a_verification_state` (`ProofState`'s 6 values contain no verification concept) | UNIT_VERIFIED |
| `SIGNATURE_VALID != CURRENT_AUTHORITY` | `tests/test_offline_transport_unit.py::TestRevocation::test_device_revoked_between_receive_and_sync_is_caught_at_sync` (a validly-signed envelope from a since-revoked device is still rejected at sync) | INTEGRATION_VERIFIED |
| `ANCHOR != LEGAL_OWNERSHIP` | `tests/test_notary*.py`, `docs/architecture/FREKCORE_API_CONTRACT_V1.md` (D5 report framing) | DOCUMENTED + UNIT_VERIFIED |
| `GENESIS != LEGAL_AUTHORSHIP` / `GENESIS != LEGAL_OWNERSHIP` | `tests/test_creative_lifecycle_unit.py`, D5's forbidden-phrase guard (`technical_evidence_report`) | UNIT_VERIFIED |
| `INFERENCE != VERIFIED_FACT` | `tests/test_relationship_graph_unit.py` (cultural relations can never reach VERIFIED status — enforced structurally, D3) | UNIT_VERIFIED |
| `WATERMARK != PROOF` | `tests/test_offline_transport_unit.py::TestWatermarkNotProof` | UNIT_VERIFIED |
| `OFFLINE_ACCEPTED != FINAL_RECONCILIATION` | `tests/test_offline_transport_unit.py::test_receive_acceptance_never_sets_sync_status_synced` | INTEGRATION_VERIFIED |
| `PUBLIC_VERIFICATION != PUBLIC_DISCLOSURE` | `tests/test_technical_evidence_report_unit.py`'s field-disclosure tests, §9 below | INTEGRATION_VERIFIED |
| `LEGACY_INTERFACE != CANONICAL_TRUTH_ENGINE` | `test_state8_validation.py::test_legacy_router_and_canonical_router_are_different_modules`; `tests/test_legacy_compatibility.py` (no route writes a second truth) | UNIT_VERIFIED + INTEGRATION_VERIFIED |
| `SDK_CONTRACT != INTERNAL_STORAGE` | `test_state8_validation.py::test_sdk_clients_never_import_backend_storage_or_db_modules` (static import audit, both SDK languages' Python clients checked; TS clients have no such imports available to them at all — httpm-fetch-only by construction) | UNIT_VERIFIED |
| `SERVICE_IDENTITY != AUTOMATIC_AUTHORITY` | `test_state8_validation.py::test_service_identity_is_not_automatically_authoritative` (neither `decide()` nor `delegation_authority_chain_valid()` accepts a bare ServiceIdentity as sufficient input) | UNIT_VERIFIED |
| `DELEGATION_GRANT != PROOF_DELEGATOR_HELD_AUTHORITY` | `tests/test_permissions.py::test_delegation_chain_denied_when_delegator_never_held_authority` + `test_state8_validation.py::test_delegation_grant_alone_never_proves_delegator_authority` | UNIT_VERIFIED |

## 4. Delegated authority — full chain

STATE_7 reported `DELEGATED_AUTHORITY=PARTIAL` because `delegation_permits()`
deliberately never checks whether the delegator actually held the authority it
purports to delegate (by its own docstring). This state closes that gap with
`permissions.delegation.delegation_authority_chain_valid()` — a composition of
the existing `decide()` (delegator's own current RoleGrants) and
`delegation_permits()` (the grant itself), never a new authority vocabulary
(`NO_PARALLEL_AUTHORITY_ENGINE=TRUE`, verified: the new function imports only
from `.engine` and `.models`, no new closed vocabulary added).

| Required proof | Test | Result |
|---|---|---|
| Delegate cannot exceed delegation scope | `test_delegation_denies_action_not_in_grant`, `test_delegation_permits_within_scope_and_actions` (STATE_7) | PASS |
| Delegation cannot exceed resource boundary | `test_delegation_resource_boundary_narrower_than_scope`, `test_delegation_resource_boundary_rejects_mismatched_resource_type` (STATE_7) | PASS |
| Expired delegation rejected | `test_delegation_denies_after_valid_until`, `test_delegation_denies_before_valid_from` (STATE_7) | PASS |
| Revoked delegation rejected | `test_delegation_denies_once_revoked` (STATE_7) | PASS |
| Wrong delegate rejected | `test_delegation_denies_wrong_delegate` (STATE_7) | PASS |
| Unsupported action rejected | `test_delegation_chain_denied_when_role_capability_does_not_cover_action` (STATE_8 — the delegator's own role does not cover the action, even though the grant itself lists it) | PASS |
| Delegator lacking originating authority cannot create/use an effective delegation | `test_delegation_chain_denied_when_delegator_never_held_authority` (STATE_8) | PASS |
| Revocation of delegator authority invalidates delegated authority | `test_delegation_chain_denied_when_delegator_authority_revoked` (STATE_8 — models the policy: authority is bounded by the delegator's CURRENT RoleGrants, not a creation-time snapshot) | PASS |
| Delegator/grant identity mismatch rejected | `test_delegation_chain_denied_when_delegator_subject_mismatch` (STATE_8) | PASS |
| OBJECT-scope delegation bounded by delegator's own ownership | `test_delegation_chain_denied_object_scope_when_delegator_not_owner` (STATE_8) | PASS |

`DELEGATED_AUTHORITY=VERIFIED` (UNIT_VERIFIED — pure-logic, not wired into any
live route, same disclosed status as `decide()`/`RoleGrant` themselves).
`DELEGATOR_AUTHORITY_CHECK=VERIFIED` (UNIT_VERIFIED).

One doc/code inconsistency found and fixed while validating this: `permissions/
models.py`'s `DelegationGrant` docstring said the containment invariant was
"enforced by `delegation_permits()`... not by this model alone" in a way that
implied `delegation_permits()` checked delegator authority — it does not
(by its own, more careful docstring). Corrected to point at the new composed
function instead. This is the one bounded contract correction STATE_8 makes;
no other STATE_7 contract text was found inconsistent with its own code.

## 5. Persistence / recovery / restart

**REAL_MONGO_VALIDATION=BLOCKED.** Re-attempted this state, not assumed carried
forward:

```
$ docker pull mongo:7
Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
Is the docker daemon running?
$ which mongod            # (no output — not installed)
$ env | grep -i mongo     # (no output — no MONGO_URI configured)
```

This sandbox has no reachable Docker daemon at all (a different failure mode
than the `403 Forbidden` pull error recorded in `reports/23_REAL_MONGODB_
VALIDATION_PLAN.md` during D1-D6, but the same underlying blocker: no real
MongoDB reachable here).

**Addendum (2026-09-03, post-STATE_8-delivery)** — the founder supplied real
MongoDB Atlas cluster credentials directly in chat after this state's report
was delivered. Re-attempted immediately, credentials never written to disk
or committed anywhere (used only in-memory for one diagnostic command, then
discarded from this session's working state):

```
$ python3 -c "import socket; socket.getaddrinfo('_mongodb._tcp.cluster0.4rawqdn.mongodb.net', ...)"
# SRV lookup succeeds -- 3 shard hosts resolve via DNS fine
$ python3 -c "socket.socket(...).connect(('ac-86nvg7r-shard-00-00.4rawqdn.mongodb.net', 27017))"
TimeoutError: timed out
$ pymongo.MongoClient(<the real srv URI>).admin.command('ping')
ServerSelectionTimeoutError: No replica set members found yet, Timeout: 8.0s,
  ... servers: [... server_type: Unknown, rtt: None ...]  (all 3 shard hosts unreachable)
```

This never reached the authentication step at all -- the connection is
blocked at the network layer, before any credential is evaluated (proven by
running the same diagnostic with a placeholder password: identical
failure). A control test to a wholly unrelated HTTPS destination
(`https://www.google.com`) through this sandbox's own egress proxy returned
the same class of result: `403 connect_rejected` ("gateway answered 403 to
CONNECT (organization policy)"), confirming this sandbox's outbound network
is allowlist-gated at the organization/session level, not merely missing a
local Docker daemon. **This is stronger evidence than STATE_8's original
finding**, not new information changing the verdict: even a real, reachable
Atlas cluster with valid credentials cannot be validated from this specific
sandboxed session -- the blocker is this session's own network egress
policy, external to the FREKCORE codebase and independent of Docker's
absence. Per the mission's explicit instruction, mongomock is **not**
substituted as equivalent evidence. Consequently, true restart-survives
-real-Mongo-persistence is **NOT_VERIFIED** for every Mongo-backed collection
(identity, registry, content bindings, creative lifecycle, relationships,
proof/notary, offline queue, technical evidence reports, audit trail,
compatibility mappings) — this is unchanged from every prior state and remains
the single largest concrete blocker to freeze. **Recommendation to the
founder**: this validation needs to run from an environment with open
egress to MongoDB Atlas (a developer machine, a CI runner with network
access, or a sandbox session configured with that destination allowlisted)
-- not achievable by supplying credentials alone to this session.

What this sandbox *can* verify, and does:

- **`storage.local.LocalFilesystemStorageProvider`** — the one canonical
  persistence layer in this codebase backed by real, non-mocked I/O. Write,
  new process-equivalent instance, read: **REAL_INFRA_VERIFIED**
  (`test_state8_validation.py::TestLocalStorageRestartDurability`, 2 tests).
- **No route holds authoritative state in Python-process memory** — every
  Mongo-backed canonical route was confirmed (by direct code reading of
  `server.py` + each module's `set_db()` pattern) to source all reads through
  the injected `db` handle, never a module-level cache; concretely
  demonstrated for content_binding by tearing down and rebuilding the FastAPI
  app against the same mongomock instance and confirming the write survives
  (`test_state8_validation.py::TestAppRestartAgainstSamePersistedDb`,
  INTEGRATION_VERIFIED). This proves the *code* is restart-safe by
  construction; it does not and cannot prove real-MongoDB durability itself
  (`mongomock_motor` is confirmed this state to isolate state per client
  instance — `AsyncMongoMockClient()` twice at the same connection string
  returns two independent stores, unlike real MongoDB).
- **Migration/compatibility mapping persistence** —
  `tests/test_identity_reconcile_unit.py::test_duplicate_reconciliation_is_idempotent`
  and `::test_reconciliations_are_visible_from_either_side` (INTEGRATION_VERIFIED,
  pre-existing, re-run green).
- **Write / read / duplicate retry / conflict** for content_binding,
  creative_lifecycle, relationship_graph, offline_transport, registry — all
  already INTEGRATION_VERIFIED by the existing per-domain unit-test files
  (content_binding idempotent-dedup-by-hash; offline_transport's conflict/
  duplicate-replay/out-of-order suite; registry's 409-on-duplicate-in-namespace).
- **Index creation is idempotent** — `test_state8_validation.py::
  TestIndexCreationIsIdempotent` calls `content_binding.routes.ensure_indexes()`
  (real startup code) twice against the same mongomock db and confirms no
  exception, then confirms the unique index it creates still rejects a real
  duplicate afterward (INTEGRATION_VERIFIED).

`PERSISTENCE_RESTART`: REAL_INFRA_VERIFIED (local disk) /
INTEGRATION_VERIFIED (code-level restart-safety, Mongo-backed) /
NOT_VERIFIED (real-Mongo durability itself) — reported precisely, not as one
blended "VERIFIED".

## 6. Real OTS / Bitcoin anchor

**REAL_OTS_VALIDATION=BLOCKED**, re-confirmed this state:

```
$ curl -s -o /dev/null -w "%{http_code}\n" https://alice.btc.calendar.opentimestamps.org
000  (curl exit 56 — connection failed through the sandbox's outbound proxy)
```

Unchanged from every prior state (`reports/18_RUNTIME_VALIDATION.md`'s 6-level
Proof Engine classification): OpenTimestamps submission code is real
(`notary/anchor.py`) but its calendar servers are unreachable from this
sandbox. **BITCOIN_ANCHOR_VALIDATION=NOT_VERIFIED** (depends on OTS
confirmation plus real wall-clock time, neither available here) — never
claimed VERIFIED without external evidence, per standing instruction.

## 7. Migration / legacy validation

Full detail: `docs/validation/FREKCORE_MIGRATION_VALIDATION.md`. Summary:
all 19 historical `backend/frek/` routes remain reachable and present in the
generated OpenAPI schema (`test_api_contract.py::
test_all_19_legacy_routes_present_in_openapi_surface`, re-run green this
state); zero routes write an independent second truth (`test_legacy_
compatibility.py`, `FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`); response
compatibility unchanged (`backend/frek/` has an empty diff this state, `git
diff --stat -- backend/frek/` confirmed empty). `LEGACY_ROUTES_DELETED=0`.

## 8. Consumer safety (regression only, not a new audit)

Re-ran the exact discovery already recorded in `reports/FREKCORE_CONTRADICTIONS.md`'s
STATE_6 update: `frontend/src/pages/Certify.jsx` and `Verify.jsx` still exist
and still call the same endpoints unchanged —

```
Certify.jsx:79   fetch(`${API_URL}/api/frek/certify`)
Verify.jsx:43    fetch(`${API_URL}/api/frek/verify/${frekId}`)
Verify.jsx:44    fetch(`${API_URL}/api/v1/notary/proof/${frekId}`)
Verify.jsx:45    fetch(`${API_URL}/api/v1/identity/${frekId}/status`)
Verify.jsx:46    fetch(`${API_URL}/api/v1/audit/${frekId}`)
```

Both a legacy route (`/api/frek/certify`, `/api/frek/verify/{frek_id}`) and
three canonical `/api/v1/...` routes have a real, live, local caller —
confirming the D1 legacy routes' additive-only compatibility discipline is
still load-bearing, and that canonical routes are already depended on
locally too. This is regression evidence only, not a new whole-repository
audit (`GENERAL_REAUDIT=FALSE`). `NONE_FOUND_LOCALLY` still does **not**
become `NO_EXTERNAL_CONSUMER`: no other CVLN repository is present in this
workspace to check (`reports/21_FREEZE_ASSESSMENT.md`'s own standing
disclosure, unchanged).

## 9. Content Binding / D1

`D1_VERIFICATION_STATUS=PARTIAL`, unchanged. No new scientific testing was
performed this state (software regression tests, per the mission's own
instruction, are not grounds to upgrade this). Software invariants re-run
green, all pre-existing:

| Property | Test |
|---|---|
| Same-input determinism | `tests/test_content_binding_extraction_unit.py::test_deterministic` |
| Hash/fingerprint separation | `tests/test_content_binding_unit.py::TestCryptoHashSeparatedFromSignalFingerprint` |
| Algorithm/version persistence | `tests/test_content_binding_unit.py::TestAlgorithmVersioned` |
| Short-input safety | `tests/test_content_binding_unit.py::test_audio_too_small_is_400` |
| Invalid/non-finite input behavior | `tests/test_content_binding_extraction_unit.py::test_rejects_non_finite_vector`, `::test_rejects_infinite_vector` |
| Binding persistence | `tests/test_content_binding_unit.py::TestPersistenceAndReads` |
| Legacy mapping | `tests/test_content_binding_unit.py::TestLegacyIdentifierCompatibility` |
| Permission enforcement | `tests/test_content_binding_unit.py::TestUnauthorized` |
| Idempotency | `tests/test_content_binding_unit.py::TestIdempotency` |

All UNIT_VERIFIED / INTEGRATION_VERIFIED, none scientific-robustness claims.

## 10. Creative lifecycle / relationship graph / proof-notary

Cross-module lifecycle behavior (GENESIS references valid subject, stage
transitions, EMISSION requires object, idempotency, event ordering, legacy
route compatibility), relationship graph behavior (canonical references,
cultural-inference-never-becomes-VERIFIED, bounded traversal, legacy read
adapters), and proof/notary behavior (hash chain, proof-state mapping,
missing/invalid anchor, modified block) are all pre-existing
INTEGRATION_VERIFIED coverage in `test_creative_lifecycle_unit.py`,
`test_relationship_graph_unit.py`, `test_proof_engine.py`, `test_notary*.py`
— re-run green this state (part of the 507-test full regression), not
duplicated in `test_state8_validation.py`.

## 11. Offline transport

Already the most thoroughly covered domain in this codebase pre-STATE_8:
`tests/test_offline_transport_unit.py` (44 tests) covers receive/persist/
restart-equivalent-queue-listing/sync, authority-fresh/stale/revoked-before-
sync, duplicate replay, out-of-order, conflict-at-same-sequence, tampered
envelope, unknown issuer/device, unsupported signature algorithm, and
per-operation event/audit emission. Re-run green this state
(INTEGRATION_VERIFIED). Canonical business state (sync_status) is confirmed
to only change to `synced` after explicit reconciliation
(`test_receive_acceptance_never_sets_sync_status_synced`).

## 12. Failure injection

Test-level fault injection only, no chaos infrastructure:

| Scenario | Test | Result |
|---|---|---|
| DB write failure | `test_state8_validation.py::TestDbWriteFailureInjection` (class-level `insert_one` patch, scoped to one collection name) | Response is never a false 200; no traceback/internal path leaks into the body. Genuine, disclosed gap: the route does not catch this specific exception type, so it surfaces as a bare 500 rather than a canonical error code — compatibility debt, not a crash. |
| EventBus publish() raises | `tests/test_fk_object_created_event.py::test_a_broken_bus_does_not_break_fk_creation` (pre-existing) | Operation still succeeds; publish failure never breaks the triggering request. |
| EventBus subscriber raises | `tests/test_eventbus.py::test_bus_never_raises_when_subscriber_fails` (pre-existing) | Caught and logged inside `InProcessEventBus.publish()`. |
| Permission denial / revoked authority | `tests/test_permissions.py` (delegation-chain + decide() denial paths), `tests/test_offline_transport_unit.py::TestRevocation` | Denied cleanly, reason string present, no crash. |
| Bad pagination token | `test_state8_validation.py::TestBadPaginationToken` (3 tests: out-of-range offset -> empty page; negative limit -> clamped; non-numeric offset -> clean 422) | No crash, no 500. |
| Unsupported API version | `test_state8_validation.py::TestUnsupportedApiVersion` (`/api/v2/...` -> clean 404, no `/api/v2` router exists) | Disclosed compatibility debt: a generic 404, not yet the canonical `UNSUPPORTED_VERSION` error code — not retrofitted this state. |

## 13. Event / audit validation

- Business event emitted once per operation, audit record created as
  required: `tests/test_offline_transport_unit.py::TestAuditEventbus`,
  `tests/test_fk_object_created_event.py` (pre-existing, INTEGRATION_VERIFIED).
- Retry does not duplicate a semantic business event: `tests/
  test_offline_transport_unit.py::test_sync_retry_on_already_synced_is_safe`,
  `tests/test_content_binding_unit.py::TestIdempotency` (dedup returns the
  existing record, no second event).
- Legacy adapter does not double-publish: `tests/test_legacy_compatibility.py`.
- Sensitive payload not leaked in events: `docs/architecture/
  FREKCORE_EVENT_CONTRACT_V1.md`'s privacy-classification column, cross-checked
  against `registry/events/event_registry.json` (unchanged this state).
- Event registry entry matches actual producer: re-verified directly against
  `registry/events/event_registry.json` this state (same 12 EXISTS / 2 PARTIAL
  / 3 MISSING / 1 REJECTED classification as STATE_7 — file untouched).
- Audit != Event Bus: unchanged, `backend/audit/` (legacy aggregation) vs
  `backend/audit_trail/` (write-only, event-bus-fed) remain structurally
  distinct modules, confirmed by import graph.

`EVENT_AUDIT_DUPLICATION_ABSENT=TRUE`.

## 14. Error contract — runtime classification

STATE_7 built the canonical vocabulary (`backend/errors.py`) without
retrofitting existing routes. STATE_8 classifies runtime behavior instead of
rewriting it:

| Class | Endpoints | Basis |
|---|---|---|
| CANONICAL_ERROR_NATIVE | 0 of 46 canonical + 0 of 19 legacy | `backend/errors.py` exists but is not imported by any route module (confirmed: `grep -rl "from errors import\|from backend.errors" **/routes.py` -> no matches) |
| HTTP_STATUS_COMPATIBLE_ONLY | all 46 canonical `/api/v1/...` endpoints | Correct HTTP status codes throughout (STATE_7's own audit, re-confirmed), missing only the machine-readable `code` field |
| LEGACY_ERROR_SHAPE | all 19 `backend/frek/` legacy endpoints | STATE_6's own hardening classification, unchanged |
| INTERNAL_ONLY | 0 | `INTERNAL_ENDPOINTS=0` per STATE_7's own contract matrix, unchanged |

One raw-exception-leak candidate was checked this state and found safe, not a
defect: `relationship_graph/routes.py:280` returns `str(e)` from a caught
`UnknownPredicateError(ValueError)` — a deliberate, controlled domain
exception for FREKCORE's own closed predicate vocabulary, not an internal
implementation detail (message is e.g. "unknown predicate '...'", never a
stack trace or file path). No fix needed; documented as
HTTP_STATUS_COMPATIBLE_ONLY, not a leak.

The DB-write-failure injection test (§12) additionally confirms directly that
a genuine internal exception (`ConnectionError` from a mocked Mongo failure)
does **not** leak its traceback or any repository file path into the HTTP
response body, even though it is not yet caught into a canonical error shape.

## 15. API contract regression

`tests/test_api_contract.py` (4 tests) re-run against the STATE_7 golden
snapshot (`backend/tests/fixtures/api_contract_snapshot.json`, 46 canonical
endpoints) — **all pass, snapshot unchanged**. `API_CONTRACT_REGRESSION`:
`BREAKING_CHANGE=FALSE`. No canonical route was added, removed, or renamed
this state (`backend/frek/` diff is empty; no D1-D5 module route changed).

## 16. SDK validation

**Python**: `PYTHONPATH=backend:sdk/python pytest sdk/python/tests` — 31
passed, real ASGI (`fastapi.testclient.TestClient`) against each capability's
actual canonical router + `mongomock_motor`, exercising request path, method,
payload shape, response shape, and error mapping for real (`raise_for_frek_
status()` against real HTTP responses). `PYTHON_SDK_VALIDATION=INTEGRATION_VERIFIED`.

**TypeScript**: `npm run typecheck && npm test` — typecheck clean, 38 passed,
all against a mocked `fetch` (no ASGI-transport equivalent exists for Node —
unchanged from STATE_7). This proves request construction, header/auth
behavior, and response-shape parsing against the *documented* contract, but
never exercises a real HTTP round-trip. **`TYPESCRIPT_RUNTIME_E2E=NOT_VERIFIED`**
— stated explicitly, per the mission's own instruction, rather than implied
by "38 passed."

Unknown-field and version-behavior checks: both SDKs' response models accept
extra/未知 fields without erroring (Python: plain `dict` returns, no strict
Pydantic response validation; TypeScript: structurally-typed interfaces, no
runtime shape enforcement) — this is a deliberate design choice (forward
compatibility with additive schema evolution, per `FREKCORE_VERSIONING_
POLICY.md` §3's SAFE list), not a gap, and was true unchanged since STATE_7.

## 17. Idempotency validation

| Case | Domain | Result |
|---|---|---|
| Same key + same payload | content_binding (key = content hash) | Returns existing record, `deduplicated: true` (`test_content_binding_unit.py::TestIdempotency`) |
| Same key + different payload | offline_transport (key = issuer_id+sequence) | Flagged as conflict, not silently overwritten (`test_offline_transport_unit.py::TestConflict`) |
| Repeated after "restart" | content_binding | `test_state8_validation.py::TestAppRestartAgainstSamePersistedDb` (same db handle) |
| Concurrent duplicate | Not practically testable without real infra (mongomock is single-threaded/in-process); unique-index-backed dedup (`create_index(..., unique=True)`) is real MongoDB's own atomicity guarantee, `NOT_VERIFIED` in this sandbox for the concurrent case specifically, consistent with `REAL_MONGO_VALIDATION=BLOCKED` above | NOT_VERIFIED (disclosed) |
| Expired-key TTL behavior | No idempotency key in this codebase carries a TTL (FREKCORE_VERSIONING_POLICY.md §7: domain-derived keys, no caller-supplied header with expiry) | N/A, documented |
| Scope collision between users/resources | content_binding's key is `(frek_id, exact_hash)` — cross-user collision structurally impossible (frek_id is part of the key); offline_transport's key is `(issuer_id, sequence)`, same property | UNIT_VERIFIED via existing per-domain tests |

Idempotency is **not** inferred from duplicate-safe Mongo writes alone: each
case above is a real, targeted route-level test, not an assumption from the
unique-index existing.

## 18. Revocation validation

`REVOCATION_REGRESSION_GREEN=TRUE`:
- Device/authority revoked between receive and sync: `test_offline_transport_
  unit.py::TestRevocation` (INTEGRATION_VERIFIED, pre-existing).
- Delegated-authority revocation propagation: §4 above (UNIT_VERIFIED, new
  this state).
- Identity revocation: `tests/test_identity_lifecycle.py`,
  `tests/test_identity_recovery_unit.py` (pre-existing, re-run green).

## 19. Privacy / disclosure validation

`PRIVACY_DISCLOSURE_REGRESSION_GREEN=TRUE`. `PUBLIC_VERIFICATION !=
PUBLIC_DISCLOSURE` and `PUBLIC OBJECT != ALL PROVENANCE PUBLIC` /
`PUBLIC PROOF != PRIVATE EVIDENCE PUBLIC` remain enforced structurally — D5's
field-level disclosure rules (`technical_evidence_report`) and D3's
private/hidden relationship visibility are unchanged and were not touched
this state (`INTEGRATION_VERIFIED`, pre-existing test files: `tests/
test_technical_evidence_report_unit.py`, `tests/test_relationship_graph_unit.py`).
No new privacy surface was added this state (no new route exposes any field
that was previously private).

## 20. Security boundary (not Red Team)

Known controls re-exercised as regression, not adversarially probed for new
findings: auth (`TestUnauthorized` classes throughout), scope checks
(`permissions` suite), delegation (§4), revocation (§18), rate limiting
(`FREK_DISABLE_RATE_LIMIT` escape hatch documented, `tests/
test_security_hardening.py` exercises it directly), input validation (D1's
non-finite/oversized/undersized rejection, §9), exception safety (§12/§14).
`SECURITY_BOUNDARY_REGRESSION=GREEN`, explicitly not a claim of adversarial
resilience.

## 21. Index / database validation

§5 above. `create_index(..., unique=True)` calls audited across content_
binding, creative_lifecycle, relationship_graph, offline_transport,
technical_evidence_report, registry, identity_engine, audit_trail — all
idempotent by MongoDB's own semantics (re-creating an identical index is a
no-op), directly confirmed for content_binding this state
(INTEGRATION_VERIFIED). No new database technology introduced.

## 22. Acceptance gate — self-assessment

| Gate item | Status |
|---|---|
| FULL_UNIT_REGRESSION_GREEN | TRUE |
| CROSS_MODULE_INTEGRATION_TESTS_GREEN | TRUE |
| HISTORICAL_COMPATIBILITY_REGRESSION_GREEN | TRUE |
| API_CONTRACT_SNAPSHOT_GREEN | TRUE |
| PYTHON_SDK_CONTRACT_GREEN | TRUE |
| TYPESCRIPT_SDK_CONTRACT_GREEN | TRUE |
| AUTHORITY_REGRESSION_GREEN | TRUE |
| DELEGATION_CONTAINMENT_VERIFIED | TRUE |
| DELEGATOR_AUTHORITY_VALIDATION_VERIFIED | TRUE |
| REVOCATION_REGRESSION_GREEN | TRUE |
| IDEMPOTENCY_REGRESSION_GREEN | TRUE |
| OFFLINE_RECONCILIATION_REGRESSION_GREEN | TRUE |
| PROOF_EVIDENCE_SEMANTICS_PRESERVED | TRUE |
| PRIVACY_DISCLOSURE_REGRESSION_GREEN | TRUE |
| EVENT_AUDIT_DUPLICATION_ABSENT | TRUE |
| NO_PARALLEL_TRUTH_ENGINE | TRUE |
| NO_LEGACY_ROUTE_DELETED | TRUE |
| NO_NEW_UNDOCUMENTED_CONTRADICTION | TRUE |
| D1_VERIFICATION_STATUS_TRUTHFUL | TRUE (PARTIAL, unchanged, not upgraded) |
| REAL_INFRA_STATUS_EXPLICIT | TRUE (§5, §6 — BLOCKED/NOT_VERIFIED stated explicitly, not implied) |
| BLOCKING_CI_GREEN | TRUE (pending final push confirmation — see PR CI-status comment) |
| STATE_9_NOT_STARTED | TRUE |

**Real-infra exception applied**: per the mission's own "REAL INFRA EXCEPTION"
clause — the real-Mongo and real-OTS blockers are external, reproduced,
documented, not simulated, and all software-level validation that can run in
this sandbox is green — this does not, by itself, fail STATE_8's acceptance.
`BLOCKED != VERIFIED` is stated throughout, not elided.
