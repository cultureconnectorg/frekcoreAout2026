# 05 — Security Report — FREKCORE

## 1. Authentication mechanisms found (evidence)

| Actor | Mechanism | Evidence |
|---|---|---|
| API clients (server-to-server, e.g. Culture Connect, CVL Brain) | OAuth2 client-credentials → JWT-like access token, hashed at rest | `backend/frek_v1/auth.py:61-90`, tokens stored as `hash_secret(access_token)` in `frek_tokens`, revocable (`token_doc.get("revoked")`, line 41-42) |
| End users | WebAuthn/Passkey registration+authentication, stateless HMAC session token (90-day TTL) | `backend/identity_engine/service.py:36-37,216-251` |
| Field staff | PIN login with lockout | `backend/staff/routes.py` (`db.staff.create_index("locked_until", ...)`, `server.py:568-569`) |

Client secrets are never defaulted: `configured_client_secret()` (`server.py:101-104`) returns `None` on empty env var, and seeding **refuses** to create a client without one (`server.py:474-483`, logs an error and skips). This is a real fail-closed behavior, verified by reading the code path, not assumed.

## 2. Authorization

- `require_permission(permission: str)` (`frek_v1/auth.py:50-58`) is a flat allow-list check (`permission not in client.get("permissions", [])`) — **not** hierarchical RBAC, **not** the Founder/Executive/Artist/Student/Teacher/Admin-Label/Agent role vocabulary the Master Prompt specifies (Bloc 6). See `02_GAP_ANALYSIS.md` row 6.
- No scope-based JWT claims were found (`grep -rn "scope" backend/frek_v1/` → no matches beyond the word "scope" in comments); permissions are a flat string list per client document.

## 3. CORS

`cors_origins_from_env()` (`server.py:82-98`) **fails fast** in production if `CORS_ORIGINS` is unset or contains `"*"` — wildcard origins are explicitly rejected because they are incompatible with `allow_credentials=True`. This is a correct, defensive implementation, confirmed by reading the raise conditions, not inferred.

## 4. Rate limiting & audit trail

- `backend/security/policies.py` + `backend/security/routes.py` implement rate limiting (`rate_limits` collection, purged between test runs per `tests/conftest.py:25-37`) and an "anomaly trail" (module docstring: "rate limiting silencieux + audit trail", `server.py:42-44`).
- `backend/audit/routes.py` provides a human-readable timeline aggregator over `frek_stages`, `scans`, `transactions`, `notary_blocks` (lines 1-8) — this is an operational audit view, separate from `security/`'s anomaly trail.

## 5. Cryptography

- Ed25519 signing (`backend/passport/keys.py`) for passports and FK attestations; **no evidence of key rotation tooling** (`grep -rn "rotate" backend/passport/` → no matches) — a single long-lived keypair per `KEY_ID` (`passport/service.py:125`).
- Session tokens use `hmac.compare_digest` (`identity_engine/service.py:243`) — correct constant-time comparison, not a naive `==`.
- `SECRET_KEY` is required at runtime with no default (`identity_engine/service.py:217-220`, raises `RuntimeError` if missing) and again in `docker-compose.yml` (`SECRET_KEY: ${SECRET_KEY:?Set SECRET_KEY...}` — fails to start the container rather than running with an empty secret).

## 6. What Bloc 6 (Zero Trust) explicitly asks for that is MISSING

| Requirement | Status | Evidence |
|---|---|---|
| CVLN role vocabulary (Founder/Executive/Artist/Student/Teacher/Admin Label/Agent) | MISSING | grep negative across `backend/` |
| JWT **scopes** (as opposed to flat permission strings) | MISSING | see §2 |
| Distinct "API Keys" as a first-class concept separate from OAuth2 client-credentials tokens | PARTIAL | `frek_clients`/`frek_tokens` conflate the two; no dedicated API-key model |
| Unified audit log across *all* privileged actions | PARTIAL | `audit/` + `security/` cover different slices; no single append-only security event log spans both |

## 7. New surface added this session — security review

`backend/registry/routes.py` adds 5 **read-only, unauthenticated** GET/POST endpoints. Threat-model review performed before merging:

- **No database access** — the module has no `set_db()` and cannot read/write MongoDB, so it cannot be used to exfiltrate or corrupt application data.
- **No file-path input from the client** — `namespace` is matched against an in-memory dict keyed by values loaded from a fixed, repo-committed directory (`backend/registry/schemas/v1/`); it is never used to construct a filesystem path from user input (no path traversal surface).
- **`POST /registry/validate`** accepts an arbitrary JSON `payload` but only ever passes it to `jsonschema.Draft202012Validator(...).iter_errors(payload)` — a pure, side-effect-free validation call. No `eval`, no dynamic imports, no code execution paths.
- Left **unauthenticated by design**, consistent with existing public documentation endpoints (`/api/v1/spec/*`, `/api/v1/passport/verifier/*`) — this is a schema catalog, equivalent in sensitivity to serving a static OpenAPI file.

No new secrets, no new database writes, no new authentication bypass were introduced.

## 8. Recommendations (not implemented this session — see `08_NEXT_INTEGRATION.md`)

1. Design and implement the CVLN role model (Bloc 6) before granting any external system (Wallet, KORA, Academy, ...) programmatic access to FREKCORE.
2. Add key-rotation tooling for the Ed25519 signing key.
3. Add a request-ID / correlation-ID middleware (also needed for Bloc 11 observability) so security audit trails can be correlated end-to-end.
