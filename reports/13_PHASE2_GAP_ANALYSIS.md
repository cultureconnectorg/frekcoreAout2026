# 13 — Phase 2 Gap Analysis

Updates `reports/02_GAP_ANALYSIS.md` where Phase 2 changed the picture. Rows not listed here are unchanged from Phase 1.

## Updated rows

| # | Item | Phase 1 status | Phase 2 status | Evidence |
|---|---|---|---|---|
| 6 | Permission Engine | PARTIAL (flat strings) | **PARTIAL → model DELIVERED, not enforced** | `backend/permissions/` — real, tested, typed model; zero wiring into any route. Still true today: the only thing actually *enforcing* access on any live endpoint is `backend/frek_v1/auth.py`'s flat permission strings. |
| 4 | Audit Trail | not explicitly tracked | **DELIVERED (module only)** | `backend/audit_trail/` — append-only by construction, not yet a sink for any real operation |
| 7 | Event Bus | MISSING → catalog delivered | **Catalog + real abstraction + 1 real producer DELIVERED** | `backend/eventbus/`; `identity.created` flipped to `implemented: true` with evidence |
| 9 | SDK | MISSING | **DELIVERED (Registry API only, 2 languages)** | `sdk/python/`, `sdk/typescript/` |
| 11 | Observability | PARTIAL | **PARTIAL → primitives DELIVERED, not wired** | `backend/observability/` |
| 12 | CI/CD | MISSING | **DELIVERED** | `.github/workflows/ci.yml`, 7 jobs |

## New rows this phase

| Item | Status | Evidence |
|---|---|---|
| Test infrastructure (`unit`/`integration` split, canonical command) | **DELIVERED** | `reports/10_TEST_INFRASTRUCTURE.md` — `pytest` now exits 0 in a clean checkout |
| Proof Engine explicit states (Bloc 4 readiness) | **DELIVERED** | `backend/proof_engine/` |
| Storage abstraction interface | **DELIVERED (interface + local impl only)** | `backend/storage/` |
| Contract tests (envelope vs. schema, SDK vs. server) | **PARTIAL** | See `12_PHASE2_IMPLEMENTATION.md` Priority 14 — real but incomplete (no OpenAPI contract check, no cross-language automation) |

## New gaps discovered this phase (not visible from Phase 1's evidence)

| Finding | Severity | Evidence | Status |
|---|---|---|---|
| `backend/requirements.txt` cannot be installed with a single `pip install -r` on any clean environment — `emergentintegrations==0.1.0` is not on PyPI | **High** — blocks CI dependency-install, Docker build, and a fresh dev-machine setup | `reports/10_TEST_INFRASTRUCTURE.md` §2d, reproduced twice | Documented, not fixed (needs a human decision: private index secret, vendor, or lazy-import) |
| `backend/requirements.txt` has an internal version conflict: `cryptography==46.0.4` vs. `webauthn==3.0.0`'s `cryptography>=49.0.0` requirement | **High** — same consequence as above, independent cause | `reports/10_TEST_INFRASTRUCTURE.md` §2d, pip resolver output quoted verbatim | Documented, not fixed |
| `ecosystem/registry.json` overclaimed "Ed25519 signed blocks" for `frek_chain`; no such signature exists in `backend/notary/*.py` | **Medium** — a false capability claim in a file other CVLN systems may read to decide what to trust | `reports/12_PHASE2_IMPLEMENTATION.md` Priority 12; `grep -rn "sign\|Ed25519" backend/notary/*.py` → no matches | **Fixed this phase** (`ecosystem/registry.json` corrected with an inline note) |
| `backend/tests/test_security_hardening.py` (and, less severely, 6 other test files) hardcode `/app/...`, breaking portability to any checkout other than the original Emergent container path | **Medium** — blocks CI from ever running these files | `reports/10_TEST_INFRASTRUCTURE.md` §2b | **Fixed** for the one file that crashed collection; the other 6 were left alone (guarded, non-blocking — see rationale in the same section) |
| No coverage tooling existed before this phase | **Low** | `reports/06_TEST_REPORT.md` (Phase 1) | **Fixed** — `pytest-cov` now in `requirements-ci.txt`, wired into CI with `--cov-fail-under=90`, currently 99.03% on the 7 modules that have it |

## Priorities not advanced this phase (explicitly out of scope, not silently dropped)

- Wiring `backend/permissions/` into `frek_v1/auth.py` or any route.
- Wiring `backend/audit_trail/` into any route or database.
- Wiring `backend/observability/`'s middleware/metrics into `server.py`.
- Producers for `identity.updated`, `identity.revoked`, `object.created`, `proof.generated` (real), `certificate.issued`.
- Fixing `backend/requirements.txt`'s two install blockers.
- Bumping any of the CVE-flagged pinned dependencies (`reports/11_SECURITY_PHASE2.md` §3).
- A DDD reorganization of the 30-module backend (never in scope for either phase — explicitly a non-goal in this phase's brief).
