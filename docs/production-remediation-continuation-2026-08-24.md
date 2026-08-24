# Production remediation continuation checklist — 2026-08-24

## Reference state

The starting commit is `e6f4f79` (`Harden bootstrap credentials and offline IDs`). The
P0 CORS, empty client-secret seed, default Staff PIN, committed credential literal, and
scanner identifier fixes remain in place and are intentionally out of scope for rework.

## Continuation matrix

| ID | Severity | Finding from continuation audit | Decision | Status |
| --- | --- | --- | --- | --- |
| P1-01 | P1 | `frontend/src/scan/lib.js` used IndexedDB but only stored `attempts: 0`; `flushQueue` sent every entry immediately and deleted successes. | Added a durable state machine, bounded exponential retry, failure classification, correlation IDs, persisted timestamps/errors, and policy tests. Full browser reload/reconnect replay remains an E2E validation item. | Remediated in code; E2E validation pending |
| P1-02 | P1 | FastAPI has an OpenAPI schema only when `FREK_PUBLIC_DOCS=true`; no committed schema or deterministic validation command exists. | Add a generation/validation command that enables schema generation locally without exposing production docs, commit the artifact, and check drift. | Pending |
| P1-03 | P1 | Startup has automatic drop/recreate index repair and several silent/best-effort exception paths. | Remove destructive automatic index repair; add documented preflight migration tooling. Treat remaining optional integrations explicitly. | Pending |
| P1-04 | P1 | Unique index repair can drop an index before checking duplicate data. | Replace it with a duplicate-reporting migration preflight; no automatic cleanup or drops. | Pending |
| P1-05 | P1 | `/scanner` and `/poste` own a separate `frek_offline_queue` in localStorage. Search confirms only these two pages use it. | Migrate local records into the staff IndexedDB queue before deleting localStorage; preserve unsupported entries for manual review. | Pending |
| P1-06 | P1 | `App.jsx` has public, Staff, Admin, and legacy routes in one route list; backend—not UI hiding—remains the security boundary. | Do not refactor routes until current scanner queue boundaries are consolidated and direct-route usage is assessed. | Pending |
| P1-07 | P1 | Scanner has camera/GPS cleanup, but the legacy Web NFC reader has no lifecycle cancellation; QR wrapper suppresses cleanup failures. | Add explicit lifecycle audit/tests after queue work. | Pending |
| P1-08 | P1 | Critical Moment/FK/identity/notary paths require a database-backed integration audit before transactional changes. | Do not alter historical data/event semantics without a running Mongo test environment and migration plan. | Pending |
| P1-09 | P1 | No generic projection/reconciliation command was identified. | Document sources/projections first; implement only against observed divergence. | Pending |
| P1-10 | P1 | Schemas use existing per-domain fields/protocols; no validated incompatible schema change is part of this batch. | Preserve current schemas and add versions only alongside an actual compatibility migration. | Pending |
| P1-11 | P1 | Public `/api/status` remains unauthenticated and unpaginated; sensitive routes need endpoint-by-endpoint consumer review. | Keep open until consumer/use analysis is complete. | Pending |
| P2-01..05 | P2 | Design-system, accessibility, performance and proof-UX work requires dedicated product/usage review. | Defer until P1 evidence is complete. | Deferred |
| P2-06 | P2 | Full Creator→Verification E2E needs Mongo plus configured credentials/WebAuthn/browser hardware. | Add automated queue tests now; retain end-to-end scenario as environment-gated validation. | Pending |

## Test-environment findings

`backend/requirements.txt` already declares `python-dotenv`, FastAPI and related backend
dependencies, but the active Python interpreter has none of them installed. This is an
environment provisioning defect, not a missing repository dependency. The frontend declares
ESLint but has no ESLint configuration file, which is a repository defect to correct in this
batch. No production data, Mongo collection, route, or ecosystem contract was modified by
this continuation audit.

## Offline state-machine contract

Scanner operations are retained in IndexedDB by their `client_uuid` idempotency key and
correlation ID. Their persisted state is one of `queued`, `processing`, `succeeded`,
`retrying`, or `dead_letter` (with `cancelled` reserved for a future explicit user action).
Temporary failures (network, timeout, 401, 408, 429 and 5xx) are retried after a bounded
deterministic exponential delay; validation/authorization/conflict failures are placed in
`dead_letter` immediately. A success is retained as `succeeded` rather than being silently
discarded, so the terminal outcome is observable and a reload cannot enqueue a duplicate.
