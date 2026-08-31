# 17 — Security Final (Phase 3, Priority 11)

Updates and extends `reports/11_SECURITY_PHASE2.md` (Phase 2). This report reflects what changed in Phase 3.

## 1. Dependency audit — now runs against the REAL `backend/requirements.txt`

Phase 2 could only audit a curated subset (`requirements-ci.txt`) because the real file wouldn't resolve. Phase 3 fixed both blockers (`reports/15_DEPENDENCY_REMEDIATION.md`), so this is the first genuinely comprehensive dependency audit of this codebase:

```
$ pip-audit -r <(grep -v '^emergentintegrations' backend/requirements.txt)
Found 115 known vulnerabilities in 20 packages
```

By package (advisory count, not deduplicated across CVE aliases):

| Package | Installed | Advisories found | Fix available |
|---|---|---|---|
| `pillow` | 12.1.0 | 27 | 12.1.1 – 12.3.0 (several) |
| `aiohttp` | 3.13.3 | 25 | 3.13.4 / 3.14.0 / 3.14.1 / 3.14.2 / 3.14.3 |
| `litellm` | 1.80.0 | 12 | 1.82.0 – 1.84.0 (several) |
| `pyjwt` | 2.11.0 | 11 | 2.12.0 / 2.12.1 / 2.13.0 |
| `starlette` | 0.37.2 | 9 | 0.40.0 / 0.47.2 / 1.0.1 / 1.1.0 / 1.3.0 / 1.3.1 |
| `pyasn1` | 0.6.2 | 6 | 0.6.3 / 0.6.4 |
| `python-multipart` | 0.0.22 | 5 | 0.0.26 / 0.0.27 / 0.0.30 / 0.0.31 |
| `urllib3` | 2.6.3 | 3 | 2.7.0 |
| `black` | 26.1.0 | 3 | 26.3.0 / 26.3.1 |
| `idna` | 3.11 | 2 | 3.15 |
| `httplib2` | 0.31.2 | 2 | 0.32.0 |
| `ecdsa` | 0.19.1 | 2 | 0.19.2 (one, PYSEC-2026-1325, has **no fix version listed** — a known, long-standing `python-ecdsa` design limitation around side-channel timing, not a simple version bump) |
| `requests` | 2.32.5 | 1 | 2.33.0 |
| `python-dotenv` | 1.2.1 | 1 | 1.2.2 |
| `pytest` | 9.0.2 | 1 | 9.0.3 |
| `pymongo` | 4.5.0 | 1 | 4.6.3 |
| `pygments` | 2.19.2 | 1 | 2.20.0 |
| `msgpack` | 1.1.2 | 1 | 1.2.1 |
| `cryptography` | 49.0.0 | 1 | 50.0.0 (down from 8 advisories on the pre-Phase-3 pin of 41.0.7 — see `reports/15_DEPENDENCY_REMEDIATION.md`) |
| `click` | 8.3.1 | 1 | 8.3.3 |

