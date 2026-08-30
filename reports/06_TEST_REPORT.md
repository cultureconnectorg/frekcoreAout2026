# 06 — Test Report — FREKCORE

## 1. Existing test suite (as found)

- 28 test files under `backend/tests/` (`ls backend/tests | wc -l` → 28, plus `conftest.py`).
- Framework: `pytest==9.0.2` + `pytest-asyncio==1.4.0`, `asyncio_mode = auto` (`backend/pytest.ini:1-2`).
- **Architecture**: integration tests against a **live backend process**. `backend/tests/conftest.py:6-9,21` sets `TEST_BASE_URL = os.environ.get("TEST_BACKEND_URL") or "http://localhost:8001"` and points `REACT_APP_BACKEND_URL` at it — tests make real HTTP calls to a running `uvicorn` instance, not in-process `TestClient` calls. An autouse session fixture also connects directly to MongoDB to purge `rate_limits` between tests (`conftest.py:25-43`).
- **This session's environment does not have `mongod` or a running backend supervisor** (`which mongod` → not found; no `.env` with a reachable `MONGO_URL`). Attempting to run the suite as-is (`python3 -m pytest tests/test_registry.py`) failed at **collection time**, before any test logic ran, with:
  ```
  pyo3_runtime.PanicException: Python API call failed
  ModuleNotFoundError: No module named '_cffi_backend'
  ```
  raised from `cryptography`/`pymongo`'s SSL context import, triggered by `conftest.py`'s autouse fixture. This is a **pre-existing sandbox environment issue** (a broken system `cryptography`/`cffi` install unrelated to this session's changes), not a regression: the same failure occurs on the untouched `backend/tests/` suite with no FREKCORE code involved.
- **Historical evidence of the suite passing**: `test_reports/pytest/*.xml` (JUnit XML, 12 files) and `test_reports/iteration_*.json` (28 files, iterations 1–28) record prior green runs, most recently referenced in `memory/INVENTORY.md:220-223` ("iteration_28 = 100%"). This session did not re-verify those results (no live environment available) and does not claim they still hold — it reports what evidence exists.
- **No coverage tool is configured** (`grep -rn "coverage" backend/pytest.ini backend/requirements.txt` → no matches, no `pytest-cov` dependency). The Master Prompt's "90% coverage" target (Phase 11 / Bloc 15 quality bar) cannot currently be measured, let alone met, without adding that tooling first.

## 2. New tests added this session — `backend/tests/test_registry.py`

Because `backend/registry/` has **no MongoDB dependency**, it was tested directly with `fastapi.testclient.TestClient` against an isolated `FastAPI()` app mounting only `registry_router` — sidestepping the live-server requirement of the rest of the suite while still exercising real HTTP request/response cycles through FastAPI's routing and Pydantic validation.

To avoid the same `conftest.py`-triggered `cffi` crash (an environment issue, not a code issue — see §1), the test file was additionally executed standalone (copied outside `backend/tests/`, `PYTHONPATH=backend`) to prove the module itself is correct independent of the broken sandbox dependency:

```
$ PYTHONPATH=backend python3 -m pytest test_registry_standalone.py -v
test_registry_standalone.py::test_versions_lists_v1 PASSED                     [ 10%]
test_registry_standalone.py::test_namespaces_cover_bloc1_catalog PASSED        [ 20%]
test_registry_standalone.py::test_get_schema_for_each_namespace_is_valid_json_schema PASSED [ 30%]
test_registry_standalone.py::test_unknown_namespace_is_404 PASSED              [ 40%]
test_registry_standalone.py::test_validate_valid_artist_payload PASSED         [ 50%]
test_registry_standalone.py::test_validate_rejects_missing_required_field PASSED [ 60%]
test_registry_standalone.py::test_validate_rejects_bad_frek_id_pattern PASSED  [ 70%]
test_registry_standalone.py::test_validate_unknown_namespace_is_404 PASSED     [ 80%]
test_registry_standalone.py::test_event_registry_catalog_shape PASSED         [ 90%]
test_registry_standalone.py::test_service_all_namespace_schemas_are_valid_draft202012 PASSED [100%]

10 passed in 0.54s
```

Coverage of these 10 tests:

| Test | Verifies |
|---|---|
| `test_versions_lists_v1` | `GET /registry/versions` lists `v1` |
| `test_namespaces_cover_bloc1_catalog` | The 8 namespaces named in the Master Prompt Bloc 1 table are exactly what the API returns |
| `test_get_schema_for_each_namespace_is_valid_json_schema` | Every namespace schema resolves its `_base.schema.json` `$ref` correctly (inlined, no dangling ref) |
| `test_unknown_namespace_is_404` | Unknown namespace → HTTP 404, not a 500 |
| `test_validate_valid_artist_payload` | A well-formed `frek.artist` payload validates as `valid: true` |
| `test_validate_rejects_missing_required_field` | Missing `display_name` is caught with a field-pathed error message |
| `test_validate_rejects_bad_frek_id_pattern` | The shared `frek_id` regex constraint from `_base.schema.json` is actually enforced through the `allOf` composition |
| `test_validate_unknown_namespace_is_404` | `POST /validate` on an unknown namespace → 404, not a silent pass |
| `test_event_registry_catalog_shape` | `GET /registry/events` returns ≥8 catalog entries, each with `event_type`/`implemented`/`status` |
| `test_service_all_namespace_schemas_are_valid_draft202012` | Every schema, after base-ref inlining, is itself a syntactically valid Draft 2020-12 JSON Schema (via `Draft202012Validator.check_schema`) |

This is a genuine, reproducible pass — not asserted without the transcript above.

## 3. What was **not** verified

- `backend/server.py` was **not** booted end-to-end in this session. Reasons: it imports ~30 feature modules at module load time (`server.py:14-76`), transitively requiring `motor`, `webauthn`, `boto3`, `stripe`, `opentimestamps`, `bit`, `coincurve`, `h3`, `openlocationcode`, and others. Installing the full dependency set hit unrelated sandbox packaging failures (`openlocationcode` wheel build failure against a broken `setuptools`/`distutils` install; see raw pip output captured during this session). `python3 -c "ast.parse(open('server.py').read())"` **was** run and confirms the file — including this session's 3-line addition wiring `registry_router` — is syntactically valid Python.
- The pre-existing 28-file integration suite was not re-run (see §1) — no claim is made about its current pass/fail state.
- `python scripts/export_openapi.py --check` was not run for the same reason (it imports `server.py`, see `scripts/export_openapi.py:22`).

## 4. Recommendation

Before the next phase, provision a sandbox (or CI runner, see `07_DEPLOYMENT_REPORT.md`) with: a working `mongod` (or `mongomock`), the full `backend/requirements.txt` installable without system-package conflicts, and `pytest-cov` added to measure real coverage against the Master Prompt's 90% target.
