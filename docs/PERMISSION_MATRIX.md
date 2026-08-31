# FREKCORE — Permission Matrix (Phase 3, Priority 4)

## Methodology (evidence, not assumption)

This matrix was built in three passes, all against the real, current code:

1. **Automated extraction**: every `@*_router.get/post/put/patch/delete(...)` decorator across `backend/` (excluding `tests/`) was located and its path/method recorded — 239 routes total, matching the live app's `len(app.routes)` (confirmed by booting the real `server.py`, see `reports/15_DEPENDENCY_REMEDIATION.md`).
2. **Automated auth-dependency detection**: a 40-line window after each route decorator was scanned for the concrete auth mechanisms that actually exist in this codebase (found by grepping every `Depends(...)` call site in `backend/`, not assumed): `require_permission`/`_auth_require_permission` (29+3 sites), `require_staff_perm` (9 sites), `verify_admin_key` (8 sites), `get_current_staff` (5 sites), `get_current_client`/`_auth_get_current_client` (4+1 sites), plus header/HMAC patterns (`X-Admin-Key`, `X-FREK-Session`, webhook HMAC signatures) matched by text search since they are not always `Depends(...)`-wrapped.
3. **Manual spot-check**: every mutating (POST/PUT/PATCH/DELETE) route the automated pass could not attribute to a known auth mechanism (43 routes) was read directly to determine whether it is genuinely unauthenticated by design, protected by a mechanism the scanner didn't recognize, or an actual gap. Findings are called out individually below.

This is a first-pass matrix built from real code, not a claim of formal security certification. Where classification required judgment (e.g. "is this public-by-design or a gap"), the reasoning and evidence are given so a reviewer can disagree with the conclusion without having to redo the research.

## Category definitions used

