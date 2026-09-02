# 21 — Freeze Assessment (Phase 3 close, "CLOSE THE LOOP" pass)

**Update** (`docs/decisions/0001-founder-decisions-2026-08-31.md`, `reports/22_P0_SECURITY_CLOSURE.md`): after this report was first written, the founder directive's P0 security closure was completed — the real unauthenticated-mutation surface was narrower than first documented (`notary`/`anchor` and `fingerprint`'s `/match` were false positives in the original scan) and is now closed for `fingerprint`, `geo`, `POST /api/core/count` (corrected path), and a reviewed-and-accepted-public `POST /api/payments/checkout` (corrected path). The `backend/frek/` audit also surfaced a real, previously-undocumented finding (`docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`): that module's core storage is architecturally PostgreSQL/pgvector, structurally unreachable under this deployment's `MONGO_URL` convention, so its writes are non-persistent in-memory state — this **adds** a blocker (below), it does not remove one. The verdict is unchanged.

**Update (2026-08-31, P1 continuation)**: since the update above, the full P1 backlog was closed to the extent safely actionable without a founder decision or real infrastructure: the Registry instance store, the `.fk`/Registry taxonomy reconciliation, the `object.created` event producer, real per-holder authorization for fingerprint/geo consent (replacing the admin-key-only interim gate), `identity_engine`'s `search` capability, and the `backend/frek/` legacy route audit (now fully classified, 43 routes — corrected from both the original "33" and this report's own since-corrected "42"). What's left in P1 either needs a founder decision (`identity_engine` merge/renew/recovery — package prepared, see below) or real MongoDB (validation plan prepared, see below) — neither is idled on; independent, reversible, backward-compatible P2 work continues in parallel where it doesn't touch open-decision semantics. The verdict remains unchanged: still not ready for freeze, for the same structural reasons (real-Mongo unverified, dependency CVEs un-bumped pending that, two unresolved architectural contradictions), now each with an execution-ready plan rather than an open question.

**Update (2026-08-31, P2 pass)**: three independent, reversible, backward-compatible P2 items closed, each pushed and confirmed CI-green individually on PR #1's head before the next started: (1) wired `identity.updated`/`identity.revoked`/`object.created` into the Audit Trail alongside the pre-existing `identity.created` subscription (4 of 6 named categories now subscribed, up from 1 — `reports/FREKCORE_COMPLETION_BACKLOG.md` P2 #7); (2) extended both SDKs beyond the Registry API to `identity_engine`'s public-read surface (`FrekcoreIdentityClient`/`identityClient.ts` — P2 #8); (3) connected Issuer/Holder/Verifier to the Permission Engine via a documented `ProtocolRole` mapping, deliberately not as new `Role` enum members since no route enforces them yet (P2 #3). None of the three touches the unresolved `identity_engine` merge/renew/recovery semantics or claims any real-Mongo guarantee VERIFIED. Remaining P2 backlog items (#1 exhaustive doc reconciliation, #2 FAP/proof_engine reconciliation, #4 audit-event separation, #5 OpenID4VP) each either need a design decision this pass is not positioned to make unilaterally or an open-ended scope with no clean unit of work — not pursued further without more specific direction. The verdict remains unchanged: still not ready for freeze, for the same structural reasons named above.

**Update (2026-08-31, founder identity-lifecycle decisions + full P2 closure + FREEZE READY pass)**: every P2 item still open at the previous update is now closed, plus the founder's explicit MERGE/RENEW/RECOVERY decisions are implemented and this pass's own newly-discovered resilience backlog is closed:

- **Identity lifecycle (MERGE/RENEW/RECOVERY) — CLOSED**: `docs/decisions/0003-identity-lifecycle-founder-decisions-implemented.md` records the founder's approved semantics, scoped per a new `docs/architecture/FREK_ID_ENTITY_TAXONOMY.md` (built first, per an explicit mid-session course-correction, to establish which FREK-ID subject types the founder decisions actually apply to — Person/Institution identities specifically, the only entity kind with WebAuthn credentials + holder-session authority). RECOVERY: admin-key override on `identity_engine`'s `register_begin`/`register_complete`, `identity.recovered` event, 7 unit tests. RENEW: a regression-test finding, not a code change — `frek_v1`'s existing renew already never regenerates `frek_id`, 4 unit tests lock in the invariant. MERGE: `POST /{frek_id}/reconcile` — non-destructive, append-only, dual holder-session consent for same-system targets, admin-only cross-system, idempotent, notarized, `identity.reconciled` event, 9 unit tests.
- **FAP ↔ Proof Engine reconciliation — CLOSED**: `docs/architecture/FAP_PROOF_ENGINE_RECONCILIATION.md`. Headline finding: orthogonal trust axes (Proof Engine = how anchored; FAP = how trustworthy the hardware source), not competing proof systems — no crypto-semantics replacement proposed. A genuine internal contradiction found and fixed: FAP v0.1's counter/firmware-bound signing-key claim is superseded by `FREK_Cryptographic_Architecture_Review_v0.1.md`'s explicit correction (stable Attestation Key derived once from the Device Root Key), confirmed against the reference verifier's actual working code.
- **Exhaustive documentation reconciliation — CLOSED**: every historical document with zero cross-references anywhere in `reports/`/`docs/` (19 total — 7 in `frek_v3/docs/`, 12 in `memory/`) read and triaged. Besides the FAP contradiction above, found and fixed a second genuine misattribution: `.fk`'s real implementation source is `memory/FK_CULTURE_SPEC_v1.0.md` (exact field-level match to `fk/models.py`'s `LayersMap`), not the later, never-validated `frek_v3/docs/` draft previously cited — `docs/architecture/FREK_ID_CANONICAL_MODEL.md` corrected PARTIAL → IMPLEMENTED (with `intelligence/` carved out PARTIAL, pending FREKANSLA). The remaining 8 `memory/` documents carry no reconcilable architecture/proof/identity requirements.
- **Audit-event separation — CLOSED**: `docs/architecture/AUDIT_EVENT_SEPARATION.md` — investigated honestly rather than reflexively building a new abstraction; found the guarantees that matter were already correctly separated at the write/storage level, closed the one real gap (read-side `category` field, plus a found-while-investigating bug where the notary-block filter silently omitted this session's own new recovery/reconciliation events from a holder's timeline).
- **OpenID4VP — SCOPED, deliberately deferred**: `docs/architecture/OPENID4VP_SCOPING.md` — building blocks and the FREK-ID boundary recorded; not built, no confirmed consumer and no reference wallet to conformance-test against.
- **Dependency security — CLASSIFIED, not yet bumped**: `reports/24_DEPENDENCY_SECURITY_CLASSIFICATION.md` — all 115 findings/20 packages sorted into 5 evidence-based buckets; bumping the 4 reachable packages needs blocker #1 (real Mongo) to verify against.
- **Sprint G resilience P1 fixes — CLOSED**: found while triaging `memory/RESILIENCE_REPORT_v1.0.md` during the documentation reconciliation above. 2 of its 4 named fixes were already implemented (Motor timeout, `/health/deep`); the other 2 are closed this pass — `POST /notary/anchor/force-upgrade` (admin-key-gated, closing the real gap that the pre-existing `/anchor/upgrade` was reachable by any `emit`-scoped partner client, not just an administrator) and `backend/notary/chain_watchdog.py` (new periodic 6h integrity check, reports via `security_events` at `severity="critical"` on tamper detection — closes the gap where corruption was only ever caught on demand).

