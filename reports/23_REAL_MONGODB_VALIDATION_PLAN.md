# 23 — Real MongoDB Validation Plan (execution-ready, not yet run)

Status: **BLOCKED on infrastructure, not attempted this phase**. `reports/16_INTEGRATION_TEST_BASELINE.md` §1 re-confirmed the exact blocker as of this phase: this sandbox's Docker daemon runs, but every image pull (`docker pull mongo:7`) returns `403 Forbidden` from `production.cloudfront.docker.com` — a network-policy boundary, not a transient failure or something fixable by retrying. Every test result in this repository against a real MongoDB is, as of this document, `mongomock`-substituted. This plan exists so that validation can start immediately, with no design work left to do, the moment a real MongoDB becomes reachable (a different sandbox, a CI runner with registry access, or this sandbox's policy changing). **No claim anywhere in this repository should describe real-MongoDB guarantees as VERIFIED until this plan has actually been executed and its results recorded.**

---

## 1. Environment requirements

- **MongoDB 7.0**, matching `docker-compose.yml`'s pinned `mongo:7.0` image — not a newer major version, to avoid validating against behavior this deployment doesn't actually run.
- **Reachable via TCP**, not just via a mocked driver substitution — the single biggest gap `mongomock` cannot close (see §4).
- One of, in order of preference:
  1. `docker compose up mongo` in this repo, if Docker registry access is available (the `docker-compose.yml` `mongo` service already exists, unmodified, at repo root).
  2. A standalone `mongod` binary if Docker itself is unavailable but package installation is not blocked (`apt-get install mongodb-org` or equivalent, MongoDB 7.0 release channel).
  3. A managed MongoDB instance (Atlas free tier or equivalent) reachable from this environment, if outbound TCP to a MongoDB port is permitted even when Docker registry pulls are not — worth checking independently, since the two blocks (registry pull vs. arbitrary outbound TCP) are not necessarily the same policy.
