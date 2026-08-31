# 16 — Integration Test Baseline (Phase 3, Priority 2 & Priority 3 evidence)

## 1. Why this is a `mongomock`-backed run, not a real MongoDB

`docker-compose.yml` defines a real `mongo` service. This sandbox's Docker daemon runs (`dockerd &`, confirmed working for daemon operations), but **every image pull returns `403 Forbidden`** from `production.cloudfront.docker.com` — reconfirmed this phase with a direct `docker pull mongo:7`:
```
failed to copy: httpReadSeeker: failed open: failed to do request: Get "https://production.cloudfront.docker.com/registry-v2/...": Forbidden
```
This is the same network-policy boundary documented in `reports/15_DEPENDENCY_REMEDIATION.md` for the private PyPI package — a hard boundary, not a technical failure to route around (per this sandbox's own proxy README instruction to never retry policy denials). `scripts/run_dev_server_mongomock.py` is the documented, clearly-labeled substitute: it monkeypatches `motor.motor_asyncio.AsyncIOMotorClient` to `mongomock_motor.AsyncMongoMockClient` before importing the real `server.py`, then serves the real, unmodified application (240 routes) with uvicorn. Its own docstring lists the known gaps (no real network/auth/TLS, partial aggregation-operator coverage, no real index-enforcement parity). Every result below is evidence of **real FastAPI/Pydantic/route/business-logic behavior**, filtered through that one substitution — not proof of real-MongoDB behavior.

## 2. Run 1 (discarded) — a harness bug, not a finding

The first attempt produced 131 spurious auth failures. Root cause: the mongomock server process was started (with real env-var secrets exported) in one Bash tool call; `pytest` was launched in a separate Bash tool call whose shell did not inherit those exports (this harness's own documented behavior: "Shell state (env vars, functions) does not persist" across tool calls). `FREK_CLIENT_KILTIKONET_SECRET`/`FREK_CLIENT_CVLBRAIN_SECRET` were empty in the pytest process, so every OAuth2 token request got `401 Secret invalide`, cascading into ~131 fixture-setup errors. Not a code finding — discarded, re-run with every export in the same shell invocation as `pytest`.

## 3. Run 2 (baseline "as-is") — the real, valid Priority 2 baseline

Command (single Bash call, all env vars exported inline):
```
MONGO_URL=mongodb://mock/ DB_NAME=frekcore_mongomock2 SECRET_KEY=dev-only ... \
python3 -m pytest -m integration -q --ignore=tests/test_ecosystem.py
```
(`--ignore=tests/test_ecosystem.py`: the one module that fails at *collection*, not test, time without the private `emergentintegrations` package — same exclusion `pytest.ini`'s own `addopts` documents and reports/10 already established.)

**Exact result:**
```
50 failed, 184 passed, 12 skipped, 63 deselected, 2 warnings, 89 errors in 668.49s (0:11:08)
```
(335 collected+deselected items match the "335-test integration suite" the mission's own backlog names; 63 are `unit`-marked items auto-deselected by `-m integration`.)

## 4. Failure/error classification (per-item root cause, verified against server logs and code — not guessed)

| Root cause | Classification | Approx. items affected | Evidence |
|---|---|---|---|
| `FREK_EMAIL_SALT` required but **entirely absent from `backend/.env.example`** | **CONFIGURATION** (documentation gap — a real bug in the repo, not just this session's harness) | ~40+ (every route through `frek_v1/utils.py:hash_email()` — badges/create, jetons flows, identity/emit, etc.) | Server log: `RuntimeError: Variable d'environnement manquante: FREK_EMAIL_SALT`, 33+ occurrences. Cross-checked: `grep -rn "get_env(" backend --include="*.py"` finds only 2 required vars (`FREK_EMAIL_SALT`, `SECRET_KEY`); `SECRET_KEY` **was** documented, `FREK_EMAIL_SALT` was not. |
| `OTSAnchor`'s calendar-submission loop has no circuit breaker — every identity emission (background task) and every `/anchor/sweep` call retries all 5 `DEFAULT_CALENDARS` unconditionally, even when all 5 are unreachable | **APPLICATION BUG** | Majority of the 89 errors + a chunk of the 50 failures, spread across unrelated test files (`test_did_vc.py`, `test_eudi.py`, `test_governance_phase1.py`, `test_passport.py`, `test_staff_scan.py`, etc. — none of these exercise the notary/anchor code themselves) | `mongomock_server.log`: hundreds of `OTS submit failed on https://...: Tunnel connection failed: 403 Forbidden` lines fired continuously for the run's duration; server confirmed running the whole time (no crash) — the exhaustion is of the shared `asyncio.to_thread` thread pool (used both by `submit_block`'s blocking calendar calls and by every synchronous FastAPI route handler via Starlette's `run_in_threadpool`), not a server crash. Manifests as `requests.exceptions.JSONDecodeError`/`ConnectionError`/`TimeoutError` on **unrelated concurrent requests**. |
| Several test files' local `mongo` fixture connects **directly** to `pymongo.MongoClient(host=["localhost:27017"])`, bypassing the API entirely | **ENVIRONMENT** (expected, disclosed limitation of the `mongomock` substitute — no real TCP listener exists) | `test_security_hardening.py`, `test_core_ingest.py`, `test_fingerprint.py`, `test_staff_bcrypt.py` (all define a `mongo` fixture at module scope) | `grep -n "^def mongo" tests/*.py`; `mongomock_motor` is in-process only, nothing listens on port 27017 in this setup. |
| `backend/frek/nodes/node01_extraction.py` lazily imports `librosa` (audio feature extraction for `/api/frek/certify`'s audio path), never declared in `backend/requirements.txt` | **ENVIRONMENT / DEPENDENCY GAP** | `test_frek_api.py::test_certify_audio` | Server log: `ModuleNotFoundError: No module named 'librosa'`. Not added this phase: `backend/frek/` is Contradiction C4 (`reports/FREKCORE_CONTRADICTIONS.md`) — unversioned legacy surface with a pending founder decision on its fate; adding a heavy native-dependency library (librosa pulls in `numba`, `soundfile`, `audioread`) to a module whose future is undecided is new scope, not a proven-defect fix. |
| `tests/test_identity_engine.py`'s two `EXPECTED_RP_ID` assertions hardcode a specific external preview domain (`culture-chain.preview.emergentagent.com`) instead of deriving the expected value from the test's own configured `REACT_APP_BACKEND_URL` | **TEST DEBT** | `TestRegisterBegin::test_register_begin_returns_valid_options`, `TestAuthenticateBegin::test_authenticate_begin_returns_options` | `assert 'localhost' == 'culture-chai...gentagent.com'` — the application correctly derived `rp.id`/`rpId` from the *actual* configured backend URL (`identity_engine/service.py:get_rp_id()`); the test's expected value is environment-specific, not portable. Not edited this phase — no test file may be blind-rewritten per the mission's rules, and this session did not have enough context on why that specific domain was chosen originally to safely generalize the assertion. Flagged in `reports/FREKCORE_COMPLETION_BACKLOG.md`. |
| `tests/test_offline_verifier.py`'s `VERIFIER_PATH` was hardcoded to `/app/verifier/python/verify_passport.py` (a specific deployment container's mount path); the file genuinely exists in the repo, just at a different absolute path in this checkout | **TEST DEBT — FIXED this phase** | `TestVerifierAvailability::test_python_script_exists` | Verified `verifier/python/verify_passport.py` exists at the repo root before touching anything. Fix: resolve relative to the test file's own location when the deployment path isn't present, preserving the deployment path first (no behavior change there). Re-run in isolation against the live mongomock server: `1 passed`. |
| Assorted real assertion mismatches not yet individually root-caused (aggregation-pipeline coverage gaps in `mongomock` vs. real MongoDB per the harness script's own disclaimer; a few genuinely unreviewed `AssertionError`s) | **ENVIRONMENT (unconfirmed) / NOT YET CLASSIFIED** | Remainder | Not exhaustively triaged item-by-item this phase — see §6. |

## 5. Fixes applied this phase (Priority 3 — proven defects only)

1. **`backend/.env.example`**: added the missing `FREK_EMAIL_SALT` line with a comment explaining what breaks without it. One-line documentation fix, zero application-code risk.
2. **`backend/notary/anchor.py`**: added `_CalendarCircuitBreaker` (per-calendar consecutive-failure counter with a cooldown), wired into both `submit_block()`'s and `upgrade_block()`'s calendar loops. Defaults: 3 consecutive failures opens the breaker, 5-minute cooldown before retrying — both overridable via `OTS_BREAKER_THRESHOLD`/`OTS_BREAKER_COOLDOWN_SECONDS` env vars, so a real deployment with genuinely flaky (not permanently blocked) calendars can tune it. No behavior change when calendars are reachable — the breaker only ever *skips* calls after a run of failures, never adds latency to a working calendar. 7 new unit tests (`backend/tests/test_notary_anchor_breaker.py`), pure state-machine tests, no network/asyncio/DB — all pass. **Note on `upgrade_block()`'s wiring**: `_upgrade_via_calendar()` internally catches and logs (not re-raises) per-attestation exceptions inside `_walk_and_upgrade()`, so the breaker's `record_failure` on that path will rarely trigger from a real calendar outage — documented here rather than overclaimed; `submit_block()`'s wiring (the path actually exercised by this run) is the one with verified effect.
3. **`backend/tests/test_offline_verifier.py`**: `VERIFIER_PATH` now resolves portably (see table above). Pure test-infrastructure fix, no application code touched, verified passing in isolation.

## 6. Run 3 — same suite, same server, all three fixes applied

<!-- Filled in once the background re-run (bw782kv0d / /tmp/integration_run3.log) completes. -->

**Status at time of writing: in progress.** Command identical to Run 2's, plus `FREK_EMAIL_SALT` and the four `FREK_STAFF_*_PIN` vars now exported (the latter were already documented in `.env.example` — their absence in Run 2 was this session's own harness gap, not a repo bug, so setting them is not counted as an application fix).

Final counts and a fixed-vs-still-failing delta will be appended below once the run finishes; do not treat Run 2's numbers as the final Phase 3 baseline.
