# FREKCORE Readiness Roadmap — State 9 -> State 10 -> Production Readiness -> Red/Blue/Purple -> CVLN

**Status: PLANNING ARTIFACT.** Sequences what the founder's own roadmap
message named. Nothing here is authorized to execute by this document —
each stage still needs its own explicit `STATE_TRANSITION_AUTHORIZATION`,
exactly as every prior state in this project has required.

## 0. Where things actually stand right now (evidence, not aspiration)

| Item | Status | Evidence |
|---|---|---|
| D1-D6 capabilities | IMPLEMENTED | `reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` |
| Historical Compatibility Reconciliation (STATE_6) | DONE | `docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md` |
| API/SDK Contract Stabilization (STATE_7) | DONE | `docs/architecture/FREKCORE_API_CONTRACT_V1.md` + 4 companions |
| Regression/Evidence/Migration Validation (STATE_8) | DONE | `docs/validation/FREKCORE_STATE8_VALIDATION_RESULTS.md` + 3 companions |
| `real-mongo-validation` CI job | BUILT, ran twice for real | See §2 below — currently `BLOCKED_NETWORK` at the TLS layer, not a code gap |
| `STATE_9_FINAL_HISTORICAL_ARCHITECTURAL_RECONCILIATION` | NOT STARTED | Founder's own next-named state; not authorized yet |
| `STATE_10` (freeze) | NOT STARTED | Not yet named/authorized |
| Production Readiness (formal) | NOT STARTED | This document's own companions are *preparation* for it, not the state itself |
| Red/Blue/Purple Team | NOT STARTED | Every prior authorization has explicitly prohibited it until now |
| CVLN ecosystem wiring | NOT STARTED | Explicitly prohibited in every prior authorization (`WIRE_CVLN=FALSE`) |

## 1. Sequencing (as the founder laid it out, confirmed consistent with this project's own established order)

```
STATE_9_FINAL_HISTORICAL_ARCHITECTURAL_RECONCILIATION
        |
        v
STATE_10 (freeze assessment)
        |
        v
PRODUCTION_READINESS (formal state -- infra actually stood up,
                       using docs/production_readiness/* as the checklist)
        |
        v
RED_TEAM / BLUE_TEAM / PURPLE_TEAM (adversarial validation of what's
                                     now actually running in production)
        |
        v
CVLN ecosystem wiring (KORA, Wallet, Academy, LabelOS, FREKANSLA,
                        CVLN Intelligence OS, Agent Factory, Laurentia,
                        Command Center, ...)
```

Each arrow is a founder decision point, not an automatic transition — this
matches `AUTO_TRANSITION=FALSE` as it has applied to every state so far.

## 2. Real MongoDB — current live status (this session)

Both real CI runs against the founder-supplied `MONGO_URI` (once correctly
configured as a repository secret) reached the actual connection attempt and
failed identically on all 3 Atlas shard hosts:

```
SSL handshake failed: ac-86nvg7r-shard-00-XX.4rawqdn.mongodb.net:27017:
[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
```

This is a **TLS-handshake-level rejection**, before authentication is ever
reached — not a credentials problem, not a plain unreachable-network
timeout. The most common real-world cause of exactly this signature against
Atlas is the cluster's **Network Access** (IP allowlist) configuration
rejecting the connecting IP at the TLS layer rather than with a clean
connection refusal. **FOUNDER-OPERATED next step**: in the Atlas project,
check Network Access -> IP Access List. If it's restricted to specific IPs
(e.g. the founder's home IP), GitHub Actions runners use dynamic,
unpredictable IP ranges and will never match a static allowlist — either
open the allowlist to `0.0.0.0/0` (acceptable for this project's non-secret
Atlas credentials model, since auth still gates access, exactly the
posture a public-internet-facing FREKCORE server will need anyway once the
Cloudflare Tunnel is live) or use Atlas's own GitHub Actions integration if
the tier supports dynamic allowlisting. Once resolved, no code change is
needed — the existing `real-mongo-validation` job and its 20 tests
(`backend/tests/test_real_mongo_validation.py`) re-run automatically on the
next push or manual rerun and will produce a real
`REAL_INFRA_VERIFIED`/`FAILED_SOFTWARE_VALIDATION` result instead of
`BLOCKED_NETWORK`.

This same resolved connection is also exactly what the self-hosted
FREKCORE server (once running behind the Cloudflare Tunnel, per
`FREKCORE_DEPLOYMENT_ARCHITECTURE.md`) will need — closing this one Atlas
configuration item unblocks both the CI validation and the real production
deployment simultaneously.

## 3. Real OTS / Bitcoin anchor

Unchanged since STATE_8: OTS calendar servers are unreachable from this
sandbox's own egress policy (`docs/validation/FREKCORE_STATE8_VALIDATION_
RESULTS.md` §6). Worth re-attempting from GitHub Actions the same way real
Mongo was — a GitHub-hosted runner should have ordinary internet access to
public OTS calendar servers (`alice.btc.calendar.opentimestamps.org` and
peers) even though this sandbox does not. Not attempted by this document;
a natural, small follow-up once real-Mongo validation is fully green
(same CI job pattern, different destination). Bitcoin anchor confirmation
remains downstream of that and of real wall-clock time — cannot be
short-circuited.

## 4. D1 scientific status

`D1_VERIFIED=PARTIAL` remains the honest, evidence-scoped status
(`reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`). Upgrading it requires new
scientific testing (lossy-compression robustness, re-recording robustness,
collision-rate measurement on a larger corpus) — explicitly not something
any prior state's software regression tests were permitted to use as
grounds for an upgrade, and this roadmap does not propose changing that
rule. This is a research/testing task, not an infrastructure task; it does
not block Production Readiness for the capabilities that don't depend on
D1's unproven robustness margins, but should be scoped and resourced
explicitly before any public claim about audio-fingerprint robustness is
made in a user-facing context.

## 5. Delegation runtime wiring

Sized concretely in `FREKCORE_SECRETS_KEYS_AUTH_PLAN.md` §3 — a small,
additive, one-route-at-a-time wiring task, not a redesign. Reasonable to
schedule as part of formal Production Readiness (it's exactly the kind of
"make what's already correct in isolation load-bearing" work that state is
for), not before.

## 6. UPS / power resilience

Sizing note for the founder: if `api.frekcore...` starts carrying real
traffic other systems depend on (i.e., once CVLN wiring begins), an
unplanned power loss on a single home PC becomes a real availability risk
in a way it isn't while FREKCORE is pre-launch. A UPS sized for a clean
shutdown (not necessarily hours of runtime — enough to let
`ExecStop`/Docker's own graceful-shutdown path run, which this codebase's
Mongo-backed durability model (§8 of the readiness plan) already tolerates
without corruption) is the proportionate answer, not an immediate
pre-launch blocker.

## 7. What this roadmap explicitly does NOT authorize

`EXECUTE_STATE_9=FALSE`, `EXECUTE_STATE_10=FALSE`, `PRODUCTION_READINESS=
FALSE` (as a formally-entered state — the planning documents in this
directory are preparation, not the state itself), `RED_TEAM=FALSE`,
`BLUE_TEAM=FALSE`, `PURPLE_TEAM=FALSE`, `WIRE_CVLN=FALSE`, `DEPLOY=FALSE`
(no real deployment was performed), `MERGE_PR=FALSE`. This document
recommends a sequence; it does not start it.