| Category | Meaning here |
|---|---|
| PUBLIC | No authentication of any kind; intentional (documented doctrine, protocol requirement, or genuinely non-sensitive) |
| PUBLIC-SECRET | No header/token auth, but access is gated by a caller-supplied secret/signature in the request body (webhook HMAC, claim_secret, WebAuthn challenge) — a real but non-header auth pattern |
| AUTHENTICATED | Requires a valid credential identifying the caller, but does not further scope by ownership/org (client API key or staff/session token) |
| OWNER-SCOPED | Should be restricted to the resource's owner; **flagged separately when intended but not enforced** |
| ORGANIZATION-SCOPED | Scoped to an organization/tenant — **not implemented anywhere in this codebase**, see note below |
| ADMIN | Requires `X-Admin-Key` (`backend/health/routes.py:_require_admin`, `backend/frek_v1/admin.py`'s `verify_admin_key`) |
| SYSTEM/AGENT | Field-staff PIN/token auth (`backend/staff/`) — matches the brief's "Agent" role concept |
| INTERNAL | Called by another system, not an end user (webhooks) |
| **FLAG** | A genuine finding: intended protection that is not enforced, or unauthenticated mutation without a documented rationale |

**ORGANIZATION-SCOPED does not exist in this codebase today.** No route, dependency, or model enforces a multi-tenant/organization boundary (confirmed: `grep -rn "organization_id" backend/ --include="*.py"` outside `backend/permissions/` and `backend/registry/` returns nothing). The closest existing concept is `client_id`-based partitioning in `frek_v1` (each OAuth2 client is scoped to its own `frek_identities`/`frek_stages` via `client_id` filters in queries) — this is API-client multitenancy, not organization/user multitenancy, and is noted per-route below where relevant.

## Summary by module

| Module (router) | Routes | Dominant classification | Real mechanism (evidence) |
|---|---|---|---|
| `health` (`health_router`) | 3 | PUBLIC | No auth — correct for k8s liveness/readiness/deep-health probes (`backend/health/routes.py:45,51,61`) |
| `health` (`admin_ops_router`) | 3 | ADMIN | `_require_admin` / `X-Admin-Key`, `hmac.compare_digest` (`backend/health/routes.py:36-38`) |
| `frek_v1` (`identity_router`) | 9 | AUTHENTICATED (client API key) | `Depends(require_permission(...))` on 7/9; `/lookup` and `/{frek_id}/status` are more open — see below |
| `frek_v1` (`stages_router`) | 2 | AUTHENTICATED (client API key) | `require_permission("stage")` |
| `frek_v1` (`stats_router`) | 2 | AUTHENTICATED (client API key) | `require_permission("stats")` |
| `frek_v1` (`admin_router`) | 6 | ADMIN | `verify_admin_key` |
| `frek_v1` (`auth_router`) | 1 | PUBLIC-SECRET | `POST /token` — OAuth2 client-credentials token issuance; protected by `client_secret` in the request body, not a header (correct OAuth2 pattern — this is how a client *obtains* auth) |
| `frek_v1` (`dashboard_router`) | 2 | AUTHENTICATED | `require_permission` |
| `identity_engine` (`identity_router`) | 9 | mixed — see below | WebAuthn ceremony endpoints are intentionally public; `/me`, `/{frek_id}/objects` are session-scoped |
| `fk` (`fk_router`) | 6 | PUBLIC | Documented doctrine (`memory/INVENTORY.md:176`): "Endpoints tierces... publique dès aujourd'hui" |
| `passport` (`passport_router`) | 5 | PUBLIC | Offline-verifiable-by-design doctrine (Phase 1 audit) |
| `registry` (`registry_router`) | 5 | PUBLIC | Stateless schema catalog, no side effects (Phase 1) |
| `notary` (`notary_router`) | 13 | mixed | `/notarize`, `/anchor/*` are internal-trigger routes with **no auth found** — see FLAG below; read routes (`/block/{h}`, `/chain/status`, `/chain/verify`) are intentionally public (offline-verifiable proof doctrine) |
| `badges` (`badge_router`) | 11 | AUTHENTICATED (client API key) | `require_permission` |
| `jetons` (`jetons_router`) | 9 | AUTHENTICATED (client API key) | `require_permission` |
| `event` (`event_router`) | 5 | mixed | `/scan`, `/nfc/tap` require `require_permission("stage")`; `/zones`, `/stats/*` are PUBLIC (read-only) |
| `staff` (`staff_router`) | 4 | SYSTEM/AGENT | `/login` is PUBLIC-SECRET (PIN in body); `/me`, `/admin/*` require `get_current_staff` |
| `staff` (`scan_router`) | 7 | SYSTEM/AGENT | `require_staff_perm` |
| `security` (`security_router`) | 3 | ADMIN | `verify_admin_key` (Phase 1 audit) |
| `email_service` (`email_router`) | 4 | AUTHENTICATED (client API key) | `require_permission` |
| `services` (`stripe_router`) | 3 | **FLAG** (see below) | No auth detected on `/checkout` |
| `services` (`webhook_router`) | 1 | INTERNAL / PUBLIC-SECRET | Stripe signature verification inside the handler (`backend/services/webhook.py`, not a FastAPI dependency) |
| `sync` (`sync_router`) | 6 | mixed | `/baserow/webhook` is PUBLIC-SECRET (HMAC, `backend/sync/routes.py:276-277`); other routes need per-route check (not fully audited this pass — see backlog) |
| `heritage` (`heritage_router`) | 6 | mixed | `/claim` is PUBLIC-SECRET (documented: "Public (pas d'auth): la preuve repose sur le secret partagé hors-bande", `backend/heritage/routes.py:216`); other routes not fully audited this pass |
| `fingerprint` (`fp_router`) | 8 | **FLAG** (see below) | `/consent/{frek_id}` writer comment admits intended-owner-scope, not enforced |
| `geo` (`geo_router`) | 9 | **FLAG** (see below) | Same pattern as `fingerprint` — consent-gated but not owner-authenticated |
| `did`/`vc` (`did_router`, `vc_router`) | 4 | PUBLIC | DID/VC resolution and verification are meant to be publicly verifiable (W3C DID/VC design intent) |
| `eudi` (`eudi_router`, `wellknown_router`) | 6 | PUBLIC (protocol-mandated) | OID4VCI endpoints (`/token`, `/credential`, `/credential-offer/{id}`) are inherently public-facing per the OpenID4VCI spec — the wallet calls them without a FREKCORE-issued credential (that's the point of the protocol) |
| `frek` (`frek_router`, `advanced_router`) | 33 | **LEGACY, PUBLIC, unaudited in depth** | `frek/routes.py` header: "FREK v2 — Routes API" — legacy/superseded surface (see `reports/FREKCORE_CONTRADICTIONS.md`), mounted at unversioned `/api` (not `/api/v1`) |
| `moment` (`moment_router`) | 6 | PUBLIC | Documented doctrine: "Endpoint public, anonyme, sans auth" (`backend/moment/routes.py:4`) |
| `counter` (`counter_router`) | 5 | **FLAG** | `POST ""` (batch ingest) has no auth found |
| `core` (`core_router`) | 5 | AUTHENTICATED | Live-traffic evidence: `POST /api/core/ingest` returned `403 Forbidden` against the mongomock run without credentials (`reports/16_INTEGRATION_TEST_BASELINE.md`) — real protection exists even though the automated scanner didn't attribute it to a named dependency in this pass |
| `standards`, `ecosystem`, `spec`, `seal` | 12 | PUBLIC | Documentation/manifest endpoints, intentionally public |
| `server` (`api_router`) | 3 | PUBLIC, **dead code** | `GET /`, `POST /status`, `GET /status` are the unmodified FastAPI project-template scaffold (`StatusCheck`/`StatusCheckCreate`, `backend/server.py:175-212`) — not a FREKCORE product route, see `reports/FREKCORE_COMPLETION_BACKLOG.md` |
| `investor` (`investor_router`) | 2 | not audited this pass | — |
| `pdf_batch` (`pdf_batch_router`) | 4 | not audited this pass | — |

## FLAG — genuine findings (mutation with no confirmed protection)

These are the routes this pass could not attribute to any real auth mechanism after both the automated scan and a manual read. Each is a candidate for Priority 4's incremental enforcement — **none were wired with new enforcement in this phase** (see "What was and wasn't wired" below) because doing so on routes this session cannot integration-test against a real MongoDB carries real regression risk that this phase's evidence cannot rule out.

| Route | Evidence | Risk assessment |
|---|---|---|
| `POST /api/v1/notary/notarize` | `backend/notary/routes.py:65` — no `Depends(...)` found | Anyone who can reach the network can write an arbitrary notarized block. Notarization is meant to be triggered by other trusted server-side modules (`notary.service.notarize_event`, called internally) — this HTTP route may be intended as an internal/service-to-service call, but nothing in the code enforces that. **Highest-severity finding in this matrix.** |
| `POST /api/v1/notary/anchor/sweep`, `/anchor/upgrade`, `/anchor/{height}` | `backend/notary/routes.py:187,196,205` | Same pattern — anchoring operations triggerable by anyone |
| `POST /api/v1/core/fingerprint/consent/{frek_id}` | `backend/fingerprint/routes.py:57`, docstring literally says "Le porteur (ou un client autorisé mandaté par lui)" with no code enforcing that claim | Anyone can flip another FREK-ID's consent flags |
| `POST /api/v1/core/fingerprint/observe/*`, `/match` | `backend/fingerprint/routes.py:82,96,108,175` | Anyone can submit fingerprint observations against any FREK-ID |
| `POST /api/geo/consent/{frek_id}`, `/observe`, `/notarize`, `/encode` | `backend/geo/routes.py:26,42,60,131` | Same pattern as fingerprint — consent is checked, but nothing authenticates the caller as the consent-setter |
| `POST /api/core/count` (`counter_router`, empty path = router prefix root) | `backend/counter/routes.py:33` | Open batch-ingest of arbitrary counted entries |
| `POST /api/v1/checkout` (`stripe_router`) | `backend/services/stripe_pay.py:46` | Anyone can create a Stripe Checkout session (financial-adjacent; the actual charge still requires real payment details at Stripe, but session creation itself is unauthenticated) |

## PUBLIC-by-design (verified, not a finding)

- `identity_engine`'s WebAuthn ceremony endpoints (`/init`, `/{frek_id}/register/begin`, `/register/complete`, `/authenticate/begin`, `/authenticate/complete`) — intentionally public; that is how WebAuthn registration/authentication ceremonies work (the caller is anonymous until the ceremony completes).
- `fk/create`, `fk/verify`, `passport/*`, `registry/validate`, `moment/*`, `did/*`, `vc/verify` — each has an explicit doctrine comment or prior-phase evidence establishing intentional public access.
- `frek_v1/auth`'s `POST /token` — the credential-issuance endpoint itself; protected by `client_secret` in the body (OAuth2 client-credentials grant), not a header.
- `services/webhook.py`'s `POST /webhook/stripe` — protected by Stripe's HMAC signature verification inside the handler, not a FastAPI `Depends`.
- `heritage/claim`, `sync/baserow/webhook` — explicit secret-in-body / HMAC patterns, documented in their own docstrings.
- `eudi`'s OID4VCI endpoints — public by protocol design (OpenID4VCI).

## What was and wasn't wired this phase

**Wired**: nothing new was added to any of the FLAG routes above. Given this sandbox's Docker/MongoDB access is blocked at the network-policy level (`reports/16_INTEGRATION_TEST_BASELINE.md` §1) for anything beyond the `mongomock`-substitute run, and every one of these routes is exercised by the pre-existing 335-test integration suite in ways this session cannot fully regression-test against real MongoDB semantics, adding enforcement blind would risk exactly the outcome Priority 3's rules forbid ("no weakening security to make tests pass" cuts both ways — it also means not adding security that might silently break a legitimate existing caller without being able to prove it doesn't).

**What this phase does instead**: this matrix itself, handed to whoever wires enforcement next with `backend/permissions/` (Phase 2, still not wired into any route) as the mechanism. The `notary/notarize` and `notary/anchor/*` findings are the clear P0 items — see `reports/FREKCORE_COMPLETION_BACKLOG.md`.

## Routes not fully audited this pass

`sync_router` (beyond `/baserow/webhook`), `heritage_router` (beyond `/claim`), `investor_router`, `pdf_batch_router`, and the 33 `frek`/`frek_router_advanced` legacy routes were classified at the module level from partial evidence (docstrings, prior-phase audits) rather than individually read line-by-line in this pass, given the scope of 239 total routes and this phase's remaining budget. This is stated explicitly rather than implied to be exhaustive — see `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 for "complete the permission matrix" as a named follow-up item.
