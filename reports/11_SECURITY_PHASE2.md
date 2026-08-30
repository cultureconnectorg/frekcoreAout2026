# 11 — Security Phase 2

Builds on `reports/05_SECURITY_REPORT.md` (Phase 1). This report covers what changed and what was newly audited in Phase 2; it does not repeat Phase 1's findings verbatim.

## 1. Secrets

- `backend/.env.example` re-checked: every value is a placeholder (`replace-with-a-...`) or empty (`FREK_STAFF_*_PIN=`). No real secret present. Not modified this phase — already compliant with the mission's "placeholders only" rule.
- `grep -rniE "AKIA[0-9A-Z]{16}|sk_live_|sk_test_[a-zA-Z0-9]{10}|-----BEGIN (RSA |EC )?PRIVATE KEY-----"` across the repository (excluding `backups/`, which is a pre-existing encrypted `.tar.gz.gpg` archive, not plaintext) → **no matches**.
- No new secret, credential, or API key was introduced by any Phase 2 file. `backend/requirements-ci.txt` and `.github/workflows/ci.yml` reference no repository secret (the two `continue-on-error` jobs are informational, not gated behind credentials).

## 2. New attack surface added this phase — reviewed

None of Phase 2's new packages (`backend/registry/` *(Phase 1)*, `backend/eventbus/`, `backend/permissions/`, `backend/audit_trail/`, `backend/proof_engine/`, `backend/storage/`, `backend/observability/`) expose a new HTTP route. The only route-level change is the `identity_engine/routes.py` addition (see `12_PHASE2_IMPLEMENTATION.md`), reviewed below:

- **`identity_engine/routes.py`'s event-publish call** (lines ~36-46, ~124-130): wrapped in `try/except Exception`, cannot raise past the route handler, does not touch any new database collection, does not accept additional user input beyond what `/identity/init` already accepted. No new injection surface.
- **`backend/storage/local.py`**: `_resolve()` explicitly rejects path traversal (`candidate` must be inside `self._root`) — tested in `test_path_traversal_is_rejected` (`backend/tests/test_storage.py`). Not wired into any route; the check exists because the module is meant to eventually receive caller-supplied paths.
- **`backend/observability/request_id.py`**: echoes a caller-supplied `X-Request-ID`/`X-Correlation-ID` header back into the response and into log-adjacent contextvars. No injection risk (values are never interpolated into a shell command, SQL, or HTML — they are opaque strings used only as log/header values), but a caller can inject an arbitrary string as their own request ID. This is standard practice (matches common frameworks) and is documented, not silently assumed safe.
- **`sdk/python`, `sdk/typescript`**: client-side code. No server-side surface.

## 3. Dependency vulnerability scan (real findings, `pip-audit`)

Run against `backend/requirements-ci.txt` (the resolvable subset — see `reports/10_TEST_INFRASTRUCTURE.md` for why the full `backend/requirements.txt` cannot be scanned this way):

```
$ pip-audit -r backend/requirements-ci.txt
```

Selected real, reproduced findings (full list is long; these are the ones with a fixed version available and a pinned version in this repo):

| Package | Installed/pinned | Known advisories | Fixed in |
|---|---|---|---|
| `starlette` | 0.37.2 (matches `backend/requirements.txt:122` pin) | PYSEC-2026-161, -248, -249, -1943, -1941, -2281, -2280 | 1.0.1 / 1.3.0 / 1.3.1 / 0.40.0 / 0.47.2 / 1.1.0 |
| `pymongo` | 4.5.0 (matches pin) | PYSEC-2026-1826 | 4.6.3 |
| `PyJWT` | 2.7.0 (matches pin) | PYSEC-2026-120, PYSEC-2025-183, -179, -175, -177 | 2.12.0 / 2.13.0 |
| `python-multipart` | 0.0.22 (matches pin) | PYSEC-2026-3038, -3037, -3036, -3040, -3039 | 0.0.26 / 0.0.30 / 0.0.31 / 0.0.27 |
| `python-dotenv` | 1.2.1 (matches pin) | PYSEC-2026-2270 | 1.2.2 |
| `pytest` | 9.0.2 (matches pin) | PYSEC-2026-1845 | 9.0.3 |
| `black` | 26.1.0 (matches pin) | PYSEC-2026-2121, -2120 | 26.3.1 / 26.3.0 |

