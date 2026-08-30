# 04 — API Contract — FREKCORE

## 1. Existing contract mechanism (evidence)

- FastAPI auto-generates OpenAPI from Pydantic v2 models at `app.openapi()`.
- `scripts/export_openapi.py` exports it to `openapi/frekcore.openapi.json` (`--check` mode diffs the committed artifact against a fresh generation — a drift gate, though it is not wired into any CI workflow, see `07_DEPLOYMENT_REPORT.md`).
- Swagger UI / ReDoc / raw `openapi.json` are **disabled by default** in production (`backend/server.py:161-168`, gated by `FREK_PUBLIC_DOCS`) — a deliberate IP-protection doctrine documented in `memory/IP_PROTECTION_STRATEGY.md`, not an oversight.
- No dedicated error-response schema exists: errors are raised as `HTTPException(status_code=..., detail=...)` ad hoc per route (confirmed by sampling `identity_engine/routes.py`, `notary/routes.py`, `fk/routes.py`) — FastAPI's default `{"detail": "..."}` shape is what clients actually receive, undocumented as a formal schema.

## 2. Route families present today (Master Prompt Bloc 8 vocabulary)

| Family (Master Prompt) | Present under | Status |
|---|---|---|
| Identity (CRUD + Search) | `/api/v1/identity/*` (`identity_engine/routes.py`) | PARTIAL — init/me/register/authenticate exist; no search/merge/archive (see `02_GAP_ANALYSIS.md`) |
| Registry (FREK types) | `/api/v1/registry/*` | **DELIVERED this session** (`backend/registry/routes.py`) |
| Proof (Generate/Verify) | `/api/v1/notary/*`, `/api/v1/passport/*` | EXISTS, different route names than the prompt's `/proof`, `/verify` |
| Certificates (Issue/Verify) | `/api/v1/badges/*` (event badges, not Academy certs) | PARTIAL/MISSING for the Academy use case (see `02_GAP_ANALYSIS.md` Bloc 5) |
| Events (Publish/Subscribe) | none (see Bloc 7 gap) | MISSING; catalog only at `/api/v1/registry/events` |
| Health | `/api/v1/health/live`, `/api/v1/health/deep` | EXISTS |
| Admin | `/api/v1/admin/*` (`health/routes.py: admin_ops_router`) | EXISTS |

## 3. New endpoints added this session (`backend/registry/routes.py`)

All mounted under `/api/v1/registry` (stateless, no auth required — read-only schema catalog, matches the existing public-doc-style endpoints like `/api/v1/spec/*` and `/api/v1/passport/verifier/*`):

| Method | Path | Description | Response model |
|---|---|---|---|
| GET | `/api/v1/registry/versions` | List available schema-set versions (`v1`, ...) | `{"versions": [...], "default": "v1"}` |
| GET | `/api/v1/registry/namespaces` | List all 8 FREK Registry namespaces with title/description/schema URL | `List[NamespaceSummary]` |
| GET | `/api/v1/registry/namespaces/{namespace}` | Return the full JSON Schema (draft 2020-12) for one namespace | raw JSON Schema |
| POST | `/api/v1/registry/validate` | Validate an arbitrary payload against a namespace's schema | `ValidateResponse {valid, errors[]}` |
| GET | `/api/v1/registry/events` | Bloc 7 Event Registry catalog (envelope schema + 9-event catalog with implementation status) | raw JSON |

Example (as tested in `backend/tests/test_registry.py`):

```
POST /api/v1/registry/validate
{
  "namespace": "frek.artist",
  "payload": {
    "frek_id": "id-abcdef012345-ab12",
    "entity_type": "frek.artist",
    "status": "active",
    "created_at": "2026-08-30T00:00:00Z",
    "display_name": "Luciole"
  }
}
→ 200 {"valid": true, "namespace": "frek.artist", "schema_version": "v1", "errors": []}
```

Because these routes use standard FastAPI `response_model=` Pydantic classes, `python scripts/export_openapi.py` will pick them up automatically the next time it is run (not executed in this sandbox — see `06_TEST_REPORT.md` for why).

## 4. Versioning

- All existing routes are mounted under `/api` or `/api/v1` — there is no `/api/v2` anywhere (`grep -rn "api/v2"` → no matches), so "API versioning" per Bloc 8 is currently a single frozen `v1` surface plus one legacy unversioned `/api/*` (`frek_router`, `frek_v1` router mounted at `/api` not `/api/v1` — see `server.py:217-221`).
- The new Registry endpoints follow the `v1` convention and additionally version their **schema payloads** independently (`schema_version` query/body param, defaulting to `v1`) so namespace schemas can evolve without an API version bump — this satisfies the Master Prompt's "chaque namespace possède un JSON Schema versionné" requirement at the schema level, not yet at the route level (no `v2` registry routes exist, none were needed).

## 5. Gaps not addressed this session

- No formal `ErrorSchema` (Bloc 8 asks for one explicitly).
- No `/proof` / `/verify` top-level aliases matching the Master Prompt's literal route names (existing `/notary/notarize` and `/passport/*` cover the same capability under different names — renaming risks breaking existing integrations per the "never break an existing API" invariant, so aliasing rather than renaming would be the correct next step, not attempted here to keep this session's diff minimal and reviewable).
