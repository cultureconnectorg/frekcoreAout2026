# 09 — Phase 2 Baseline

**Purpose**: the state of the repository *before* any Phase 2 change, captured per Step 0's instructions, so every later claim in this phase can be checked against a fixed starting point.

## Git state

```
$ git status --short -b
## claude/frekcore-v1-production-b9h2q0...origin/claude/frekcore-v1-production-b9h2q0
(clean — nothing to commit)

$ git rev-parse HEAD
a9fa42c54a447aa3c10aa5389f54f0da9f908631

$ git log --oneline -1
a9fa42c Add FREK Registry (Bloc 1), Event Registry catalog, CVLN interface docs, and forensic audit reports
```

Branch: `claude/frekcore-v1-production-b9h2q0`. Working tree clean. This is exactly the commit Phase 1 reported pushing.

## Reports read before any Phase 2 edit (per Step 0)

- `reports/01_FORENSIC_AUDIT.md` — confirmed: monolithic FastAPI app, 30 feature packages, no DDD split, no CI, no request-ID middleware.
- `reports/02_GAP_ANALYSIS.md` — confirmed: per-block EXISTS/PARTIAL/MISSING table; priority ranking already named CI/CD (#1), Permission Engine (#2), Event Bus producers (#3), SDKs (#4), Observability (#5) — this phase follows that ranking for Priorities 1–6, then treats 7–15 at lighter depth per the Phase 2 brief's own ordering.
- `reports/03_ARCHITECTURE_MAP.md` — confirmed: module-by-module map, cryptographic architecture diagram, `backend/registry/` structure as delivered in Phase 1.
- `reports/08_NEXT_INTEGRATION.md` — confirmed: exact diff delivered in Phase 1 (+4 lines in `backend/server.py`), and the 6-item recommended order this Phase 2 brief mostly follows.

**No claim from these reports was taken on faith without re-verification in this session** — every fact re-used below was re-checked against the live filesystem/tests before being relied upon (see `10_TEST_INFRASTRUCTURE.md`).

## Registry (Phase 1 deliverable) — re-verified, not assumed

```
$ ls backend/registry/
__init__.py  events/  routes.py  schemas/  service.py

$ ls backend/registry/schemas/v1/
_base.schema.json  frek.album.schema.json  frek.artist.schema.json
frek.certificate.schema.json  frek.event.schema.json  frek.organization.schema.json
frek.track.schema.json  frek.wallet.schema.json  frek.work.schema.json
```

Test re-run (before any Phase 2 change):

```
$ cd backend && python3 -m pytest tests/test_registry.py -v
...
10 passed in 0.64s
```

All 8 namespaces + base schema present and passing, exactly as Phase 1 reported. Confirmed by execution, not by reading the prior report's claim.

## Environment available in this session (re-discovered fresh, not assumed from Phase 1)

Phase 1's `06_TEST_REPORT.md` reported the sandbox could not run `pymongo`/`cryptography` imports (a `pyo3_runtime.PanicException` from a broken `_cffi_backend`). Re-checked at the start of this phase:

```
$ python3 -c "from pymongo import MongoClient; print('imported OK')"
imported OK
```

**This now succeeds.** The fix from Phase 1 (`pip install --force-reinstall --no-cache-dir cffi cryptography`) persisted in this container across sessions (same underlying sandbox). This is recorded here explicitly rather than silently relied upon — see `10_TEST_INFRASTRUCTURE.md` §1 for the full before/after evidence and why the *code* (not just the environment) was still worth hardening against this class of failure.

- `mongod` / `mongosh`: **not present** (`which mongod` → nothing). No real MongoDB is reachable in this sandbox.
- `docker` CLI: present (`/usr/bin/docker`) but **no daemon** (`docker build` → `failed to connect to the docker API at unix:///var/run/docker.sock ... no such file or directory`). Docker builds could not be executed end-to-end in this sandbox; see `12_PHASE2_IMPLEMENTATION.md` for how this was handled (the underlying `pip install` failure was verified independently of the daemon).
- `pip` install access: available (verified throughout this session).

## Tests executable vs. not executable in this sandbox (baseline, before Phase 2 changes)

| Tier | Executable here? | Evidence |
|---|---|---|
| `backend/tests/test_registry.py` (Phase 1, 10 tests) | **Yes** | passes standalone, no live server/Mongo needed |
| The other 27 test files (`test_fk.py` through `test_universe_mission.py`) | **Partially** — some collect and pass without a live server (discovered *during* this phase, see `10_TEST_INFRASTRUCTURE.md`), most require `http://localhost:8001` + MongoDB and were not run end-to-end | `requests.exceptions.ConnectionError` reproduced for the live-server-dependent ones |
| `scripts/export_openapi.py` | Not run | imports `server.py`, which (as discovered this phase) transitively requires the private `emergentintegrations` package — see `10_TEST_INFRASTRUCTURE.md` |

## Known limitations carried into this phase

1. No real MongoDB — any code touching `db.*` collections can be reviewed and unit-tested around its pure logic, but not integration-tested end-to-end in this sandbox.
2. No Docker daemon — Docker-build verification in this phase is necessarily partial (see `12_PHASE2_IMPLEMENTATION.md`).
3. `backend/requirements.txt` cannot be installed in a single `pip install -r` in *any* clean environment (not sandbox-specific) — discovered and reproduced during Priority 1/2 work in this phase, see `10_TEST_INFRASTRUCTURE.md` for the full evidence. This shapes both the CI design and the Docker-build finding.

This baseline is the reference point for every "before/after" claim in `12_PHASE2_IMPLEMENTATION.md`.
