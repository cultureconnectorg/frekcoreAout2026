# 22 — P0 Security Closure (founder directive §14–15)

Per-mutation analysis and disposition for the four route groups named as P0 in `reports/21_FREEZE_ASSESSMENT.md` prior to this pass: `fingerprint/*`, `geo/*`, `POST /api/count`, `POST /api/v1/checkout`. Two of those four paths were themselves wrong (corrected below, with evidence — `docs/PERMISSION_MATRIX.md` is updated to match).

**Path corrections found while doing this pass** (verified against `server.py`'s actual `include_router(...)` calls, not assumed):
- Counter batch ingest is `POST /api/core/count`, not `POST /api/count`.
- Stripe checkout is `POST /api/payments/checkout`, not `POST /api/v1/checkout`.

## Methodology

Per §14: for every mutation, determined WHO IS AUTHORIZED / WHAT RESOURCE / WHAT ACTION / UNDER WHAT AUTHORITY / WHAT AUDIT EVENT / WHAT FAILURE BEHAVIOR — by reading each route's full handler and its service-layer callee, not assuming a uniform fix. Per §14's explicit instruction not to apply generic authentication blindly: two different remediations were used depending on who legitimately calls each route.

- **ADMIN-key gate** (`X-Admin-Key` == `SECRET_KEY`, matching the pattern `fingerprint/routes.py` already used for its own `GET /{frek_id}`, `POST /match`, `GET /export/{frek_id}`): applied to low-frequency, high-stakes mutations with no real end-user-device caller — consent *writes*, the geo trail read, geo notarization, and the counter batch ingest (called by partner backend systems, not browsers/devices).
- **Rate limiting instead of auth** (`security/policies.py:check_rate_limit`, new `DEFAULT_LIMITS` entries `fingerprint_observe`, `geo_observe`, `checkout_create`): applied where the real caller is an end-user's own device/browser (fingerprint/geo `/observe/*`) or a participant with no account system at all (Stripe checkout) — authenticating these would break the actual product, per §14/§15's explicit instruction not to do that. Consent-gating (already present) remains the real protection against silent data collection; the rate limit bounds abuse volume once consent is granted.

## Per-route disposition

| Route | Real caller | Resource | Action | Authority applied | Audit/failure behavior | Regression test |
|---|---|---|---|---|---|---|
| `POST /api/core/fingerprint/consent/{frek_id}` | Was: anyone. Should be: holder or mandated client (no such mechanism exists yet — Contradiction C1) | A FREK-ID's tracking-layer consent flags | Write | **ADMIN** (interim) | 403 on missing/wrong key, no state change (verified) | `tests/test_fingerprint.py::TestConsentWriteAuth` (new, 3 tests) |
| `POST /api/core/fingerprint/observe/device`, `/observe/nfc`, `/observe/web-verify` | End-user's own device/browser | Behavioral signal for one FREK-ID | Write | Unchanged: **consent-gated, no caller credential** (device flow, changing this would break it) — **hardened**: rate-limited per FREK-ID | 429 past 120/hour per FREK-ID; unchanged `consent_required` refusal below that | `tests/test_fingerprint.py` (existing suite re-verified passing; rate limit not separately load-tested — see note) |
| `POST /api/geo/consent/{frek_id}` | Same as fingerprint's consent write | Geo consent level | Write | **ADMIN** (interim) | 403 on missing/wrong key | `tests/test_geo_security.py::TestConsentWriteAuth` (new) |
| `POST /api/geo/observe` | End-user's own device | Raw lat/lon for one FREK-ID | Write | Unchanged: consent-gated (in `service.observe()`), no caller credential — **hardened**: rate-limited per FREK-ID | 429 past 120/hour; unchanged `consent_required` refusal | `tests/test_geo_security.py::TestObserveConsentGate` (new) |
| `GET /api/geo/trail/{frek_id}` | Was: anyone. Full raw location history — materially more sensitive than a consent-level read | A FREK-ID's location history | Read | **ADMIN** (new — this read was not previously gated at all) | 403 on missing/wrong key | `tests/test_geo_security.py::TestTrailReadAuth` (new) |
| `POST /api/geo/notarize` | Rare, high-stakes (writes a permanent FREK-Chain block + attempts Bitcoin OTS) | Geo-anchored notarization | Write | **ADMIN** (new) | 403 on missing/wrong key | `tests/test_geo_security.py::TestNotarizeAuth` (new) |
| `POST /api/core/count` | Partner backend systems (9 named `CVLN_SOURCES`), not end-user devices | Batch of counted events attributed to a source | Write | **ADMIN** (interim; per-source API keys would be the precise fix — no existing per-source credential store found to build on) | 403 on missing/wrong key | `tests/test_counter_security.py::TestCountBatchAuth` (new) |
| `POST /api/payments/checkout` | CC2026 participant at a kiosk/web app — no account/session system exists for this caller at all | Stripe Checkout session + a pending `payment_transactions` row | Write (no fund movement — see below) | **PUBLIC, by design, documented in-route** — authenticating would break the only real caller | Hardened: rate-limited per `badge_id` (20/hour); unchanged 400/404 validation | `tests/test_checkout_security.py` (new, includes a live rate-limit-threshold test) |
| `GET /api/geo/{consent,heatmap,satellite*}`, `POST /api/geo/encode`, `GET /api/core/count/{sources,rules,stats}` | Public dashboards / stateless utilities / already-anonymized aggregates | — | Read or stateless compute | **PUBLIC, unchanged** — verified these were not accidentally locked down by this pass | — | `tests/test_geo_security.py::TestPublicByDesignRoutesUnaffected`, `tests/test_counter_security.py::TestReadRoutesRemainPublic` |

## Why checkout's real risk is lower than the original FLAG framing implied

`docs/PERMISSION_MATRIX.md`'s original entry read "Anyone can create a Stripe Checkout session (financial-adjacent...)". Reading `get_checkout_status()` in full shows jetons are only ever credited after Stripe itself reports `payment_status == "paid"` — creating a session for someone else's `badge_id` cannot move funds or credit jetons; it can only create a pending, unpaid `payment_transactions` row and an unused Stripe session (which Stripe expires on its own). The real residual risk is `badge_id`'s low entropy (`badges/nomenclature.py:generate_badge_id` — 4 random alphanumeric characters + a predictable trailing digit, ≈1.6M keyspace per badge type) enabling enumeration/pollution, not fund theft. Rate-limiting is a proportionate response to that actual risk; requiring a login this feature was never designed to need would not be.

## What is still open (not closed by this pass, and why)

- **True per-holder ("porteur") consent authorization** — **CLOSED 2026-08-31**, see `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #3 and `docs/architecture/FREK_ID_RECONCILIATION.md`. `identity_engine`'s `X-FREK-Session` (direct match, or via its pre-existing `linked_objects` mechanism for `frek_v1`-space `frek_id`s) is now the primary authority for fingerprint's `consent`/`{frek_id}`/`export` and geo's `consent`/`trail`/`notarize`; the ADMIN-key gate documented below remains only as the override.
- **Per-source credentials for `POST /api/core/count`** (rather than one shared admin key for all 9 `CVLN_SOURCES`) — same reasoning: no existing per-source credential store to build on; the shared-key interim gate closes the real anonymous-write hole today.
- **Rate-limit thresholds were not load-tested at true production volume** — the new `DEFAULT_LIMITS` values (120/hour for observe endpoints, 20/hour for checkout) are reasoned defaults, not empirically tuned; each is env-var-overridable (`FREK_RATE_FP_OBSERVE_PER_HOUR`, `FREK_RATE_GEO_OBSERVE_PER_HOUR`, `FREK_RATE_CHECKOUT_PER_HOUR`) for exactly that reason.
- **The `backend/frek/` (33 legacy routes) security review** required by §15 is covered separately in `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`, not folded into this report.

## Evidence

All new/changed code verified: `python3 -m pytest -q` → 74 passed / 0 failed (local unit tier, unaffected); a live `mongomock`-backed server run of every new and modified integration test in this closure (`test_fingerprint.py`, `test_geo_security.py`, `test_counter_security.py`, `test_checkout_security.py`) → 37 passed, 2 failed — both failures are the pre-existing, already-documented `mongo` direct-fixture ENVIRONMENT limitation (`reports/16_INTEGRATION_TEST_BASELINE.md` §7's classification table), not a regression from this change. flake8/mypy diff-checked clean against each file's pre-existing baseline (no new findings introduced).