- Python env: `pip install -r backend/requirements.txt` (the **real** requirements file, not `requirements-ci.txt`) minus the one still-private `emergentintegrations` line (`reports/15_DEPENDENCY_REMEDIATION.md` — its import was already made lazy in `services/webhook.py`, so its absence does not block server startup, only Stripe checkout's own code path).
- Env vars (matching `docker-compose.yml`'s `backend` service, real secrets not the `dev-only` placeholders used for `mongomock` runs this phase):
  ```
  MONGO_URL=mongodb://localhost:27017      # or the real service's actual host:port
  DB_NAME=frekcore_realmongo_validation    # a dedicated, disposable DB name — never frekcore/frekcore_prod
  SECRET_KEY=<real random value>
  FREK_EMAIL_SALT=<real random value>
  CORS_ORIGINS=http://localhost:3000
  FREK_ENV=development
  FREK_CLIENT_KILTIKONET_SECRET=<value>
  FREK_CLIENT_CVLBRAIN_SECRET=<value>
  FREKCORE_SECRET_KILTIKONET=<value>        # backend/core/ ingest source secret, distinct from the OAuth2 client secret above
  FREK_PASSPORT_KEY_PATH=/tmp/frekcore_realmongo_passport_key.pem
  REACT_APP_BACKEND_URL=http://localhost:8001
  TEST_BACKEND_URL=http://localhost:8001   # some test files read this name instead
  ```
- **Do not reuse a `DB_NAME` that has ever held real production or demo data.** This plan is destructive by design in its own scratch database (see §6).

## 2. Commands

Run in this exact order; each step's success is a precondition for the next.

```bash
# 1. Bring up real MongoDB (pick the environment-requirements option that applies)
docker compose up -d mongo
# ...or: mongod --dbpath /tmp/frekcore_realmongo_data --port 27017 &

# 2. Confirm real TCP connectivity BEFORE starting the app (catches a misconfigured
#    MONGO_URL immediately, rather than 90 seconds into a test run)
python3 -c "
from pymongo import MongoClient
c = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
print(c.admin.command('ping'))
"

# 3. Install the REAL requirements (not requirements-ci.txt)
cd backend
pip install -r requirements.txt   # emergentintegrations line will fail to resolve — expected, see §1; strip it first if pip aborts the whole install rather than skipping one line

# 4. Start the real server against the real MongoDB (no mongomock patch — this is
#    the actual scripts/ entrypoint the real deployment uses, not
#    scripts/run_dev_server_mongomock.py)
MONGO_URL=... DB_NAME=frekcore_realmongo_validation SECRET_KEY=... FREK_EMAIL_SALT=... \
  CORS_ORIGINS=http://localhost:3000 FREK_ENV=development \
  FREK_CLIENT_KILTIKONET_SECRET=... FREK_CLIENT_CVLBRAIN_SECRET=... \
  FREKCORE_SECRET_KILTIKONET=... FREK_PASSPORT_KEY_PATH=/tmp/frekcore_realmongo_passport_key.pem \
  PORT=8001 python3 -m uvicorn server:app --host 0.0.0.0 --port 8001

# 5. Confirm the server's own startup log shows every index-creation block completing
#    with no errors (grep for "indexes crees", "Index ... has incompatible options",
#    "Cannot create unique index" — the last two are the _ensure_unique_sparse_index
#    guard's own failure messages, server.py:434, and must NOT appear on a fresh DB)

# 6. Run the full test suite, ALL markers, against the real server
cd backend
REACT_APP_BACKEND_URL=http://localhost:8001 TEST_BACKEND_URL=http://localhost:8001 \
  MONGO_URL=... DB_NAME=frekcore_realmongo_validation SECRET_KEY=... \
  FREKCORE_SECRET_KILTIKONET=... \
  python3 -m pytest -m "" -v --tb=short 2>&1 | tee /tmp/real_mongo_run_$(date +%Y%m%d_%H%M).log

# 7. Coverage pass (blocking-scope modules only, matching CI's own gate exactly —
#    this should already be green from mongomock runs; re-running against real
#    Mongo is a sanity check, not expected to change the number materially)
python3 -m pytest --cov=registry --cov=eventbus --cov=permissions --cov=audit_trail \
  --cov=proof_engine --cov=storage --cov=observability \
  --cov-report=term-missing --cov-fail-under=90
```

## 3. Expected test set

As of this phase, `pytest --collect-only -q` (unfiltered, all markers) collects **528 tests** (123 `unit` + 405 auto-marked `integration` per `conftest.py`'s `pytest_collection_modifyitems`), excluding `tests/test_ecosystem.py` (the one module that cannot even be collected without the private `emergentintegrations` package — `pytest.ini`'s own `--ignore`, unrelated to real-vs-mock Mongo). This number will have grown further by the time this plan is actually executed; re-run `pytest --collect-only -q` first and use *that* count as the run's own baseline, not this document's stale snapshot.

Expected outcome, calibrated against `reports/16_INTEGRATION_TEST_BASELINE.md`'s Run 4 (the last full classification against `mongomock`, before this phase's P1 additions):
- **The `mongo` pytest fixture-dependent tests** (`test_fingerprint.py::TestConsent::test_revoke_triggers_purge`, `test_fingerprint.py::TestAnomalyAndDevice::test_anomaly_bot_signal_high_for_regular_cadence`, and any other test using a bare `pymongo.MongoClient(os.environ["MONGO_URL"])` fixture) — these were the very cases `mongomock` could **not** satisfy (no real TCP listener). **This is the primary reason this plan exists**: expect these to go from ERROR (mongomock) to a real PASS/FAIL against real Mongo — this is new, real information, not a re-confirmation.
- Every other currently-green test (against `mongomock`) is expected to **stay green** — a regression here (a test that passes against `mongomock` but fails against real Mongo) is itself a finding worth its own investigation, since it would mean `mongomock`'s behavior diverged from real MongoDB's in a way this codebase was silently relying on.
- Known, already-classified, non-Mongo-related failures from Run 4 (`reports/16_INTEGRATION_TEST_BASELINE.md` §4/§7 — RP-ID/environment mismatches, the OTS-calendar network dependency now circuit-breaker-guarded but still genuinely blocked by this sandbox's own outbound-network policy) are expected to reproduce identically; do not re-litigate those root causes here, cross-reference them.

## 4. Indexes / uniqueness / atomicity / concurrency / persistence checks

This is the actual point of running against real MongoDB — `mongomock` cannot exercise most of these with full fidelity.

### 4a. Index creation (every module's own `ensure_indexes()`/startup block)
Confirm every index below is present with `db.<collection>.getIndexes()` after server startup, matching what the code declares (list built from a direct `grep -rn "unique=True"` across `backend/`, re-verify this list itself hasn't drifted before treating it as complete):

| Collection | Field(s) | Unique | Source |
|---|---|---|---|
| `frek_identities` | `frek_id` | yes | `server.py:550` |
| `frek_clients` | `client_id` | yes | `server.py:556` |
| `badges` | `badge_id` | yes | `server.py:560` |
| `marchands` | `marchand_id` | yes | `server.py:572` |
| `payment_transactions` | `session_id` | yes | `server.py:573` |
| `staff` | `agent_id` | yes | `server.py:585` |
| `scans` | `client_uuid` (partial, string-typed only) | yes | `server.py:587`, via `_ensure_unique_sparse_index` |
| `transactions` | `client_uuid` (partial, string-typed only) | yes | `server.py:588`, via `_ensure_unique_sparse_index` |
| `frek_heritage_declarations` | `declaration_id` | yes | `server.py:614` |
| `frek_heritage_transfers` | `transfer_id` | yes | `server.py:617` |
| `frek_sync_mapping` | `(service, frek_id)` compound | yes | `server.py:622` |
| `frek_sync_cursor` | `service` | yes | `server.py:625` |
| `frek_persons` | `frek_id` | yes | `identity_engine/routes.py:106` |
| `frek_persons_challenges` | `challenge` | yes | `identity_engine/routes.py:113` |
| `registry_objects` | `(namespace, frek_id)` compound | yes | `registry/routes.py:51` (P1, this phase) |
| `frek_fingerprint` | `frek_id` | yes | `fingerprint/routes.py:43` |
| `frek_consent` | `frek_id` | yes | `fingerprint/consent.py:15` |
| `frek_device_observations` | `(frek_id, device_hash)` compound | yes | `fingerprint/device.py:21` |
| `frek_coupling_observations` | `(frek_id, nfc_scan_id)` compound | yes | `fingerprint/layers.py:15` |
| `frek_geo_consent` | `frek_id` | yes | `geo/service.py:23` |
| `frek_geo_observations` | `idempotency_key` | yes | `geo/service.py:24` |
| `frek_subjects` | `frek_id` | yes | `core/service.py:23` |
| `frek_events` | `idempotency_key` | yes | `core/service.py:25` |
| `frek_count_events` | `idempotency_key` | yes | `counter/service.py:60` |
| `frek_count_subjects` | `frek_id` | yes | `counter/service.py:64` |
| `frek_count_rules` | `action` | yes | `counter/service.py:65` |
| `eudi_offers` | `pre_authorized_code` | yes | `eudi/service.py:31` |
| `eudi_tokens` | `access_token` | yes | `eudi/service.py:33` |
| `notary_blocks` | `height`, `block_hash` (two separate unique indexes) | yes | `notary/chain.py:62-63` |
| `audit_trail_events` (or the module's actual collection name) | `event_id` | yes | `audit_trail/mongo_recorder.py:29` |

For each: (a) confirm the index exists with the exact expected shape (`unique`, compound field order, `partialFilterExpression` where applicable), (b) attempt a real duplicate insert and confirm MongoDB itself rejects it with `DuplicateKeyError` (not just that application code happens to check first — `mongomock` may enforce uniqueness with different strictness than real MongoDB, this is exactly the divergence real-Mongo validation exists to catch).

### 4b. `_ensure_unique_sparse_index`'s own preflight guard (`server.py:434`)
This function is itself untested against real MongoDB's aggregation pipeline behavior. Specifically validate:
- On a **fresh** `scans`/`transactions` collection (no pre-existing duplicates), startup creates the partial unique index cleanly with no error.
- On a collection **seeded with a duplicate** `client_uuid` value beforehand (simulate the exact scenario this guard exists for), startup raises `RuntimeError` and does **not** create the index — confirm the server refuses to silently proceed with a missing safety index, and that the error message correctly points at `backend/migrations/20260824_unique_index_preflight.py`.
- Run `backend/migrations/20260824_unique_index_preflight.py` itself against the seeded-duplicate state and confirm it actually resolves the duplicates (read `20260824_unique_index_preflight.md` alongside it for the documented expected behavior before running).

### 4c. Atomicity
- **`registry/routes.py`'s `create_registry_object`**: the existence-check (`find_one`) and the `insert_one` are two separate operations, not a single atomic upsert. Real-Mongo-only concurrency test: fire two concurrent `POST /api/v1/registry/objects/{namespace}` requests with the **same explicit `frek_id`** in the payload (simultaneously, e.g. via `asyncio.gather` or two threads) and confirm exactly one succeeds (`201`) and the other gets `409` from the unique index itself (not a race where both read "not found" and both insert, which the unique index should prevent at the database layer even though the application-level check alone would not) — this is precisely the kind of race `mongomock`'s simpler single-process model may not reproduce faithfully.
- **`counter/service.py`'s idempotency-key pattern** (`frek_count_events`, `frek_events`): same concurrent-duplicate-write test, using the same `idempotency_key` twice simultaneously — confirm exactly one write lands.
- **`notary/chain.py`'s block height sequencing**: concurrent calls to whatever increments `height` — confirm no two blocks are ever created with the same `height` (the unique index on `height` should guarantee this at the DB layer; verify it does under real concurrent load, not just sequential calls).

### 4d. Concurrency (beyond atomicity — throughput/behavior under load)
- Rate limiting (`backend/security/policies.py:check_rate_limit`) is DB-backed (a sliding window stored in Mongo, per earlier session work on `fingerprint_observe`/`geo_observe`/`checkout_create`). Fire concurrent requests against a rate-limited route (e.g. `/core/fingerprint/observe/device`) at a rate exceeding the configured limit and confirm the DB-backed counter correctly rejects the excess under real concurrent writes — `mongomock`'s lack of true concurrent-access semantics is exactly the gap here.
- `notary/anchor.py`'s `_CalendarCircuitBreaker` (this phase's own addition) — not a MongoDB concern directly, but confirm its state persists correctly if the breaker's counters are ever backed by Mongo rather than in-process memory (check the actual implementation before assuming; if it's in-process-only, this bullet doesn't apply and should be struck, not silently skipped).

### 4e. Persistence (the actual reason `mongomock` was flagged as insufficient from day one)
- **Restart survival**: after a full test run, stop the server process (not the MongoDB process), restart it against the **same** `DB_NAME`, and confirm previously-created records (`frek_identities`, `frek_persons`, `registry_objects`, `fk_objects`, notary blocks) are still present and correctly shaped — this is the one guarantee `mongomock` (in-process, cleared on process exit) can never validate at all, by construction.
- **Aggregation pipeline fidelity**: `scripts/run_dev_server_mongomock.py`'s own docstring already flags this as a known `mongomock` gap ("Aggregation pipeline operator coverage is a mongomock subset, not 1:1"). Specifically re-run any test exercising an aggregation pipeline (`_ensure_unique_sparse_index`'s own `$group`/`$match` duplicate-detection pipeline is one; check `grep -rn "\.aggregate(" backend/` for the complete list at execution time) and confirm identical results to the `mongomock` run.
- **Index enforcement fidelity**: `mongomock`'s own README documents that its constraint enforcement is not a byte-for-byte match to real MongoDB's — this is the closest a run through this plan gets to actually confirming (rather than assuming) that every `unique=True` index in §4a behaves identically under real MongoDB.

## 5. What this plan does NOT cover

- Load/stress testing at production-representative volume — this plan validates correctness under real MongoDB semantics, not capacity planning. A separate exercise if ever needed.
- Real Bitcoin/OpenTimestamps anchoring end-to-end (still blocked by this sandbox's own outbound network policy independent of MongoDB, per `reports/16_INTEGRATION_TEST_BASELINE.md`) — orthogonal to this plan, do not conflate the two blockers when reporting results.
- Multi-node MongoDB (replica sets, sharding) — `docker-compose.yml` runs a single `mongo` instance; this plan validates against that same topology, not a production-representative cluster, unless the real deployment target is confirmed to also be single-node.

## 6. Rollback / cleanup steps

1. **Never point this plan at a `DB_NAME` that isn't disposable** (§1) — this is the primary safeguard; if followed, cleanup is simply dropping that one database.
2. After the run (success or failure), drop the scratch database explicitly rather than leaving it for the next run to silently inherit stale state:
   ```bash
   python3 -c "
   from pymongo import MongoClient
   MongoClient('mongodb://localhost:27017').drop_database('frekcore_realmongo_validation')
   "
   ```
3. If using `docker compose up -d mongo`: `docker compose down -v` removes the container and its named volume (`frekcore_mongo`) together — confirm this is actually wanted (it deletes the volume's on-disk data) before running; `docker compose down` alone (no `-v`) stops the container but preserves the volume, useful if a second run against the same persisted state is intended (e.g. specifically to re-test §4e's restart-survival case without recreating fixtures from scratch).
4. If §4b's duplicate-key migration test was run, confirm `backend/migrations/20260824_unique_index_preflight.py` was run only against the scratch database — re-read its own `.md` companion doc for any migration-specific rollback notes before assuming a clean drop of the whole DB is sufficient (a migration script that also writes outside MongoDB, e.g. a log file, would need that cleaned up separately).
5. Record the run's full log (`/tmp/real_mongo_run_*.log` from §2 step 6) as this report's own future evidence trail — append a dated "Run N" section to *this* document (matching `reports/16_INTEGRATION_TEST_BASELINE.md`'s own convention of Run 1/2/3/4 sections) rather than creating a new report file, so the plan and its execution history stay in one place.
6. Update `reports/21_FREEZE_ASSESSMENT.md` and `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #1 only after a run has actually completed and its results are recorded here — never mark either as "real-Mongo verified" based on this plan's existence alone.