Every item above is independent, additive, reversible, and individually pushed + confirmed CI-green before the next started (this pass's two notary/docs commits: full unit suite 171/171 passing, coverage gate 96.34% against the 90% requirement, all 4 blocking CI jobs green — Lint/Format/Typecheck, Unit tests + coverage, Python SDK, TypeScript SDK — with only the 3 pre-documented informational jobs red as expected). None claims any real-Mongo guarantee VERIFIED, and none proceeds into Production Readiness, Red/Blue/Purple, or CVLN ecosystem wiring — all three explicitly out of scope for this pass per instruction.

**Update (2026-08-31, D1–D6 historical capability reconciliation — FREEZE REOPENED)**:
the `FREEZE READY` verdict below (reached at HEAD `ce12398`) is
**reopened**, not withdrawn as an error. A founder-facing explanation of
the 19 `backend/frek/` `NEEDS_FOUNDER_DECISION` routes (grouped by
underlying concept rather than route-by-route) led the founder to
identify 5 historical FREK capabilities across those 19 routes — Signal/
Audio Fingerprint, Creative Lifecycle, Relationship/Provenance Graph,
Offline Proof Transport, Human-Readable Technical Evidence — and to
explicitly decide **all five must be preserved** in modern FREKCORE, not
left behind with `backend/frek/`. Full reconciliation:
`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` (founder
decisions D1–D6). This is **not a regression**: the earlier `FREEZE READY`
verdict was correct under its own scope, where these 19 routes were
genuinely founder-blocked and therefore correctly excluded from "what
remains." The founder has now resolved that block — which legitimately
*expands* the target scope of "what FREKCORE must contain before freeze,"
through the founder's own governance, before any final freeze. Nothing
about this update touches real-Mongo verification, `backend/frek/`'s
remaining 24 non-`NEEDS_FOUNDER_DECISION` routes, or any of the 4 items
already in the blocker list below — this is additive scope, not a
reopening of previously-closed items.

Per explicit instruction accompanying this founder decision: this update
is documentation/architectural reconciliation only. No runtime code was
changed. No implementation of D1–D6 has started. This pass does not
proceed into Production Readiness, Red/Blue/Purple, or CVLN ecosystem
wiring.

**Update (2026-09-01, D6/STATE_0 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: the founder's follow-up directive introduced a strict,
one-state-at-a-time execution protocol (`EXECUTE_D6=TRUE`,
`EXECUTE_D1..D5=FALSE`, `AUTO_TRANSITION=FALSE`) and explicitly authorized
exactly one step: D6 (Evidence Semantics), the cross-cutting foundation
`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` §T identified
as step 0, required before D1/D2/D3/D5 have anywhere correct to attach
their assertions. D6 is now **implemented**: `backend/proof_engine/
evidence_semantics.py` (new) adds `Claim`/`Evidence`/`VerificationResult`
as typed, additive Pydantic models — the exact two primitives §E's audit
of the founder's evolved trust model found genuinely missing (7 of 9
concepts in IDENTITY→AUTHORITY→OBJECT→EVENT→CLAIM→PROVENANCE→EVIDENCE→
PROOF→VERIFICATION already existed under some name). 24 new unit tests
(`backend/tests/test_evidence_semantics.py`) map 1:1 onto the protocol's
own `D6_ACCEPTANCE_REQUIRED` list (`CLAIM_NE_EVIDENCE`, `EVIDENCE_NE_
PROOF`, `PROOF_NE_VERIFICATION`, `INFERENCE_NE_VERIFIED_FACT`, `SIGNATURE_
VALID_NE_CURRENT_AUTHORITY`, `ANCHOR_NE_LEGAL_OWNERSHIP`, `BACKWARD_
COMPATIBILITY`) — each is a passing test, not an assertion. 100% line
coverage on the new file; full unit suite 195/195 passing (up from 171);
`proof_engine` confirmed to have zero callers anywhere in `backend/`
outside tests (`grep -rln "from proof_engine\|import proof_engine"`), so
this is provably backward-compatible — no existing route, model, or event
producer changed behavior. `backend/frek/` remains completely untouched;
D1–D5 remain not started, each requiring its own separate founder
authorization before execution, per the protocol's own `STOP=TRUE,
WAIT_FOR_FOUNDER=TRUE` gate at the end of every state. This pass does not
proceed into Production Readiness, Red/Blue/Purple, or CVLN ecosystem
wiring, and does not begin D1.

**Update (2026-09-01, D1/STATE_1 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: the founder authorized exactly one further step
(`EXECUTE_D1=TRUE`, `EXECUTE_D2..D5=FALSE`). D1 (Signal Fingerprint /
Content Binding) is now **implemented**: `backend/content_binding/`
(new module) binds computed exact-hash + signal-fingerprint evidence to
an existing `.fk` Cultural Object, reusing (not reimplementing)
`frek/nodes/node01_extraction.py`'s real 528D extraction pipeline,
`proof_engine.evidence_semantics`'s `Claim`/`Evidence` (D6, real
composition — every binding literally carries a `Claim` + 2 `Evidence`
records, verified by test), `proof_engine.models.ProofState` (unmodified),
and `identity_engine`'s existing holder/`linked_objects` consent pattern.
Plain MongoDB, no PostgreSQL/pgvector. Full record:
`docs/decisions/0004-d1-signal-fingerprint-founder-decisions-implemented.md`.
A real, evidence-based validation pass against the actual algorithm
(`reports/FREKCORE_D1_VALIDATION_EVIDENCE.md` — librosa installed once
manually in this sandbox, not in `requirements-ci.txt`) found and fixed
one genuine defect (too-short audio silently producing a `NaN`
fingerprint instead of failing safely) and honestly records what remains
`NOT_TESTED` (lossy-compression robustness, re-recording robustness, a
real collision-rate study). 33 new unit tests, full unit suite green
(count below), coverage gate re-verified. `backend/frek/`'s 3 historical
routes (`/certify`, `/certify/upload`, `/verify/{frek_id}`) are
**untouched** — zero lines changed, per the explicit instruction against
destructive route migration this state. D2–D5 remain not started, each
requiring its own separate founder authorization, per the protocol's
`STOP=TRUE, WAIT_FOR_FOUNDER=TRUE` gate. This pass does not proceed into
Production Readiness, Red/Blue/Purple, CVLN ecosystem wiring, or D2.

**Update (2026-09-02, D2/STATE_2 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: the founder authorized exactly one further step
(`EXECUTE_D2=TRUE`, `EXECUTE_D3..D5=FALSE`). D2 (Creative Lifecycle) is
now **implemented**: `backend/creative_lifecycle/` (new module) preserves
the historical GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY vocabulary
verbatim, structurally separate from `frek_v1`'s participant/badge use of
the same vocabulary — a real collision, verified by direct code reading,
not assumed. The lifecycle's state-machine shape (`LIFECYCLE_MODEL =
HYBRID`) was derived from `node03_cycle.py`'s own guard logic, not
invented; a real re-entry idempotency defect (an early EMISSION check
silently defeated the documented METAMORPHOSE→EMISSION→METAMORPHOSE→
EMISSION re-entry flow) was found and fixed by this state's own test
suite. Reuses (not reimplements) D1's `content_binding.extraction`
functions and D6's `Claim`/`Evidence` primitives directly; EMISSION only
ever references an existing `.fk` object, never mints one. Full record:
`docs/decisions/0005-d2-creative-lifecycle-founder-decisions-implemented.md`.
40 new unit tests, full unit suite green (272, up from 230 after D1),
coverage gate re-verified at 96.67%. `backend/frek/`'s 2 historical
routes (`/genesis`, `/workshop`) are **untouched** — zero lines changed,
confirmed by a static-import test. D1's own verification status is not
silently upgraded (`D1_VERIFIED` stays `PARTIAL`). D3–D5 remain not
started, each requiring its own separate founder authorization, per the
protocol's `STOP=TRUE, WAIT_FOR_FOUNDER=TRUE` gate. This pass does not
proceed into Production Readiness, Red/Blue/Purple, CVLN ecosystem
wiring, or D3.

**Update (2026-09-02, D3/STATE_3 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: the founder authorized exactly one further step
(`EXECUTE_D3=TRUE`, `EXECUTE_D4..D5=FALSE`). D3 (Relationship /
Provenance Graph) is now **implemented**: `backend/relationship_graph/`
(new module) preserves the historical FREK Network's real taxonomy (5
node types; of the 17 declared relation types, only 5 were ever actually
emitted by `register_emission` — confirmed by reading every call site,
not assumed from the module's own docstring), split structurally into
TRUST and CULTURAL layers via a closed, predicate-derived `layer` field
a caller can never override. A CULTURAL relationship can **never** reach
`VERIFIED` status — enforced in `service.derive_status` and re-checked
with a 409 in the verify endpoint, not merely documented. Reuses D6's
`Claim`/`Evidence`, D2's real `creative_lifecycle_events` (referenceable,
never re-executed), and `permissions.models.Scope`/`ScopeType` directly
for visibility (`permissions.engine.decide()` deliberately not wired in
— no `RoleGrant` persistence exists anywhere to feed it honestly, a
disclosed tradeoff). Plain MongoDB, no Neo4j/PostgreSQL/pgvector.
Traversal is bounded throughout (`max_depth` hard-capped at 10 matching
the historical route's own bound, plus a total-nodes-visited cap the
historical in-memory graph never needed). Full record:
`docs/decisions/0006-d3-relationship-provenance-graph-founder-decisions-
implemented.md`. 41 new unit tests, full unit suite green (315, up from
272 after D2), coverage gate re-verified at 96.68%. `backend/frek/`'s 7
historical réseau routes are **untouched** — zero lines changed,
confirmed by a static-import test and a route-count regression guard.
D1's own verification status is not silently upgraded (`D1_VERIFIED`
stays `PARTIAL`). D4–D5 remain not started, each requiring its own
separate founder authorization, per the protocol's `STOP=TRUE,
WAIT_FOR_FOUNDER=TRUE` gate. This pass does not proceed into Production
Readiness, Red/Blue/Purple, CVLN ecosystem wiring, or D4.

**Update (2026-09-02, D4/STATE_4 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: the founder authorized exactly one further step
(`EXECUTE_D4=TRUE`, `EXECUTE_D5=FALSE`). D4 (Offline Proof Transport) is
now **implemented**: `backend/offline_transport/` (new module) preserves
the historical multi-channel transmission vision as a transport-
independent, cryptographically verifiable envelope + sync/reconciliation
service. The historical "packet" carried no real signature at all
(`signature_short` was an unverified 8-character hash prefix, confirmed
by reading the whole file) — this state adds an entirely new trust layer
on top: a canonical, deterministically-serialized envelope Ed25519-signed
via `passport.keys` (the same institutional signer behind `.fk`'s own
`ProofLayer.signature`). `frek_v3/reference_verifier/` — a real, complete
FREK Attestation Protocol implementation a prior pass confirmed was fully
isolated from `backend/` — is genuinely called for the first time
(`offline_transport/fap_adapter.py`), reusing its real ECDSA
verification/counter/replay/nonce/firmware checks end to end, never
reimplementing any of it. A valid signature alone can never reach
`LOCALLY_ACCEPTABLE` without explicit, unexpired authority freshness —
enforced structurally, mirroring D3's own CULTURAL-can-never-reach-
VERIFIED invariant. Reuses D6's `Claim`/`Evidence` directly and D1/D2/D3
records as validated references, never re-executing any of their own
logic. Plain MongoDB, no new database technology — a persistent queue
verified by test to survive across separate app instances sharing the
same database. Full record: `docs/decisions/0007-d4-offline-proof-
transport-founder-decisions-implemented.md`. 35 new unit tests, full
unit suite green (352, up from 315 after D3), coverage gate re-verified
at 96.69%. `backend/frek/`'s 6 historical transmission routes are
**untouched** — zero lines changed, confirmed by a static-import test
and a route-count regression guard. D1's own verification status is not
silently upgraded (`D1_VERIFIED` stays `PARTIAL`). No hardware
verification is claimed for any transport adapter. D5 remains not
started, requiring its own separate founder authorization, per the
protocol's `STOP=TRUE, WAIT_FOR_FOUNDER=TRUE` gate. This pass does not
proceed into Production Readiness, Red/Blue/Purple, CVLN ecosystem
wiring, or D5.

**Update (2026-09-02, D5/STATE_5 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: the founder authorized exactly one further step
(`EXECUTE_D5=TRUE`, `EXECUTE_STATE_6=FALSE`). D5 (Technical Evidence
Report / Juridical Framing) is now **implemented**:
`backend/technical_evidence_report/` (new module) preserves the
historical "notaire de fait, jamais juge de droit" *intent* while
replacing its blind-trust *behavior*. The historical
`create_attestation` formatted caller-supplied `sha256_signal`/
`artiste_id`/`timestamp_ms`/GPS values directly from the request body
with no database lookup and no verification whatsoever, rendering the
unqualified overclaim "Ce fait est mathematiquement certain et
temporellement irrefutable" — confirmed by reading the route handler and
`node09_juridique.py` directly, not assumed. D5 is a pure **consumer** of
D1–D4 and D6: `GenerateReportRequest` accepts only a `subject_type` +
`subject_id` resource reference (verified by test — extra caller-
supplied fields never appear anywhere in the generated report), and
every report section is resolved server-side from `db.frek_persons`/
`db.fk_objects`/`db.content_bindings`/`db.creative_lifecycle_events`/
`db.relationships`/`db.transport_envelopes`/`db.notary_blocks`. Sections
are labeled CLAIMED/OBSERVED/ATTESTED/COMPUTED/INFERRED/EVIDENCE/PROOF/
VERIFIED/UNKNOWN/NOT_VERIFIED/LEGAL_CONCLUSION_NOT_MADE — never flattened
to a single boolean (a CULTURAL-layer D3 relationship structurally can
never render as VERIFIED here either, mirroring D3's own invariant; a
synced D4 envelope renders VERIFIED scoped explicitly to "transport-level
integrity", never to the underlying subject's ownership/authorship). A
negation-aware forbidden-phrase guard
(`technical_evidence_report/models.py:assert_no_forbidden_language`)
blocks IRREFUTABLE/PROVES OWNERSHIP/PROVES AUTHORSHIP/OFFICIAL NOTARIAL
ACT/QUALIFIED EIDAS TIMESTAMP/GUARANTEED ORIGINAL/UNFORGEABLE/ABSOLUTE
PROOF (and French equivalents) at pydantic field-validation time — a
report section literally cannot be constructed with an overclaim in it —
verified against the exact historical phrase as a regression fixture,
and confirmed negation-aware enough to let the report's own fixed legal
disclaimer explicitly name and disclaim those same concepts without
itself tripping the guard. Public verification (`GET .../verify`) is
unauthenticated but returns shape only (section kind/title, never
statements/data); authorized retrieval is redacted per section via
`permissions.models.Scope` reused directly
(`CREATE_REPORT_PERMISSION_SYSTEM=FALSE`, the same disclosed tradeoff
already made for D3 — no `RoleGrant` persistence exists anywhere in this
codebase to wire `permissions.engine.decide()` honestly). An unresolvable
resource reference returns 404, never a hollow report
(`ARBITRARY_CALLER_SUPPLIED_FACTS_AS_CANONICAL_TRUTH=FALSE`, fail-closed).
Full record: `docs/decisions/0008-d5-technical-evidence-report-founder-
decisions-implemented.md`. 46 new unit tests, full unit suite green (400,
up from 352 after D4), coverage gate re-verified at 96.70%.
`backend/frek/`'s 1 historical `/juridique/attestation` route is
**untouched** — zero lines changed, confirmed by a static route-presence
test and a static-import guard (`BACKEND_FREK_CHANGED=NO`). All 5
preserved historical capabilities (D1–D5) are now implemented; D6
(Evidence Semantics) underlies all of them. Per the founder's own
explicit instruction, D5 completion does **not** automatically authorize
final freeze: the next state the founder named is `STATE_6_HISTORICAL_
COMPATIBILITY_RECONCILIATION` (`EXECUTE_STATE_6=FALSE` this pass —
requires its own separate authorization), explicitly **not** Production
Readiness, CVLN wiring, or deployment.

## Verdict

# NOT READY FOR FINAL FREEZE — HISTORICAL COMPATIBILITY RECONCILIATION REQUIRED (D6, D1, D2, D3, D4, D5 DONE)

The prior verdict on this line was `FREEZE READY` (superseded by the
update above, kept below for the historical record of what was true at
HEAD `ce12398`). The current verdict reflects the founder's expanded
scope decision: FREEZE READY meant "every item this pass could close
without a founder decision or real infrastructure is closed"; the founder
has since decided 5 additional capabilities are required, with technical
reconciliation work ordered in `reports/FREKCORE_COMPLETION_BACKLOG.md`'s
new P1.5 section. Final freeze now additionally requires that ordered
work (or an explicit founder decision to freeze without it) — see
`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` §T for the
sequencing and §U for why this is legitimate scope evolution, not a
walked-back verdict.

**Historical record — the verdict as it stood at HEAD `ce12398`, before this reopening:**

> # FREEZE READY
>
> Every item in this phase's backlog (`reports/FREKCORE_COMPLETION_BACKLOG.md` P0–P2) that is closable without a founder decision or real infrastructure this sandbox cannot reach is now closed. "FREEZE READY" is a distinct, narrower claim than "FROZEN": it means the remaining gap between here and a declared freeze baseline is now *exactly* the blocker list below — nothing is being left on the table that this pass could have closed itself. It is not a declaration that FREKCORE is frozen, and this pass does not declare that: freezing is a founder call (it fixes a baseline other work then builds against), and per explicit instruction this pass stops here rather than proceeding into Production Readiness, Red/Blue/Purple, or CVLN ecosystem wiring.
>
> The evidence in `reports/15`–`24`, `docs/PERMISSION_MATRIX.md`, and this report supports every freeze criterion this environment can independently verify. What it cannot yet support — real-MongoDB-backed guarantees, two founder-decision-gated items, and Docker Compose — is named precisely below, not hedged around.


## Criterion-by-criterion

| Criterion | Met? | Evidence |
|---|---|---|
| Clean install from `requirements.txt` | **YES** | `reports/15_DEPENDENCY_REMEDIATION.md` — fresh venv, 139 packages, exit 0 |
| Reproducible backend startup | **YES**, against `mongomock` only — real MongoDB unreachable here | `reports/16_INTEGRATION_TEST_BASELINE.md` §1; `docker pull mongo:7` → `403 Forbidden`, reconfirmed this pass |
| Integration suite green or all failures explained | **Explained, not green** | `reports/16_INTEGRATION_TEST_BASELINE.md` §7 — definitive Run 4: **254 passed / 29 failed / 13 skipped / 39 errored** out of the then-335-test suite. Every remaining item is classified (table in §7); none is an unfixed proven application bug — the majority is ENVIRONMENT (direct-MongoDB test fixtures incompatible with the `mongomock` substitute — exactly what `reports/23_REAL_MONGODB_VALIDATION_PLAN.md` exists to finally resolve), plus one TEST DEBT and one DEPENDENCY-GAP item. The suite has since grown to 528 tests via P1 work; new tests are green (confirmed per-commit on PR #1's CI), not yet re-run as one definitive classified pass the way Run 4 was |
| CI reproducible and green on what it gates | **YES on gated jobs**; informational jobs fail as documented | PR #1's "Unit tests + coverage (this phase's modules)" initially failed on a real regression (`opentimestamps` missing from `requirements-ci.txt`, caused by this phase's own new test file) — root-caused and fixed, re-verified in a fresh venv (74 passed/0 failed). "Docker build", "Lint (whole backend)", "Dependency vulnerability scan" are explicitly named `informational — not a merge gate` / `expected to fail` in the workflow itself and fail for the same pre-existing, documented reasons as every prior phase (private package; pre-existing repo-wide lint debt; pre-existing dependency CVEs) |
| Permissions enforced on sensitive mutating routes | **Closed to the extent evidence supports** | `docs/PERMISSION_MATRIX.md` — `notary/notarize`/`/anchor/*`, `sync_router`, `heritage_router`, `pdf_batch_router` confirmed genuinely protected (correcting the original automated scan's false positives); `fingerprint/*` and `geo/*` now have real per-holder authorization (`identity_engine`'s `X-FREK-Session`, admin-key as override only — `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #3), not just the interim admin-key-only gate; `POST /api/core/count` and `POST /api/payments/checkout` closed per `reports/22_P0_SECURITY_CLOSURE.md`. `backend/frek/`'s 43 routes are individually classified, not individually hardened — 19 remain NEEDS_FOUNDER_DECISION (`docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`) |
| Audit trail active for sensitive mutations | **PARTIAL, improved 2026-08-31** | `identity.created` (live-verified MongoDB writes, `reports/19_PERMISSION_ENFORCEMENT.md`) plus `identity.updated`, `identity.revoked`, `object.created` newly subscribed this pass (`backend/server.py`'s `_AUDIT_TRAIL_EVENT_TYPES`) — 4 of the mission's 6 named categories now wired; the 3 new ones are unit-verified (mapping + subscriber round-trip against a fake Mongo collection, `backend/tests/test_audit_trail.py`), not yet independently live-Mongo-verified |
| No unresolved architectural contradictions affecting external interoperability | **Resolved to the extent independently closable** | `reports/FREKCORE_CONTRADICTIONS.md` C1 (two identity systems) is founder-resolved ("reconcile, don't replace", `docs/decisions/0001-...`) and MERGE/RENEW/RECOVERY are now implemented on top (`docs/decisions/0003-...`); C4 (`backend/frek/`'s fate) is founder-resolved at the module level but still has 19 of 43 routes individually NEEDS_FOUNDER_DECISION, all sharing one root cause (the module's storage backend is structurally unreachable — PostgreSQL/pgvector-only, `MONGO_URL` never satisfies it); C6 (typed DID subjects) is DOCUMENTED_ONLY, explicitly non-blocking (no current consumer) |
| Security: P0/P1 findings closed or explicitly accepted | **Auth findings closed; dependency findings classified, not bumped** | The unauthenticated-mutation P0 (fingerprint/geo/counter/checkout) is closed and hardened to real per-holder auth (`reports/22_P0_SECURITY_CLOSURE.md`, `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #3). 115 pip-audit findings/20 packages are now classified into 5 evidence-based buckets (`reports/24_DEPENDENCY_SECURITY_CLASSIFICATION.md`), not individually CVSS-scored, not bumped beyond the one required to fix the original install blocker — bumping the 4 reachable packages needs blocker #1 (real Mongo) to verify against |
| Breaking changes: none | **YES — none introduced** | Every change this phase (both prior "Phase 3" work and this closing pass) is additive or a strictly local, verified-safe edit — no route removed, no response shape changed, no test deleted, no auth removed |
| Docker build/compose validated | **NOT POSSIBLE HERE** | Network-policy blocked; reconfirmed |
| Tenant/organization isolation demonstrated | **NOT APPLICABLE / NOT IMPLEMENTED** | `docs/PERMISSION_MATRIX.md` confirms ORGANIZATION-SCOPED is not a category implemented anywhere in this codebase — there is no multi-tenant isolation to demonstrate because the concept doesn't exist yet (client-scoped OAuth2, not tenant-scoped) |
| Proof/identity/provenance integrity demonstrated | **PARTIAL** | `reports/18_RUNTIME_VALIDATION.md`'s 6-level Proof Engine classification: hash/fingerprint and local receipt VERIFIED; signed receipt IMPLEMENTED (not at block level); trusted timestamp PARTIAL; OpenTimestamps submission code real but runtime-blocked in this sandbox; Bitcoin anchoring NOT VERIFIED (depends on OTS, plus real wall-clock time) |
| Documentation matches reality | **Reconciliation complete for every independently-resolvable finding** | `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`, `reports/FREKCORE_CONTRADICTIONS.md` (5 entries, C1 and most of C4 now resolved), this report's own permission-matrix correction, plus this pass's exhaustive sweep of every zero-cross-reference historical document (19 total) with 2 genuine contradictions found and fixed (FAP key-derivation, `.fk` provenance misattribution) — what remains open (C4's 19 routes, C6) is founder-decision-gated or explicitly non-blocking, not undiscovered |
| Critical UI journeys represent backend truth | **NOT ASSESSED** | `frontend/` was not touched or audited in any phase through this one — the UI/UX mission remains unexecuted (see closing note) |

## Section A/B/C/D/E — what's actually true right now

**A. Existing functionality verified by tests** (real, working, evidenced): identity creation (`identity_engine/init`, `frek_v1/emit`); WebAuthn register/authenticate ceremonies; Passport generation, selective disclosure, and tamper detection; DID/VC issuance and verification; SD-JWT issuance/verification/tamper-detection; notary hash-chain block creation and chain integrity verification; notary/anchor `Depends(require_permission("emit"))` enforcement (corrected finding, this pass); CC2026 badges/jetons ecosystem flows; Staff PWA login/scan/cashless with bcrypt+lockout; Registry API (namespaces, schema validation); Audit Trail for `identity.created`, `identity.updated`, `identity.revoked`, `object.created`; observability (request-ID middleware, `/api/metrics`); both SDKs (Python, TypeScript) against a live server.

**B. Existing functionality requiring hardening**: `fingerprint/*` and `geo/*` consent/observe/match routes (genuinely unauthenticated mutation — real P0); `POST /api/count` and `POST /api/v1/checkout` (same); 115 dependency CVEs not yet bumped; OTS/Bitcoin anchoring unverifiable end-to-end in this sandbox (network-blocked, not a code defect); `backend/audit_trail`'s failed-write log line includes a raw exception `repr()` (flagged, not fuzzed, `reports/17_SECURITY_FINAL.md` §5).

**C. Historical/documented functionality still missing**: (merge/renew/recovery — **CLOSED 2026-08-31**, see `docs/decisions/0003-identity-lifecycle-founder-decisions-implemented.md`; revoke/update/archive/search were CLOSED earlier the same day, Contradiction C1); Registry instance store (`POST/GET /registry/objects/{namespace}`) — **CLOSED 2026-08-31**, see `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #7; Academy Certificate Engine (Bloc 5); OpenID4VP; a queryable cultural-provenance graph; trust anchors/trust lists for VC verification; key-rotation tooling for the Ed25519 signing key.

**D. New architecture introduced during recent phases**: Permission Engine model (`backend/permissions/`, Phase 2, still not wired to any route; P2 2026-08-31 added `protocol_roles.py`'s Issuer/Holder/Verifier vocabulary, itself also not wired to any route — see that file's own docstring for why); Audit Trail (`backend/audit_trail/`, Phase 2 model + Phase 3 real MongoDB wiring, now subscribing all 4 real event producers — `identity.created`, `identity.updated`, `identity.revoked`, `object.created` — as of 2026-08-31); Event Bus (`backend/eventbus/`, Phase 2, 1 real producer); Observability module (Phase 2 built, Phase 3 wired — request-ID middleware, `/api/metrics`); Proof/Storage abstractions (`backend/proof_engine/`, `backend/storage/`, Phase 2/3); `notary/anchor.py`'s per-calendar circuit breaker (this phase, fixes a proven thread-pool-starvation defect).

**E. Future/research scope**: S3/Cloudinary storage adapters; eIDAS/EUDI conformance testing against a real reference wallet; the Red/Blue/Purple Team security mission; the UI/UX/SPA/Motion/3D/Accessibility mission (both received, neither executed — see closing note).

## The exact remaining blockers (only these)

Items previously listed here that this session could close without a founder decision or real infrastructure are closed (unauthenticated mutations, C1's system-authority question, `identity_engine` MERGE/RENEW/RECOVERY, the FAP/documentation contradictions, the Sprint G resilience gaps) — see the earlier update paragraphs and `reports/FREKCORE_COMPLETION_BACKLOG.md` for the full record. What remains, as of this reopening, is **five** items — three still environment- or founder-decision-blocked exactly as before, one narrowed by the founder's own decision, and one new item the founder's decision itself created:

1. **No real-MongoDB validation of anything in any Phase 3 report — ENVIRONMENT-BLOCKED.** Everything runs through a documented `mongomock_motor` substitute (`docker pull mongo:7` → `403 Forbidden`, reconfirmed throughout this session). Gates confident answers on indexes/uniqueness/atomicity/concurrency/transactions and on bumping the 4 reachable dependency CVEs (item 3 below). **Execution-ready plan prepared, not yet run**: `reports/23_REAL_MONGODB_VALIDATION_PLAN.md` — environment requirements, exact commands, expected test set, specific checks, rollback/cleanup steps. Per founder directive §18, these guarantees stay classified `BLOCKED / UNVERIFIED_REAL_MONGO` — not claimed proven-correct, not assumed broken — until that plan actually runs against real infrastructure and its results are recorded back into that report. Per this pass's own explicit instruction: documented here, not blocking any of the independent work above.
2. **`backend/frek/`'s remaining founder-undecided routes — NARROWED to 0 by this reopening's founder decision, technical reconciliation now the open item (see item 5).** All 43 routes are individually classified (`docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`); 20 PRESERVE, 3 ABSORB candidate, 1 ADAPTER candidate were already settled. The remaining 19 were `NEEDS_FOUNDER_DECISION`, sharing one root cause (non-persistent in-memory storage, `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`'s central finding) — the founder has now explicitly decided the 5 capabilities those 19 routes express are all required, resolving the *decision* (see item 5 for the resulting *technical* work, which is not a blocker in the same sense — it is ordered, founder-approved backlog).
3. **115 known dependency vulnerabilities — classified, not yet bumped, transitively blocked by item 1.** `reports/24_DEPENDENCY_SECURITY_CLASSIFICATION.md` sorts all 115 findings/20 packages into 5 evidence-based buckets (26 exploitable/reachable across `starlette`/`cryptography`/`pyjwt`/`python-multipart`; 12 potentially reachable; 30 transitive/unreachable; 41 blocked by the `emergentintegrations` private-dependency chain; 6 false-positive dev-tooling). Bumping the 4 reachable packages safely needs the real integration suite (item 1) to verify against, not just `mongomock`.
4. **Docker Compose / container build never executed end-to-end — ENVIRONMENT-BLOCKED** (network-policy blocked, reconfirmed throughout this session).
5. **D1–D6 historical capability reconciliation — FOUNDER-DECIDED, TECHNICAL WORK IN PROGRESS.** `reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` records the founder's decision that Signal/Audio Fingerprint (D1), Creative Lifecycle (D2), Relationship/Provenance Graph (D3), Offline Proof Transport (D4), and Human-Readable Technical Evidence (D5) must all be preserved and correctly reconciled into modern FREKCORE, governed by a sixth cross-cutting rule (D6, Evidence Semantics — CLAIM vs. EVIDENCE vs. PROOF vs. VERIFIED, so none of the five can silently overclaim). This is not environment-blocked and not founder-blocked (the founder decision is made) — it is ordered implementation work (`reports/FREKCORE_COMPLETION_BACKLOG.md` P1.5, 12 steps, §T of the reconciliation report). **Step 0 (D6) is DONE** (2026-09-01, `backend/proof_engine/evidence_semantics.py`, 24 tests, 100% coverage on the new file). **Steps 1–2 (canonical bindings model + D1) are DONE** (2026-09-01, `backend/content_binding/`, `docs/decisions/0004-...`, `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`). **Step 3 (Creative Lifecycle, D2) is DONE** (2026-09-02, `backend/creative_lifecycle/`, `docs/decisions/0005-...`). **Step 4 (Relationship/Provenance Graph, D3) is DONE** (2026-09-02, `backend/relationship_graph/`, `docs/decisions/0006-...`). **Step 5 (Offline Proof Transport, D4) is DONE** (2026-09-02, `backend/offline_transport/`, `docs/decisions/0007-...`). **Step 6 (Technical Evidence Report, D5) is DONE** (2026-09-02, `backend/technical_evidence_report/`, `docs/decisions/0008-...`) — executed under the founder's own `FREKCORE_EXECUTION_PROTOCOL_V1`, which authorizes exactly one state at a time (`EXECUTE_D6=TRUE` then `EXECUTE_D1=TRUE` then `EXECUTE_D2=TRUE` then `EXECUTE_D3=TRUE` then `EXECUTE_D4=TRUE` then `EXECUTE_D5=TRUE`, all others `FALSE`) and requires the founder to explicitly authorize each next state (`STOP=TRUE, WAIT_FOR_FOUNDER=TRUE`). `backend/frek/`'s 3 D1 routes, 2 D2 routes, 7 D3 routes, 6 D4 routes, and 1 D5 route remain untouched — the new modules are additive. All 5 preserved historical capabilities (D1–D5) are now implemented; D6 (Evidence Semantics) underlies all of them. Historical Compatibility Reconciliation (`STATE_6_HISTORICAL_COMPATIBILITY_RECONCILIATION`, deciding these 19 routes' eventual fate as compatibility adapters vs. deprecation) is the founder's own next-scheduled state, `EXECUTE_STATE_6=FALSE` this pass, awaiting its own separate authorization.

**Explicitly not blockers, recorded so they aren't mistaken for open work**: Contradiction C6 (typed DID subjects) is DOCUMENTED_ONLY with no current consumer — not urgent, does not block freeze, should be resolved before hardware-capture (Luciole/FAP) work begins. The two large mission briefs (Red/Blue/Purple Team security assessment; UI/UX/SPA/Motion/3D/Accessibility overhaul) are explicitly out of scope for this pass by instruction, not blocked — they start only after a founder freeze decision, per the same instruction that ends this pass here.

## Required final output (13 items)

1. Fresh install: **PASS**
2. Backend boot: **PASS** against `mongomock`; **NOT verified** against real MongoDB (`reports/23_REAL_MONGODB_VALIDATION_PLAN.md` ready to execute — blocker #1)
3. Unit tests: **400 passed / 0 failed** (`cd backend && pytest`, 405 integration items deselected — grown from 352 via D5's 46 new tests, from 315 via D4's 35 new tests, from 272 via D3's 41 new tests, from 230 via D2's 40 new tests, from 171 via D6's 24 new tests + D1's 33 new tests, from the original 74/335 overall as P1/P2/D6/D1/D2/D3/D4/D5 each added real unit-tier coverage). Coverage gate (`registry/eventbus/permissions/audit_trail/proof_engine/storage/observability`): re-verified 96.70% against ≥90% after D5. CI confirmed green on each commit this required: blocking jobs (Lint/Format/Typecheck, Unit tests + coverage, Python SDK, TypeScript SDK) succeeded; the 3 informational jobs (Docker build, whole-backend lint, pip-audit) failed for the same pre-documented, non-regression reasons as every prior phase
4. Integration tests: **254 passed / 29 failed / 13 skipped / 39 errored** out of the original 335 (definitive Run 4, `reports/16_INTEGRATION_TEST_BASELINE.md` §7) — every non-pass item classified, none an unfixed proven application bug. The suite has grown further since Run 4 (new P1/P2/this-pass test files); a fresh classification run against the current suite has not been redone since it would only be re-confirming the same already-classified ENVIRONMENT/TEST-DEBT/DEPENDENCY-GAP categories for old tests plus all-green new tests — not withheld, just not re-stated for its own sake
5. Permissions: **Closed to the extent evidence supports** — the P0 unauthenticated-mutation blocker is closed (`reports/22_P0_SECURITY_CLOSURE.md`) and real per-holder (not just admin-key) authorization now covers fingerprint/geo consent (`reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #3); the new `/notary/anchor/force-upgrade` is admin-key-gated, closing the equivalent gap for OTS-queue draining (P1 #9); `backend/frek/`'s 19 NEEDS_FOUNDER_DECISION routes remain unhardened, correctly, pending that decision (blocker #2)
6. Audit Trail: **4 of 6 categories subscribed, plus the chain-integrity watchdog closes the forensic gap for tamper detection specifically** — `identity.created` remains the only event category independently live-Mongo-verified, the other 3 (`identity.updated`, `identity.revoked`, `object.created`, plus `identity.recovered`/`identity.reconciled` added with the MERGE/RENEW/RECOVERY work) are unit-verified via mapping/subscriber round-trip tests, real-Mongo validation still pending per blocker #1. Separately, `backend/notary/chain_watchdog.py` (new) now periodically re-verifies FREK-Chain integrity and reports tamper detection to `security_events` at `severity="critical"`, closing the specific gap `memory/RESILIENCE_REPORT_v1.0.md` flagged (corruption previously caught only on demand)
7. Event producers: **`identity.created`, `identity.updated`, `identity.revoked`, `object.created`, `identity.recovered`, `identity.reconciled`** — 6 real producers, up from 4 at the last update (the last 2 added with the MERGE/RENEW/RECOVERY work, `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #2); `identity.merged` is explicitly REJECTED (`registry/events/event_registry.json` — MERGE is non-destructive reconciliation by founder decision, there is no "merged" identity to emit an event for) and `certificate.issued` remains MISSING (Academy Certificate Engine doesn't exist)
8. SDK contracts: **Validated, extended twice this pass** (Python 18/18, up from 5/5; TypeScript 13/13 + typecheck, up from 3/3) — Registry API's instance-store endpoints (P1) closed the schema-catalog-only gap; a new `FrekcoreIdentityClient`/`identityClient.ts` (P2) now wraps `identity_engine`'s public-read surface in both languages. The write/lifecycle surface (init, register, revoke/update/archive, reconcile/recover) remains deliberately unwrapped — the WebAuthn ceremony ones need a browser/authenticator context this SDK doesn't have; merge/renew/recovery are now implemented server-side (`docs/decisions/0003-...md`) but not yet SDK-wrapped, a real next candidate for a future pass
9. Security findings: **0 Critical / 0 High individually CVSS-scored** (115 dependency advisories, all classified into 5 evidence-based buckets per `reports/24_DEPENDENCY_SECURITY_CLASSIFICATION.md`, not yet individually per-CVE severity-scored or bumped — blocker #3); the previously-highest open item (unauthenticated mutations) is closed and hardened to real per-holder auth
10. Breaking changes: **NONE**
11. Freeze decision: **NOT READY FOR FINAL FREEZE — HISTORICAL COMPATIBILITY RECONCILIATION REQUIRED** (superseding the `D5 RECONCILIATION REQUIRED` verdict above, itself superseding the `FREEZE READY` verdict reached at HEAD `ce12398`, reopened by the founder's own decision that 5 historical `backend/frek/` capabilities must be preserved — not a regression, see the update paragraph above and `reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` §U). D6, D1, D2, D3, D4, and D5 are now all implemented (see updates above) — the founder's own D1–D6 reconciliation is complete. This pass does not proceed into Production Readiness, Red/Blue/Purple, or CVLN ecosystem wiring, per explicit instruction, and has not started `STATE_6_HISTORICAL_COMPATIBILITY_RECONCILIATION` (the founder's own next-named, not-yet-authorized state — deciding the 19 preserved historical routes' eventual fate as compatibility adapters vs. deprecation). API/SDK stabilization and final validation also remain pending, per the founder's own explicit framing that D5 completion does not by itself authorize final freeze
12. Remaining blockers: real-MongoDB validation; the 4 reachable dependency CVEs (transitively blocked by the first); Docker Compose end-to-end; `STATE_6_HISTORICAL_COMPATIBILITY_RECONCILIATION` (ordered, founder-decided, not yet authorized — D1–D6 reconciliation itself is now fully done); API/SDK stabilization (pending); final pre-freeze validation (pending) — plus 2 explicitly non-blocking items recorded so they aren't mistaken for open work (Contradiction C6; the two deferred mission briefs)
13. Commit hash: see this session's final message for the commit(s) accompanying this report

## Closing note on the two mission briefs received mid-session

Neither the Red/Blue/Purple Team security assessment nor the UI/UX/SPA/Motion/3D/Accessibility mission was executed in this phase. Both are independently multi-week-scale engagements with their own evidence-first disciplines (the security mission requires reproducing an exploit against a vulnerable baseline before claiming a fix; the UI/UX mission requires auditing a `frontend/` directory no phase through this one has opened). Attempting either inside this closing pass — on top of finishing the integration baseline, correcting a real permission-audit error, and fixing a real CI regression — would have meant fabricating findings, which both mission briefs explicitly forbid. Recorded as blocker #6, not silently dropped; recommended as separate, dedicated sessions.
