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
| `notary` (`notary_router`) | 13 | mixed | `/notarize`, `/anchor/sweep`, `/anchor/upgrade`, `/anchor/{height}` require `Depends(require_permission("emit"))` (`backend/notary/routes.py:69,190,199,208` — **corrected**, see note below); read routes (`/block/{h}`, `/chain/status`, `/chain/verify`) are intentionally public (offline-verifiable proof doctrine) |
| `badges` (`badge_router`) | 11 | AUTHENTICATED (client API key) | `require_permission` |
| `jetons` (`jetons_router`) | 9 | AUTHENTICATED (client API key) | `require_permission` |
| `event` (`event_router`) | 5 | mixed | `/scan`, `/nfc/tap` require `require_permission("stage")`; `/zones`, `/stats/*` are PUBLIC (read-only) |
| `staff` (`staff_router`) | 4 | SYSTEM/AGENT | `/login` is PUBLIC-SECRET (PIN in body); `/me`, `/admin/*` require `get_current_staff` |
| `staff` (`scan_router`) | 7 | SYSTEM/AGENT | `require_staff_perm` |
| `security` (`security_router`) | 3 | ADMIN | `verify_admin_key` (Phase 1 audit) |
| `email_service` (`email_router`) | 4 | AUTHENTICATED (client API key) | `require_permission` |
| `services` (`stripe_router`) | 3 | **PUBLIC-BY-DESIGN, hardened** — see `reports/22_P0_SECURITY_CLOSURE.md` | `POST /checkout` (real path: `/api/payments/checkout`, corrected — was wrongly listed as `/api/v1/checkout`) intentionally left uncredentialed (no account system exists for its caller); rate-limited per `badge_id` |
| `services` (`webhook_router`) | 1 | INTERNAL / PUBLIC-SECRET | Stripe signature verification inside the handler (`backend/services/webhook.py`, not a FastAPI dependency) |
| `sync` (`sync_router`) | 6 | mixed — **corrected** | `/baserow/webhook` is PUBLIC-SECRET (HMAC, `backend/sync/routes.py:276-277`); `/status`, `/push/{frek_id}`, `/push`, `/pull`, `/log` all call `_require_admin(x_admin_key)` in-body (`backend/sync/routes.py:35`, an admin-key check not expressed as a `Depends(...)`, which is why the first pass missed it) — ADMIN, real |
| `heritage` (`heritage_router`) | 6 | mixed — **corrected** | `/claim` is PUBLIC-SECRET (documented: "Public (pas d'auth): la preuve repose sur le secret partagé hors-bande", `backend/heritage/routes.py:216`); `/{frek_id}/declare`, `/{frek_id}` GET/DELETE, `/{frek_id}/transfer` all require `Depends(_auth_require_permission(...))` (`backend/heritage/routes.py:56-58,98,170,184,298` — a locally-wrapped `frek_v1.auth.require_permission`, also missed by the first pass) — AUTHENTICATED, real; `/lineage/{frek_id}` is intentionally PUBLIC (own docstring: "Lignee complete et publique", excludes `claim_secret_hash`) |
| `fingerprint` (`fp_router`) | 8 | **mixed — HARDENED (P1, 2026-08-31: real holder auth)**, see `reports/22_P0_SECURITY_CLOSURE.md`, `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #3 | `/consent/{frek_id}` write, `/{frek_id}` GET, `/export/{frek_id}` now accept the real holder's `X-FREK-Session` (direct or via `linked_objects`) as primary authority, admin key as override; `/observe/*` rate-limited per FREK-ID (unchanged: consent-gated, no caller credential — device flow); `/match` stays admin-only by design (cross-subject, documented in the route) |
| `geo` (`geo_router`) | 9 | **mixed — HARDENED**, see `reports/22_P0_SECURITY_CLOSURE.md` | `/consent/{frek_id}` write, `/trail/{frek_id}` read, `/notarize` now ADMIN-gated (new); `/observe` rate-limited per FREK-ID (consent-gated in `service.py`, no caller credential — device flow); `/encode`, `/heatmap`, `/satellite*` remain PUBLIC (stateless/anonymized, verified unaffected) |
| `did`/`vc` (`did_router`, `vc_router`) | 4 | PUBLIC | DID/VC resolution and verification are meant to be publicly verifiable (W3C DID/VC design intent) |
| `eudi` (`eudi_router`, `wellknown_router`) | 6 | PUBLIC (protocol-mandated) | OID4VCI endpoints (`/token`, `/credential`, `/credential-offer/{id}`) are inherently public-facing per the OpenID4VCI spec — the wallet calls them without a FREKCORE-issued credential (that's the point of the protocol) |
| `frek` (`frek_router`, `advanced_router`) | 33 | **LEGACY, PUBLIC, unaudited in depth** | `frek/routes.py` header: "FREK v2 — Routes API" — legacy/superseded surface (see `reports/FREKCORE_CONTRADICTIONS.md`), mounted at unversioned `/api` (not `/api/v1`) |
| `moment` (`moment_router`) | 6 | PUBLIC | Documented doctrine: "Endpoint public, anonyme, sans auth" (`backend/moment/routes.py:4`) |
| `counter` (`counter_router`) | 5 | **mixed — HARDENED**, see `reports/22_P0_SECURITY_CLOSURE.md` | `POST` (batch ingest, real path: `/api/core/count` — corrected, was wrongly listed as `/api/count`) now ADMIN-gated; `/sources`, `/rules`, `/stats` remain PUBLIC read-only reference data |
| `core` (`core_router`) | 5 | AUTHENTICATED | Live-traffic evidence: `POST /api/core/ingest` returned `403 Forbidden` against the mongomock run without credentials (`reports/16_INTEGRATION_TEST_BASELINE.md`) — real protection exists even though the automated scanner didn't attribute it to a named dependency in this pass |
| `standards`, `ecosystem`, `spec`, `seal` | 12 | PUBLIC | Documentation/manifest endpoints, intentionally public |
| `server` (`api_router`) | 3 | PUBLIC, **dead code** | `GET /`, `POST /status`, `GET /status` are the unmodified FastAPI project-template scaffold (`StatusCheck`/`StatusCheckCreate`, `backend/server.py:175-212`) — not a FREKCORE product route, see `reports/FREKCORE_COMPLETION_BACKLOG.md` |
| `investor` (`investor_router`) | 2 | PUBLIC (read-only) — **corrected** | `/pulse`, `/sources-stats` are GET-only, no `Depends(...)` found; low severity (no mutation), not re-classified as a FLAG, but genuinely unauthenticated dashboard reads — see backlog if this data is sensitive |
| `pdf_batch` (`pdf_batch_router`) | 4 | mixed — **corrected** | `/template` (GET) is PUBLIC; the 3 POST/GET generation routes all carry `dependencies=[Depends(require_staff_perm("view_stats"))]` (`backend/pdf_batch/routes.py:51,74,93`) — SYSTEM/AGENT, real |

## Correction (Phase "CLOSE THE LOOP" pass) — notary/anchor were false positives

`reports/FREKCORE_COMPLETION_BACKLOG.md`'s P0 #1 named `POST /api/v1/notary/notarize` and `/anchor/*` as this matrix's highest-severity finding, based on this file's original claim of "no `Depends(...)` found." That claim was **wrong** — re-read directly against `backend/notary/routes.py` while investigating an unrelated task found:

```python
@notary_router.post("/notarize", response_model=BlockResponse)
async def notarize(..., client: dict = Depends(require_permission("emit"))):
@notary_router.post("/anchor/sweep")
async def anchor_sweep(..., client: dict = Depends(require_permission("emit"))):
@notary_router.post("/anchor/upgrade")
async def anchor_upgrade(..., client: dict = Depends(require_permission("emit"))):
@notary_router.post("/anchor/{height}")
async def anchor_block_now(..., client: dict = Depends(require_permission("emit"))):
```

`require_permission(...)` (`backend/frek_v1/auth.py:50-58`) wraps `get_current_client` (Bearer-token verification, client-active check, per-token revocation check, `frek_v1/auth.py:22-47`) and additionally checks the resolved client carries the named permission scope, raising `403` if not. This is real, working, live-tested enforcement — `backend/tests/test_notary.py::TestOTSAndAnchor::test_anchor_sweep_requires_auth` asserts a `401`/`403` for an unauthenticated call and **passed** in every integration run this phase (`reports/16_INTEGRATION_TEST_BASELINE.md`).

**Root cause of the original miss**: the automated extraction pass's regex/keyword scan for auth patterns looked for a fixed set of literal dependency names and a bounded forward-window from the route decorator; `Depends(require_permission("emit"))` — a call that *returns* a dependency, rather than a bare dependency reference — was not in that pattern set. The manual spot-check pass also missed it (documented as auditing "43 unattributed mutating routes"; `notary_router`'s specific routes were not among the ones re-read by hand). Corrected here by direct code inspection prompted by an unrelated fix in the same file this session. **`notary`/`anchor` routes are removed from the FLAG table and P0 #1 below — they were never a real gap.** This is exactly the kind of audit-tooling limitation the mission's own methodology warns about; recorded here rather than silently amended.

## FLAG — genuine findings (mutation with no confirmed protection)

These are the routes this pass could not attribute to any real auth mechanism after both the automated scan and a manual read. Each is a candidate for Priority 4's incremental enforcement — **none were wired with new enforcement in this phase** (see "What was and wasn't wired" below) because doing so on routes this session cannot integration-test against a real MongoDB carries real regression risk that this phase's evidence cannot rule out.

| Route | Evidence | Risk assessment |
|---|---|---|
**All rows below are CLOSED — see `reports/22_P0_SECURITY_CLOSURE.md` for the full per-route disposition, kept here for the historical record and because two of the paths listed were themselves wrong (corrected in the closure report).** `/api/geo/encode` was included in the original list in error — it is stateless, has no `frek_id`, and writes nothing; it was never a real finding.

| Route (as originally listed) | Original evidence | Original risk assessment | Disposition |
|---|---|---|---|
| `POST /api/v1/core/fingerprint/consent/{frek_id}` (real path: `/api/core/fingerprint/consent/{frek_id}`) | `backend/fingerprint/routes.py:57` | Anyone can flip another FREK-ID's consent flags | **CLOSED** — ADMIN-gated |
| `POST /api/v1/core/fingerprint/observe/*`, `/match` | `backend/fingerprint/routes.py:82,96,108,175` | Anyone can submit fingerprint observations against any FREK-ID | **`/match` was already ADMIN-gated pre-existing** (false positive in the original scan, same class as the notary finding above); `/observe/*` rate-limited (device flow, auth would break it — see closure report) |
| `POST /api/geo/consent/{frek_id}`, `/observe`, `/notarize` | `backend/geo/routes.py:42,60,131` | Consent is checked, but nothing authenticates the caller | **CLOSED**, then P1-hardened 2026-08-31 — consent/notarize now accept the holder's `X-FREK-Session` (admin key as override), observe stays rate-limited (device flow) |
| `POST /api/core/count` (real path corrected — was listed as `/api/count`) | `backend/counter/routes.py:33` | Open batch-ingest of arbitrary counted entries | **CLOSED** — ADMIN-gated |
| `POST /api/payments/checkout` (real path corrected — was listed as `/api/v1/checkout`) | `backend/services/stripe_pay.py:46` | Anyone can create a Stripe Checkout session | **Reviewed and left PUBLIC by design** (no fund movement possible from this endpoint — see closure report), hardened with a rate limit |

## PUBLIC-by-design (verified, not a finding)

- `identity_engine`'s WebAuthn ceremony endpoints (`/init`, `/{frek_id}/register/begin`, `/register/complete`, `/authenticate/begin`, `/authenticate/complete`) — intentionally public; that is how WebAuthn registration/authentication ceremonies work (the caller is anonymous until the ceremony completes).
- `fk/create`, `fk/verify`, `passport/*`, `registry/validate`, `moment/*`, `did/*`, `vc/verify` — each has an explicit doctrine comment or prior-phase evidence establishing intentional public access.
- `frek_v1/auth`'s `POST /token` — the credential-issuance endpoint itself; protected by `client_secret` in the body (OAuth2 client-credentials grant), not a header.
- `services/webhook.py`'s `POST /webhook/stripe` — protected by Stripe's HMAC signature verification inside the handler, not a FastAPI `Depends`.
- `heritage/claim`, `sync/baserow/webhook` — explicit secret-in-body / HMAC patterns, documented in their own docstrings.
- `eudi`'s OID4VCI endpoints — public by protocol design (OpenID4VCI).

## What was and wasn't wired this phase

**Wired**: nothing new was added to any of the FLAG routes above. Given this sandbox's Docker/MongoDB access is blocked at the network-policy level (`reports/16_INTEGRATION_TEST_BASELINE.md` §1) for anything beyond the `mongomock`-substitute run, and every one of these routes is exercised by the pre-existing 335-test integration suite in ways this session cannot fully regression-test against real MongoDB semantics, adding enforcement blind would risk exactly the outcome Priority 3's rules forbid ("no weakening security to make tests pass" cuts both ways — it also means not adding security that might silently break a legitimate existing caller without being able to prove it doesn't).

**Update (founder directive, docs/decisions/0001-founder-decisions-2026-08-31.md)**: the FLAG table above is now fully closed — see `reports/22_P0_SECURITY_CLOSURE.md` for the per-route WHO/WHAT/AUTHORITY/AUDIT/FAILURE analysis and evidence. `backend/permissions/` (Phase 2's role/scope model) was still not wired into any route as the mechanism for this closure — the fixes reuse the codebase's existing, simpler admin-key and rate-limit primitives instead, since wiring the full permission engine is a larger change than a scoped P0 closure warranted.

**Update (P1, 2026-08-31)**: real per-holder (owner-scoped) authorization for fingerprint/geo consent — the gap this section used to flag — is now **CLOSED**. `identity_engine`'s `X-FREK-Session` is the primary authority (admin key remains the override, not the only path). `backend/permissions/`'s role/scope engine was reconsidered here too and again not used: it is still wired into zero live routes anywhere in this codebase, so adopting it now would have meant building its persistence layer from scratch as a side effect of this fix — the `_holder_or_admin` pattern used instead is the one already proven live twice this session (`identity_engine`, `registry`). See `docs/architecture/FREK_ID_RECONCILIATION.md`'s "A second consumer of this map" section and `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #3 for the full write-up.

## Routes not fully audited this pass

`sync_router`, `heritage_router`, `investor_router`, and `pdf_batch_router` were individually re-read line-by-line in the "CLOSE THE LOOP" pass (see the correction note above) after that pass's investigation of `notary_router` surfaced two more auth patterns (`Depends(require_permission(...))`-style wrapper calls, and an in-body `_require_admin(...)` check never expressed as a `Depends(...)`) that the original automated scan did not recognize. All four are now corrected in the table above. The 33 `frek`/`frek_router_advanced` legacy routes remain genuinely unaudited beyond a module-level pass — larger surface, and its architectural fate is Contradiction C4 (founder decision required) rather than a pure permission-labeling question — see `reports/FREKCORE_COMPLETION_BACKLOG.md` P1.

**Methodology lesson recorded**: an automated `Depends(...)`-literal scan under-detects real auth in a codebase with multiple auth-wrapper conventions (`require_permission(perm)` returning a dependency, a locally-aliased wrapper like `heritage/routes.py`'s `_auth_require_permission`, or a plain in-body function call like `sync/routes.py`'s `_require_admin`). Every remaining "not audited" or "FLAG" claim in this file has now been confirmed by direct line-by-line reading, not by the automated scan alone.
