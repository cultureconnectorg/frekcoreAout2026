# 10 — Test Infrastructure — Root Cause Analysis & Canonical Command

## 1. The canonical command

```
cd backend
pip install -r requirements-ci.txt   # curated, resolvable subset — see that file's header
pytest
```

**Result (reproduced 2026-08-30):**

```
$ python3 -m pytest -v
collecting ... collected 356 items / 335 deselected / 21 selected
tests/test_fk.py::test_create_fk_minimal PASSED
tests/test_fk.py::test_create_fk_with_media PASSED
tests/test_fk.py::test_survival_offline_verification PASSED
tests/test_fk.py::test_tampering_detected_manifest PASSED
tests/test_fk.py::test_tampering_detected_media PASSED
tests/test_fk.py::test_canonical_json_deterministic PASSED
tests/test_fk.py::test_frek_id_prefix PASSED
tests/test_production_hardening_static.py::test_server_requires_explicit_credentialed_cors_allowlist_and_nonblank_seed_secrets PASSED
tests/test_production_hardening_static.py::test_scanner_idempotency_keys_use_web_crypto_not_math_random PASSED
tests/test_production_hardening_static.py::test_staff_seed_requires_explicit_pin_outside_opt_in_development_mode PASSED
tests/test_production_hardening_static.py::test_unique_index_startup_never_drops_existing_indexes_without_preflight PASSED
tests/test_registry.py::test_versions_lists_v1 PASSED
tests/test_registry.py::test_namespaces_cover_bloc1_catalog PASSED
tests/test_registry.py::test_get_schema_for_each_namespace_is_valid_json_schema PASSED
tests/test_registry.py::test_unknown_namespace_is_404 PASSED
tests/test_registry.py::test_validate_valid_artist_payload PASSED
tests/test_registry.py::test_validate_rejects_missing_required_field PASSED
tests/test_registry.py::test_validate_rejects_bad_frek_id_pattern PASSED
tests/test_registry.py::test_validate_unknown_namespace_is_404 PASSED
tests/test_registry.py::test_event_registry_catalog_shape PASSED
tests/test_registry.py::test_service_all_namespace_schemas_are_valid_draft202012 PASSED
21 passed, 335 deselected, 2 warnings in 9.85s
$ echo $?
0
```

`pytest -m integration` runs the other 335 tests (requires a live backend at `TEST_BACKEND_URL` [default `http://localhost:8001`] and a reachable `MONGO_URL`/`DB_NAME` — not available in this sandbox, not run here; see §3).

## 2. What was actually wrong, and where each problem lives (code vs. dependencies vs. sandbox)

### 2a. `_purge_rate_limits()` imported `pymongo` unconditionally (code bug — fixed)

**Before** (`backend/tests/conftest.py`, prior to this phase):
```python
def _purge_rate_limits():
    try:
        from pymongo import MongoClient
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        if not mongo_url or not db_name:
            return
        ...
```
The `pymongo` import ran *before* the env-var check that would otherwise make the whole function a no-op. In this sandbox at the start of Phase 1, that import chain (`pymongo` → `cryptography`/`cffi`) crashed with `pyo3_runtime.PanicException: Python API call failed` / `ModuleNotFoundError: No module named '_cffi_backend'` — a broken native extension in the sandbox's system Python, **not** a FREKCORE code defect by itself. But the *code* made that crash unavoidable even when MongoDB was never going to be used (no `MONGO_URL` configured), because the import ran unconditionally in an `autouse=True`, `scope="session"` fixture — meaning one broken/absent MongoDB client library could abort collection of the *entire* test session, including tests that need no database at all.

**Fixed this phase** (`backend/tests/conftest.py`): the env-var check now runs first; `from pymongo import MongoClient` only executes when `MONGO_URL`/`DB_NAME` are actually set. Verified: `pytest` (no MongoDB configured in this sandbox) no longer even attempts the import, and does not depend on the sandbox's `cffi` fix persisting.

### 2b. `test_security_hardening.py` hardcoded `/app/backend/.env` and `/app/frontend/.env` (code bug — fixed)

```python
# before
with open("/app/backend/.env") as f:
    ...
```
`/app` is the Docker container's `WORKDIR` (`Dockerfile:3`: `WORKDIR /app/backend`) — correct *inside that container*, but not portable to any other checkout location (a developer's machine, this sandbox, or a GitHub Actions runner checking out to `$GITHUB_WORKSPACE`). This crashed **collection** (not just the test) with `FileNotFoundError`, which is why it appeared in the "2 errors during collection" bucket even before any test ran.

