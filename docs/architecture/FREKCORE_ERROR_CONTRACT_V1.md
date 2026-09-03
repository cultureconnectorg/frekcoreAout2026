# FREKCORE Error Contract — v1

STATE_7 (2026-09-03). Canonical error semantics for `/api/v1/...`
endpoints, and an honest audit of what today's endpoints actually return.

## Canonical error codes

| Code | HTTP status | Meaning |
|---|---|---|
| `INVALID_REQUEST` | 400 / 422 | Malformed input (bad base64, unreadable content, missing/invalid field) |
| `AUTHENTICATION_REQUIRED` | 401 | No credential supplied where one is required (reserved — see "Current status" below) |
| `AUTHORITY_DENIED` | 403 | A credential was supplied but does not authorize this action (wrong admin key, session for the wrong identity, insufficient scope) |
| `NOT_FOUND` | 404 | Referenced resource does not exist |
| `CONFLICT` | 409 | A same-key-different-payload idempotency conflict, or a genuine state conflict (D4's `CONFLICT` sync_status) |
| `RATE_LIMITED` | 429 | `security.policies.check_rate_limit` denied the call |
| `IDEMPOTENCY_CONFLICT` | 409 | Same idempotency key, different payload (see `FREKCORE_VERSIONING_POLICY.md` §7) — a specific case of `CONFLICT`, named separately because the mission brief names it separately |
| `VERIFICATION_FAILED` | 422 | A cryptographic or structural verification step failed (signature invalid, malformed envelope/proof) |
| `STALE_AUTHORITY` | 200/409 (context-dependent) | Not an HTTP failure by itself — a *content* status (`AuthorityStatus.STALE`, `LocalValidationStatus.CRYPTO_VALID_BUT_STATUS_STALE`) already returned inline in D4 responses; listed here for completeness, never itself raised as an exception |
| `REVOKED` | 403 / 200 (content-dependent) | An identity/device/credential is revoked — either blocks the action (403) or is reported inline (`FreshnessInfo.status=REVOKED`) depending on the endpoint, per existing D4 behavior |
| `UNSUPPORTED_VERSION` | 400 | Reserved for a future `v2` cutover — no `v1` endpoint returns this today (no version negotiation exists yet, honestly) |
| `INTERNAL_ERROR` | 500 | Unhandled server fault |

This is the founder's own named list, adopted verbatim — no additional
error class was invented (`FrekcoreError` in the SDK, see
`FREKCORE_SDK_CONTRACT_V1.md`, maps 1:1 to this table, not a second
taxonomy).

## Current status — honest audit, not retrofitted

**Every canonical `/api/v1/...` endpoint built through D1–D5 already
returns the *correct HTTP status* for each case above** (403 for bad
admin key, 404 for missing resource, 429 for rate limit, 400/422 for
malformed input) — confirmed by re-reading every `raise HTTPException`
call site across `content_binding/`, `creative_lifecycle/`,
`relationship_graph/`, `offline_transport/`, `technical_evidence_report/`
this pass. **What is missing is a machine-readable `code` field
distinct from the human-readable `detail` string** — today's `detail`
values are a mix of English/French, some snake_case
(`"invalid_admin_key"`), most free-text (`"Trop de requetes"`,
`f"Binding {binding_id} introuvable"`). A consumer today can reliably
branch on **HTTP status** (already correct and stable) but not on a
stable **error code string** independent of message wording/language.

**This is a disclosed gap, not fixed by rewriting every existing route
this state** (`REWRITE_D1_D6_ARCHITECTURE=FALSE`, and retrofitting ~40
raise sites across 5 modules is exactly the kind of invasive change that
rule exists to prevent mid-contract-stabilization). Instead, STATE_7
adds the canonical vocabulary (`backend/errors.py`, below) that:

1. **New canonical endpoints built from STATE_7 forward should use.**
2. **Every SDK method (Python and TypeScript) maps HTTP status → the
   matching canonical error class** regardless of whether the server's
   `detail` string is already machine-readable — status-code mapping
   alone is sufficient and already 100% reliable today, so the SDK
   error model is fully usable *now*, even before every server route
   adds an explicit `code` field.

## `backend/errors.py` — the canonical vocabulary

New, pure module (no FastAPI/route dependency, importable from any
future canonical route): `ErrorCode` (the `str` enum matching the table
above) and `CanonicalError` (an exception carrying `code: ErrorCode`,
`message: str`, `http_status: int`, optional `details: dict` — safe for
disclosure, never raw exception internals) plus `to_http_exception()`
producing a FastAPI `HTTPException(status_code=..., detail={"code":
..., "message": ..., "details": ...})` — a structured `detail` object,
strictly additive over today's plain-string convention (a consumer
reading `.detail` as a string today would see a dict instead only on
endpoints that adopt this — no existing endpoint's `detail` shape
changes retroactively).

## No raw internal exceptions

Verified, not assumed: `server.py`'s `FastAPI(...)` construction does not
set `debug=True` — Starlette's default `ServerErrorMiddleware` therefore
returns a bare `{"detail": "Internal Server Error"}` (no stack trace, no
exception class name, no file paths) for any unhandled exception,
confirmed from Starlette's own documented default behavior. No canonical
route this session has ever caught and re-raised a raw `PyMongoError`,
cryptography exception, or filesystem error directly to the client —
every catch site either translates to a canonical `HTTPException` with a
safe message, or (for best-effort side effects: notarization, event
publishing) swallows the exception entirely behind a `try/except ...
logger.warning(..., exc_info=True)` (server-side log only, never
returned to the caller) — the same pattern independently established in
every D1–D5 module's own `_publish_and_notarize`/equivalent helper.

## Privacy in error responses

No canonical error response includes: raw credential/key material,
another user's private data, full internal object dumps, or Mongo
`_id` values (every `find_one`/`find` in D1–D5 explicitly projects
`{"_id": 0, ...}`, confirmed repeatedly across this session's own code).
404 responses are used deliberately over 403 where existence itself is
sensitive (D3/D5's own "404, not 403" privacy discipline, documented in
their own ADRs) — this contract preserves that distinction rather than
flattening every denial to 403.
