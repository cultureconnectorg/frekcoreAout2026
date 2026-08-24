# FREKCORE production-hardening audit — 2026-08-24

## Scope and method

This is a repository-static audit completed before remediation. It inspected the FastAPI
composition and route registrations, authentication and authorization helpers, MongoDB
index startup, frontend routes and scanner/offline code, ecosystem registry/contracts,
dependency manifests, existing test suites and reports, and tracked secrets. No data was
deleted, reset, migrated, or modified during this audit.

The repository has a deliberately additive architecture: FREKCORE owns the core trust
layer. `ecosystem/registry.json`, `ecosystem/capabilities.json`, and the contracts under
`ecosystem/contracts/` describe external FREKRAW, FREKANSLA, and FREK V3 boundaries; none
should be folded into this application.

## Audit matrix

| ID | Severity | Component | Problem | Impact | Cause | Proposed correction | Regression risk | Necessary tests | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC-001 | P0 | Git history / integration tests | Reusable API client secrets and an admin key are committed as test defaults. | An attacker can mint bearer tokens or administer protected surfaces where the deployed values were reused. | Credentials were used as convenient live-test defaults. | Remove literals, require environment credentials in CI, and rotate the exposed deployed secrets outside the repository. | Tests that assumed local real credentials now require explicit configuration. | Credential-source tests; secret scanner; authenticated integration suite with CI secrets. | Remediated in code; **operational rotation remains required**. |
| SEC-002 | P0 | FastAPI CORS | `CORS_ORIGINS` defaults to `*` while credentials are enabled. | Cross-origin credentialed requests have an unsafe / invalid policy boundary. | Permissive development default reached production configuration. | Parse and validate an explicit allowlist; use localhost-only development defaults and reject wildcard with credentials. | Deployments relying on wildcard must configure origins. | Configuration unit tests; browser preflight integration test. | Remediated. |
| SEC-003 | P0 | API-client bootstrap | Missing client-secret environment values are hashed and seeded, permitting the predictable empty secret for newly seeded clients. | Authentication bypass after misconfigured deployment. | Startup treated an absent secret as a valid seed value. | Never seed a client without a nonblank secret; log an actionable error. | A first boot missing required config has no seeded API clients, intentionally fail-closed. | Startup helper unit tests; token endpoint rejects empty secret. | Remediated. |
| SEC-004 | P0 | Staff bootstrap | Published, deterministic default PINs create privileged staff accounts when environment configuration is omitted. | Anyone with repository access could obtain staff/scanner privileges on a fresh deployment. | Startup seeds default credentials. | Require per-account PIN environment values; allow sample PINs only by explicit non-production development opt-in. | Fresh misconfigured deployments have no seeded staff accounts, intentionally fail-closed. | Startup helper unit tests; staff login integration with configured PIN. | Remediated. |
| INT-001 | P0 | Staff scanner offline queue | The queue UUID fallback uses `Math.random()`. | Offline idempotency keys can collide on unsupported/older WebViews, causing duplicate or incorrectly deduplicated staff operations. | A non-cryptographic UUID fallback. | Use `crypto.randomUUID` or `crypto.getRandomValues`; fail explicitly if neither secure browser primitive exists. | Unsupported legacy WebViews must upgrade rather than silently enqueue unsafe requests. | UUID format/uniqueness test; offline replay test. | Remediated. |
| INT-002 | P0 | Legacy `/scanner` page | Legacy scanner generates business idempotency UUIDs with `Math.random()` and persists its own localStorage queue. | Same collision risk and a divergent, less durable offline flow. | Legacy route predates the IndexedDB staff scanner. | Replace UUID generator with Web Crypto and identify the legacy queue as P1 migration work. | Legacy WebViews without Web Crypto cannot enqueue. | Scanner UUID test; legacy route compatibility check. | Remediated for identifier generation. |
| INT-003 | P1 | Staff scanner sync | Durable IndexedDB queue has persistence and server idempotency but no per-item retry schedule/backoff/status beyond an attempts counter. | Repeated temporary failures can be retried aggressively and operators lack per-item state. | Initial implementation only flushes all queued actions. | Add bounded retry metadata/backoff and test reload/reconnect replay. | Changes to queue shape require IndexedDB migration. | Offline → reload → reconnect E2E test; transient failure test. | Open. |
| API-001 | P1 | OpenAPI | OpenAPI is deliberately disabled by default, but there is no checked generated schema or CI contract comparison. | Frontend/API drift can evade review. | Production attack-surface restriction omitted a build-time contract artifact. | Generate and validate an authenticated CI OpenAPI artifact without enabling public docs in production. | CI configuration work. | OpenAPI snapshot/schema validation. | Open. |
| OBS-001 | P1 | Runtime errors | Several best-effort startup/integration paths still swallow exceptions after logging or without structured error taxonomy. | Dependency failures can be hard to correlate and reconcile. | Incremental additive modules use independent error styles. | Consolidate structured correlation IDs and explicit dependency error handling, prioritizing proof/anchor operations. | Logging format changes. | Dependency outage tests. | Open. |
| DATA-001 | P1 | Mongo startup indexes | Existing index repair can drop and recreate an index when options conflict. | During a migration race, writes may temporarily lose uniqueness protection. | Startup attempts automatic index self-repair. | Move index-option changes to a documented, audited migration command with duplicate preflight. | Deployment process change. | Migration dry-run against production-shaped dump. | Open. |
| FE-001 | P2 | Frontend token storage | Identity and staff bearer tokens are stored in localStorage. | XSS would expose bearer credentials. | Existing API uses header bearer/session tokens rather than HttpOnly cookies. | Design a CSRF-aware HttpOnly cookie/session migration; do not change protocol piecemeal. | Cross-origin/mobile clients. | XSS/session migration tests. | Open. |
| FE-002 | P2 | Legacy `/scanner` queue | Legacy scanner queue is localStorage, whereas `/poste` uses IndexedDB. | The legacy route does not meet the durable offline queue requirement. | Parallel retained legacy UI. | Trace usages, then migrate or formally retire only after compatibility evidence. | Existing users may rely on the route. | Route telemetry/replay tests. | Open. |
| PERF-001 | P2 | Public status endpoint | `/api/status` lists up to 1,000 records without authentication or pagination. | Unnecessary data exposure and avoidable query load if used. | Scaffold endpoint remains enabled. | Confirm consumers, then protect or retire with deprecation process. | Legacy demo clients. | Consumer search and authorization test. | Open. |

## Data and migration assessment

No schema migration is necessary for the P0 remediations in this change: they alter
configuration validation and client-side identifier generation only. Existing FREK-ID,
Moments, FK, Heritage, Audit, FREK-Chain, and relationship collections are neither written
nor reset. The existing startup index definitions and append-oriented event/notary modules
were inspected; DATA-001 is deliberately left open rather than performing a destructive
index operation without a production-data duplicate preflight and rollback plan.

## Decision record

P0 remediation is limited to verified vulnerabilities and integrity defects above. It does
not create external endpoints, adapters, product features, migrations, or ecosystem branch
implementations. Remaining P1/P2 work is explicitly tracked instead of being represented as
complete.