**Fixed this phase**: paths now resolve via `Path(__file__).resolve().parents[2]` (repo root, wherever it is checked out) and degrade to `None`/a `localhost` default instead of crashing when the file is absent (e.g. a CI runner with no `.env` provisioned) — the tests that actually need those values still fail explicitly and individually at call time, never silently.

Seven other files also hardcode `/app/...` paths (`test_notary.py`, `test_core_ingest.py`, `test_universe_mission.py`, `test_governance_phase1.py`, `test_governance_phase2.py`, `test_offline_verifier.py`) plus 4 **production** source files (`backend/ecosystem/routes.py`, `backend/health/routes.py`, `backend/passport/keys.py`, `backend/services/stripe_pay.py`). Confirmed by direct collection (`pytest --collect-only`) that **none of the other 6 test files crash at collection time** — their `/app/` references are either guarded with a fallback (same pattern this fix now uses) or only evaluated inside a test function body at run time, so they were left untouched (not a collection blocker, and touching working integration tests beyond the one proven blocker was out of this phase's minimal-diff scope). The 4 production files were **not** touched: `Dockerfile:3` sets `WORKDIR /app/backend`, so `/app/...` is the *correct* path in the actual deployed container — changing it would be an unjustified, unrequested risk to production behavior for zero benefit (see `12_PHASE2_IMPLEMENTATION.md` for the explicit decision not to touch these).

### 2c. Most of the 28 pre-existing test files require a live backend + MongoDB (architecture, not a bug)

```
$ grep -l "^import requests\|BASE_URL" tests/*.py | wc -l
24
$ grep -l "TestClient" tests/*.py
test_ecosystem.py
test_registry.py   (Phase 1, new)
```
24 of 28 pre-existing files make real HTTP calls (`requests.get/post(BASE_URL + ...)`) against `TEST_BACKEND_URL` (default `http://localhost:8001`, `conftest.py`). This is a deliberate integration-test design (per `memory/INVENTORY.md`'s iteration history — these tests exercised a running `uvicorn` + MongoDB stack in the original Emergent deployment), not a defect. Reproduced without a live server:
```
$ python3 -m pytest tests/ --ignore=tests/test_ecosystem.py --ignore=tests/test_security_hardening.py -q
162 failed, 33 passed, 145 errors in 63.41s
```
(`33 passed` = the same 21 unit-safe tests as today, plus 12 that happened to pass despite `ConnectionError` handling in a few defensive spots — not re-verified individually since the point of this phase's fix is to *not* run these by default, see §1.) Every failure/error in that run was `requests.exceptions.ConnectionError` — i.e. connection refused, not an assertion failure. **This is the expected behavior of an integration suite with no integration target**, not a broken test suite.

### 2d. `backend/requirements.txt` cannot be installed with a single `pip install -r` on *any* clean environment (dependency-manifest bug — not fixed, documented)

Two independent, reproduced blockers:

1. **Private package, not on PyPI**:
   ```
   $ pip install emergentintegrations==0.1.0
   ERROR: Could not find a version that satisfies the requirement emergentintegrations==0.1.0 (from versions: none)
   ERROR: No matching distribution found for emergentintegrations==0.1.0
   ```
   `requirements.txt:26`. It is a **real** dependency — `backend/services/webhook.py:8`: `from emergentintegrations.payments.stripe.checkout import StripeCheckout`, used by the Stripe-checkout webhook flow, imported transitively by `server.py:25`. Not dead code; cannot be deleted from the manifest without deciding what happens to that feature.

2. **Internal version conflict**, reproduced with pip's real resolver (not a sandbox artifact):
   ```
   $ pip install -r <(grep -v '^emergentintegrations' requirements.txt)
   ERROR: Cannot install -r requirements.txt (line 143: pytest-asyncio) and cryptography==46.0.4
   because these package versions have conflicting dependencies.
   The conflict is caused by:
       The user requested cryptography==46.0.4
       google-auth 2.49.0.dev0 depends on cryptography>=38.0.3
       webauthn 3.0.0 depends on cryptography>=49.0.0
   ```
   `requirements.txt` pins `cryptography==46.0.4` (line 20) **and** `webauthn==3.0.0` (line 144), but `webauthn==3.0.0`'s own published metadata requires `cryptography>=49.0.0` — a strictly higher version than the pin. This is an internal inconsistency in the committed file, independently confirmed by pip's dependency resolver twice (once via `pip-audit`, once via a direct `pip install -r`).

**Why this was not "fixed" in this phase**: (1) requires either removing a real, used feature (Stripe checkout) or making its import lazy/optional — a behavior change to production code that needs an explicit decision, not a silent CI-driven patch; (2) requires bumping a security-sensitive cryptography pin, which needs its own review (what else in the 30-module backend implicitly assumes `cryptography` 41–46.x behavior). Both are named as P0 remediation items in `07_DEPLOYMENT_REPORT.md` and `12_PHASE2_IMPLEMENTATION.md`, not silently patched around.

**Practical consequence**: today, `backend/requirements.txt` most likely only ever installs successfully when packages are added incrementally in an order/history that never triggers a full-graph resolve against the conflicting pins together (which is exactly how this sandbox's environment reached a working state — see `09_PHASE2_BASELINE.md`) — or inside the original Emergent platform, which presumably has its own private index resolving `emergentintegrations` and may have last resolved the crypto pins with an older webauthn version. A fresh `pip install -r backend/requirements.txt` on a standard machine (a new contributor's laptop, a GitHub Actions runner, a from-scratch Docker build) reproduces the errors above today.

## 3. Why 335 tests are not run in CI (isolated, not hidden)

Per the mission's explicit instruction ("les isoler explicitement; mais ne jamais falsifier leur résultat"), these are **not** run and **not** reported as passing. `backend/pytest.ini` deselects them by default (`addopts = -m "not integration"`) with an inline comment; `backend/tests/conftest.py`'s `pytest_collection_modifyitems` auto-marks every test `integration` unless its module opts into `unit` via `pytestmark = pytest.mark.unit`. Running them for real requires:
- A reachable MongoDB (`MONGO_URL`, `DB_NAME`).
- A live `uvicorn server:app` process on `TEST_BACKEND_URL` (default `http://localhost:8001`), itself blocked today by §2d (the app cannot even be imported without `emergentintegrations`).

Bringing up that stack (e.g. via `docker-compose.yml`, which already defines a `mongo` service) was not attempted in this sandbox (no Docker daemon — see `09_PHASE2_BASELINE.md`). This is recorded as a gap, not glossed over: **the 335 integration tests' current pass/fail state is unknown as of this report** — the last positive evidence for them is the historical `test_reports/pytest/*.xml` / `test_reports/iteration_*.json` files referenced in Phase 1's `06_TEST_REPORT.md`, which this phase does not re-verify or re-assert.

## 4. `unit` vs `integration` — what got the `unit` marker and why

| File | Marked `unit`? | Evidence |
|---|---|---|
| `tests/test_registry.py` | Yes (Phase 1 module, marker added this phase) | No `TestClient` touches MongoDB; isolated `FastAPI()` app |
| `tests/test_fk.py` | Yes (added this phase) | Docstring: "un .fk cree doit rester verifiable HORS LIGNE ... sans DB ni serveur"; imports only `fk.packager`/`fk.validator`, no `server`, no `requests`; 7/7 pass standalone |
| `tests/test_production_hardening_static.py` | Yes (added this phase) | Docstring: "deliberately require neither MongoDB nor an external deployment"; reads `server.py` as **text**, never imports it; 4/4 pass standalone |
| All other 25 files | No (auto-marked `integration` by `conftest.py`) | Use `requests` against `BASE_URL`/`TestClient(app)` importing the full `server.py` |

No file was marked `unit` speculatively — each was proven first by running it standalone with `--continue-on-collection-errors` and confirming 100% pass with no network calls.

## 5. Reproduction commands (for the next session / a reviewer)

```
cd backend
pip install -r requirements-ci.txt
pytest                                    # canonical: 21 passed, 335 deselected, exit 0
pytest --cov=registry --cov-report=term-missing --cov-fail-under=90   # 96.36% (see 12_PHASE2_IMPLEMENTATION.md)
pytest -m integration                     # will fail/error without a live backend + MongoDB — expected, not a regression
flake8 --max-line-length=120 registry/ tests/test_registry.py   # clean
black --check registry/ tests/test_registry.py                 # clean
mypy --ignore-missing-imports registry/                          # clean
```