**Reachability/exploitability note** (per this phase's instruction to classify by severity × exploitability, not bump blindly): `litellm`, `google-generativeai`, `google-ai-generativelanguage` are pulled in transitively but this session found **no evidence any FREKCORE route actually calls an LLM** (`grep -rn "litellm\.\|genai\." backend/ --include="*.py"` outside the dependency's own package → no matches in FREKCORE's own code) — these advisories are present in the dependency tree but likely unreachable from any real FREKCORE code path. Not verified further this phase; flagged rather than dismissed.

**Not fixed this phase**: bumping 20 packages blind, without the integration suite fully green against a real MongoDB (`reports/16_INTEGRATION_TEST_BASELINE.md`), risks exactly the kind of untested regression this mission's rules forbid. `cryptography` was bumped (Phase 3 Priority 1, necessary to fix the install blocker, separately validated). Every other bump is `reports/FREKCORE_COMPLETION_BACKLOG.md` P0 #3.

## 2. Secrets — re-verified, still clean

```
$ grep -rniE "AKIA[0-9A-Z]{16}|sk_live_|sk_test_[a-zA-Z0-9]{10}|-----BEGIN (RSA |EC )?PRIVATE KEY-----" .
(no matches outside this report's own quoting of the pattern, and Phase 2's report which quotes it identically)
```

No secret was added by any Phase 3 change. The mongomock dev-server script (`scripts/run_dev_server_mongomock.py`) and its usage in this session's shell used only literal placeholder strings (`"dev-only-not-a-real-secret-mongomock-run"`, etc.), never a real credential — consistent with the "never require production secrets" instruction for lab/dev tooling.

## 3. Auth review — unchanged mechanisms, new evidence they work live

`backend/frek_v1/auth.py`, `backend/health/routes.py:_require_admin`, `backend/staff/`'s PIN auth — all unchanged in Phase 3. New this phase: **live confirmation** these actually reject bad credentials, not just "code looks right": the mongomock-backed integration run (`reports/16_INTEGRATION_TEST_BASELINE.md`) recorded real `401 Unauthorized` responses for wrong staff PINs and wrong OAuth2 client secrets, and real `403 Forbidden` for missing/wrong permissions on `POST /api/core/ingest`, `/api/v1/admin/clients`, and others — see the server log excerpts quoted in that report.

## 4. CORS — unchanged, re-verified

`cors_origins_from_env()` (`backend/server.py`) untouched this phase. Re-read: still fails closed on missing/wildcard origins in production.

## 5. Error leakage — new surface reviewed

- `GET /api/metrics` (new, Phase 3): exposes only Prometheus counters/histograms with closed-enum labels (method, path, status, operation, namespace, event_type) — no header value, FREK-ID, email, or stack trace. Reviewed in `reports/18_RUNTIME_VALIDATION.md` Priority 7.
- `backend/audit_trail/mongo_recorder.py` / `subscribers.py` (new, Phase 3): a failed write logs `exc_info=True` (a traceback) at `WARNING` level — the traceback can include the exception's string representation, which for a Mongo connectivity failure is safe (host/port, not credentials — Motor does not include the password in its default exception messages), but this was not exhaustively fuzzed this phase. Flagged, not fixed: `reports/FREKCORE_COMPLETION_BACKLOG.md`.
- `backend/storage/emergent_object_storage.py` (new, Phase 3): raises `requests.HTTPError`/`ObjectStorageUnavailable` with no embedded secret (the `EMERGENT_LLM_KEY` is never included in an exception message — verified by reading the class, it's only ever used as a request parameter, never interpolated into a string).

## 6. Rate limiting — unchanged

`backend/security/policies.py` untouched. No new unauthenticated, expensive route was added this phase (the one new route, `GET /api/metrics`, is a cheap in-memory read of counters that already exist).

## 7. Insecure defaults — new finding this phase

`backend/services/webhook.py`'s now-lazy `emergentintegrations` import (`reports/15_DEPENDENCY_REMEDIATION.md`) degrades to a caught `ImportError` returned as `{"status": "error", "detail": "..."}"` with HTTP 200 (the existing handler's `except Exception` branch returns 200, not a 4xx/5xx — pre-existing behavior, not introduced by the lazy-import change, but worth noting: a caller cannot distinguish "package missing" from any other webhook processing error by status code alone, only by the `detail` string). Not changed this phase (would alter existing behavior beyond the scope of the dependency fix) — flagged in the backlog as a minor API-contract quality issue, not a security vulnerability (Stripe's own retry behavior is unaffected either way since Stripe does not require a 2xx to consider a webhook "received" in any way that FREKCORE's response body content could exploit).

## 8. What Phase 3's new code was itself reviewed for (self-audit)

Every new module this phase (`backend/audit_trail/mongo_recorder.py`, `subscribers.py`, `backend/storage/emergent_object_storage.py`, `backend/server.py`'s observability wiring) was checked for: no new database write path reachable without going through an existing, already-authenticated route (the audit trail is a *subscriber*, not a route — nothing can write to `audit_trail_events` except by first triggering a real event through `identity_engine`'s existing `/init` route); no new secret; no new unauthenticated mutation; no logging of a credential or full request body.

## Summary table (per the mission's maturity-area format, evidence-based, no invented score)

| Area | Status |
|---|---|
| Secrets in repo | VERIFIED clean |
| Dependency vulnerabilities | VERIFIED present (115 findings, 20 packages), NOT remediated (documented, prioritized) |
| CORS | VERIFIED correct (fail-closed) |
| Authentication mechanisms | VERIFIED working (live 401s observed) |
| Authorization on audited routes | PARTIAL (see `docs/PERMISSION_MATRIX.md` — most routes classified, some routes' enforcement not confirmed live) |
| New Phase 3 attack surface | VERIFIED reviewed, no new finding |
| Error leakage | PARTIAL (one flagged, not fixed, low-severity item) |
| Rate limiting | VERIFIED unchanged, no new gap introduced |