These are **pre-existing pins in `backend/requirements.txt`** (except `black`, which is this phase's own CI tooling choice, pinned to the version this session used throughout — trivially bumpable). None were introduced by Phase 1 or Phase 2 code changes. Not fixed in this session: bumping any of these (especially `starlette`, which FastAPI 0.110.1 has its own compatibility range for) needs its own regression pass against the 335 integration tests this sandbox cannot run — see `reports/10_TEST_INFRASTRUCTURE.md`. Flagged here as the concrete, evidenced list a maintainer should triage first.

**Not scannable at all**: `cryptography` — the version actually resolvable alongside `webauthn==3.0.0` in a clean install is contested (see `10_TEST_INFRASTRUCTURE.md` §2d); `pip-audit` against whatever is installed in this sandbox reported the *system* apt package (41.0.7, several CVEs, none of them the pinned `46.0.4`) — not reported as a finding against the repo's own pin because it is not evidence of what a real install resolves to.

## 4. CORS, authentication, authorization — re-verified from Phase 1, no regressions

- `cors_origins_from_env()` (`backend/server.py:82-98`) — unchanged this phase, re-read: still fails closed on missing/wildcard `CORS_ORIGINS` in production.
- `backend/frek_v1/auth.py` (OAuth2 client-credentials, hashed tokens, revocation check) — unchanged this phase.
- New: `backend/permissions/` (Phase 2, Priority 3) is **not wired into any route** — see `12_PHASE2_IMPLEMENTATION.md` for why. It therefore introduces **zero** change to what is actually enforced on any live endpoint today; it is reviewed here only because it will be the enforcement layer once wired.

## 5. Input validation review — new modules

- `backend/registry/routes.py` `POST /validate`: `payload: Dict[str, Any]` accepts arbitrary JSON, but the only thing done with it is `jsonschema.Draft202012Validator(...).iter_errors(payload)` — a pure, side-effect-free validation call (re-confirmed this phase, no change since Phase 1).
- `backend/permissions/models.py`: every field is a typed Pydantic model (`Role`, `Action`, `ScopeType` are closed `Enum`s) — an invalid role/action/scope value is rejected by Pydantic before `engine.decide()` ever sees it.
- `backend/audit_trail/models.py`: `result` is a `Literal["allow", "deny", "success", "failure"]` — validated by Pydantic (`test_audit_event_result_is_constrained_to_known_values`).

## 6. Error leakage / logging of sensitive data

- `identity_engine/routes.py`'s new `logger.warning("identity.created event publish failed (non-blocking)", exc_info=True)` logs the exception traceback, not the identity payload itself — no PII/credential leakage into logs from this addition.
- No new module logs a raw payload, credential, or secret at any level (grep across all 7 new packages for `logger\.\w+\(.*payload\|credential\|secret\|password` → no matches).

## 7. Rate limiting

Unchanged this phase (`backend/security/policies.py`). None of the new modules add an unauthenticated, expensive operation reachable over HTTP (they add no new route at all — see §2).

## 8. Summary of Phase 2 security posture

| Area | Status |
|---|---|
| Secrets in repo | Clean (re-verified) |
| New HTTP attack surface | None (no new routes) |
| Dependency vulnerabilities | Real, pre-existing, documented above — not fixed this phase (needs a regression pass this sandbox cannot run) |
| CORS / auth / authz | Unchanged, re-verified, no regression |
| Input validation on new code | Typed end-to-end (Pydantic + JSON Schema) |
| Logging hygiene on new code | Clean |
| Permission Engine | Model only, not enforced anywhere yet — **do not treat `backend/permissions/` as providing any actual access control today** |
