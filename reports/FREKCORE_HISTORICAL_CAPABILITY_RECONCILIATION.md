# FREKCORE — Historical Capability Reconciliation (D1–D6)

**Status**: All of D1–D6 are IMPLEMENTED, Historical Compatibility
Reconciliation (STATE_6) is DONE, API/SDK Contract Stabilization
(STATE_7) is DONE, and Regression/Evidence/Migration Validation (STATE_8)
is DONE. D6 (Evidence Semantics), D1 (Signal Fingerprint /
Content Binding), D2 (Creative Lifecycle), D3 (Relationship / Provenance
Graph), D4 (Offline Proof Transport), and D5 (Technical Evidence Report /
Juridical Framing) — see the 2026-09-01/2026-09-03 updates below —
(`backend/proof_engine/evidence_semantics.py`,
`backend/content_binding/`, `backend/creative_lifecycle/`,
`backend/relationship_graph/`, `backend/offline_transport/`,
`backend/technical_evidence_report/`). `backend/frek/` was additively
built alongside throughout D1–D5 (untouched by those 5 states), hardened
in place in STATE_6 (rate limiting, audit visibility, additive canonical
cross-references, one wording fix — never destructively rewritten), and
left untouched again in STATE_7 (a contracts/documentation/SDK state, see
`docs/architecture/FREKCORE_API_CONTRACT_V1.md` and its 4 companion
documents) and once more in STATE_8 (a validation state — `git diff
--stat -- backend/frek/` confirmed empty; see `docs/validation/
FREKCORE_STATE8_VALIDATION_RESULTS.md` and its 3 companion documents).
STATE_8 completion does **not** by itself authorize final freeze: the
founder's own next-named state is `STATE_9_FINAL_HISTORICAL_
ARCHITECTURAL_RECONCILIATION`, not yet authorized. PR #1 not merged, not
deployed.

**Founder decision this document records**: the 19 `backend/frek/` routes
classified `NEEDS_FOUNDER_DECISION` in `docs/architecture/
FREK_LEGACY_ROUTE_AUDIT.md` map to exactly **5 historical FREK
capabilities**, none of which the founder authorizes for deletion. All
five **survive** — they are not preserved as their current implementation
(in-memory, unauthenticated, unpersisted), but as concepts that must find
a correct, reconciled place in modern FREKCORE. This document is the
per-capability and per-route reconciliation required before any of the
five is actually built.

**Baseline**: HEAD `ce12398`, branch `claude/frekcore-v1-production-b9h2q0`,
PR #1 unmerged. Previous verdict `FREEZE READY` (`reports/
21_FREEZE_ASSESSMENT.md`) is reopened by this founder decision — see
§T and the updated freeze report for why this is scope expansion by
legitimate founder governance, not a regression.

**Update (2026-09-01, D6/STATE_0 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: per the founder's strict, one-state-at-a-time execution
protocol (`EXECUTE_D6=TRUE`, `EXECUTE_D1..D5=FALSE`), D6 — Evidence
Semantics — is no longer documentation-only. §T step 0's plan ("CLAIM/
EVIDENCE as first-class concepts... must exist before D1/D2/D3/D5 have
anywhere correct to attach their assertions") is implemented:
`backend/proof_engine/evidence_semantics.py` (new, 6 exported symbols:
`Claim`, `ClaimOrigin`, `Evidence`, `EvidenceKind`, `AuthorityStatus`,
`VerificationResult`), 24 new unit tests in `backend/tests/
test_evidence_semantics.py` mapping 1:1 to the protocol's
`D6_ACCEPTANCE_REQUIRED` list, 100% line coverage on the new file, full
unit suite 195/195 passing (was 171), zero existing route/model/behavior
changed (`proof_engine` has no caller anywhere in `backend/` outside
tests — confirmed by grep — so this is provably backward-compatible).
D1–D5 remain exactly as this document left them: reconciled on paper,
**not started** — `backend/frek/` is untouched, no route anywhere
changed. Per the protocol, this document now stops and waits for the
founder to authorize STATE_1 (D1) before any further execution.

**Update (2026-09-01, D1/STATE_1 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: per `EXECUTE_D1=TRUE, EXECUTE_D2..D5=FALSE`, D1 — Signal
Fingerprint / Content Binding — is now IMPLEMENTED, not just reconciled.
`docs/decisions/0004-d1-signal-fingerprint-founder-decisions-implemented.md`
is the full record. In brief: `backend/content_binding/` (new module)
binds computed exact-hash + signal-fingerprint evidence to an existing
`.fk` Cultural Object, never minting an identifier of its own — the
structural fix for `FREK_ID_EQUALS_SIGNAL_FINGERPRINT=FALSE`. Reuses,
rather than reimplements: `frek/nodes/node01_extraction.py`'s real
528D extraction pipeline (verbatim), `proof_engine.evidence_semantics`'s
`Claim`/`Evidence` (D6, built the prior state — every binding is
literally composed of a real `Claim` + two real `Evidence` records, not
a lookalike type), `proof_engine.models.ProofState` (unmodified),
`identity_engine`'s existing holder/`linked_objects` consent pattern, and
plain MongoDB (no PostgreSQL/pgvector — these 3 routes never need
similarity search). 33 new unit tests (`test_content_binding_unit.py`,
`test_content_binding_extraction_unit.py`), full unit suite green (see
§U for the exact count), coverage gate re-verified. A real, evidence-
based validation pass (`reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`,
librosa installed once manually in this sandbox — not in
requirements-ci.txt) found and fixed one genuine defect (too-short audio
silently producing a `NaN` fingerprint) and honestly records what is and
is not demonstrated about the algorithm's robustness (compression/
re-recording/collision-rate all stay `NOT_TESTED`). `backend/frek/`'s
own 3 historical routes (`/certify`, `/certify/upload`, `/verify/
{frek_id}`) are **untouched** — zero lines changed, per the explicit
instruction against destructive route migration this state. D2–D5 remain
exactly as before: reconciled on paper, not started. Per the protocol,
this document now stops and waits for the founder to authorize STATE_2
(D2) before any further execution.

**Update (2026-09-02, D2/STATE_2 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: per `EXECUTE_D2=TRUE, EXECUTE_D3..D5=FALSE`, D2 — Creative
Lifecycle — is now IMPLEMENTED, not just reconciled.
`docs/decisions/0005-d2-creative-lifecycle-founder-decisions-implemented.md`
is the full record. In brief: `backend/creative_lifecycle/` (new module)
preserves the historical GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY
vocabulary verbatim, structurally separate from `frek_v1`'s
participant/badge stage lifecycle (own collection, own notarization
`payload_type`, own authority model — the collision was verified by direct
code reading this state, not assumed). The lifecycle's state-machine shape
was derived from `node03_cycle.py`'s own guard logic, not invented:
`LIFECYCLE_MODEL = HYBRID` — WORKSHOP repeatable-but-bounded, METAMORPHOSE
unguarded, EMISSION strictly current-stage-gated, which together allow a
real, supported METAMORPHOSE → EMISSION → METAMORPHOSE → EMISSION
re-entry. A defect in this exact re-entry flow was found and fixed by this
state's own test suite (an early EMISSION idempotency check silently
defeated legitimate re-entry by scanning the full event history instead of
the current position — see the ADR). Reuses, rather than reimplements:
D1's `content_binding.extraction` functions for exact-hash/signal-
fingerprint computation (`D2_CONSUMES_D1=TRUE`, confirmed structurally, not
just claimed), D6's `Claim`/`Evidence` primitives (every lifecycle event is
literally composed of them), `identity_engine`'s holder-session pattern,
and plain MongoDB (`db.creative_lifecycle_events`, no PostgreSQL/pgvector
— D2 never needs similarity search). EMISSION requires and only ever
references an existing `.fk` Cultural Object — this module never mints a
FREK Object identity itself. 40 new unit tests
(`test_creative_lifecycle_unit.py`), full unit suite green (272, up from
230 after D1), coverage gate re-verified at 96.67%. `backend/frek/`'s own
2 historical routes (`/genesis`, `/workshop`) are **untouched** — zero
lines changed, confirmed by a static-import test, per the explicit
instruction against destructive route migration this state. D1's own
verification status is **not** silently upgraded: `D1_VERIFIED` stays
`PARTIAL` (D2 consumes D1's extraction functions but produces no new
evidence about the signal algorithm's own robustness). D3–D5 remain
exactly as before: reconciled on paper, not started. Per the protocol,
this document now stops and waits for the founder to authorize STATE_3
(D3) before any further execution.

**Update (2026-09-02, D3/STATE_3 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: per `EXECUTE_D3=TRUE, EXECUTE_D4..D5=FALSE`, D3 —
Relationship / Provenance Graph — is now IMPLEMENTED, not just
reconciled. `docs/decisions/0006-d3-relationship-provenance-graph-
founder-decisions-implemented.md` is the full record. In brief:
`backend/relationship_graph/` (new module) preserves the historical FREK
Network's real taxonomy (5 node types; of the 17 declared relation types,
only 5 were ever actually emitted by `register_emission` — confirmed by
reading every call site, not assumed from the module's own docstring),
split structurally into TRUST and CULTURAL layers via a closed,
predicate-derived `layer` field a caller can never override. A CULTURAL
relationship (e.g. `similar_to`, `influenced_by`) can **never** reach
`RelationshipStatus.VERIFIED` — enforced in `service.derive_status` and
re-checked with a 409 in the verify endpoint, not merely documented.
Reuses, rather than reimplements: D6's `Claim`/`Evidence` (every
`Assertion` is literally composed of them), D2's real
`creative_lifecycle_events` (referenceable via `source_event_id`, never
re-executed), `permissions.models.Scope`/`ScopeType` (reused directly,
not a lookalike enum, for relationship visibility — `permissions.engine.
decide()` itself was deliberately NOT wired in, since no `RoleGrant`
persistence exists anywhere in the codebase to feed it honestly, a
disclosed tradeoff). Plain MongoDB (`db.relationships`, one collection
for both layers since `layer` is derived not caller-supplied), no
Neo4j/PostgreSQL/pgvector. Traversal is bounded (`max_depth` hard-capped
at 10 matching the historical route's own bound, plus a total-nodes-
visited cap the historical in-memory graph never needed). 41 new unit
tests, full unit suite green (315, up from 272 after D2), coverage gate
re-verified at 96.68%. `backend/frek/`'s own 7 historical réseau routes
are **untouched** — zero lines changed, confirmed by a static-import
test and a route-count regression guard, per the explicit instruction
against destructive route migration this state. D1's own verification
status is **not** silently upgraded (`D1_VERIFIED` stays `PARTIAL`). No
cultural-fingerprint/recommender/reputation/AI-influence pipeline was
built — the relationship shape supports these as future consumers only.
D4–D5 remain exactly as before: reconciled on paper, not started. Per
the protocol, this document now stops and waits for the founder to
authorize STATE_4 (D4) before any further execution.

**Update (2026-09-02, D4/STATE_4 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: per `EXECUTE_D4=TRUE, EXECUTE_D5=FALSE`, D4 — Offline
Proof Transport — is now IMPLEMENTED, not just reconciled.
`docs/decisions/0007-d4-offline-proof-transport-founder-decisions-
implemented.md` is the full record. In brief: `backend/offline_transport/`
(new module) preserves the historical multi-channel transmission vision
(5 declared protocols, confirmed) as a transport-independent,
cryptographically verifiable envelope + sync/reconciliation service. The
historical "packet" carried no real signature at all (`signature_short`
is an unverified 8-character hash prefix, not a signature over anything
— confirmed by reading the whole file, not assumed) — this state adds an
entirely new trust layer on top: a canonical, deterministically-
serialized envelope, Ed25519-signed via `passport.keys` (the same
institutional signer behind `.fk`'s own `ProofLayer.signature`, not a
second signer). `frek_v3/reference_verifier/` — a real, complete,
independently tested FREK Attestation Protocol implementation confirmed
by a prior pass to be fully isolated from `backend/` — is genuinely
called for the first time (`offline_transport/fap_adapter.py`), reusing
its real ECDSA verification, counter/replay/nonce/firmware checks
end-to-end for an optional device-attestation layer, never
reimplementing any of it. A cultural relation's inability to reach
VERIFIED (D3) has its own D4 analogue: a valid signature alone can never
reach `LOCALLY_ACCEPTABLE` — only `CRYPTO_VALID_BUT_STATUS_STALE` —
unless authority freshness is explicitly current and unexpired
(`OFFLINE_VERIFIED_EQUALS_ONLINE_STATUS_FRESH=FALSE`, enforced
structurally). Reuses, rather than reimplements: D6's `Claim`/`Evidence`
(every envelope is literally composed of them), D1 content bindings/D2
lifecycle events/D3 relationships (referenceable, validated to exist,
never re-executed). Plain MongoDB (`db.transport_envelopes`,
`db.offline_issuer_state`, `db.fap_devices`), no new database technology
— a persistent queue verified by test to survive across separate app
instances sharing the same database. The historical ultrasonic
watermark generator is reused verbatim, wrapped with an honest
`NOT_TESTED` validation status; `WATERMARK_EQUALS_PROOF=FALSE` is
enforced structurally (no other module in `offline_transport/` imports
the watermark module at all). 35 new unit tests, full unit suite green
(352, up from 315 after D3), coverage gate re-verified at 96.69%.
`backend/frek/`'s own 6 historical transmission routes are **untouched**
— zero lines changed, confirmed by a static-import test and a
route-count regression guard. D1's own verification status is **not**
silently upgraded (`D1_VERIFIED` stays `PARTIAL`). No hardware
verification is claimed for any transport adapter — this sandbox has no
real BLE/NFC/QR/ultrasonic hardware. D5 remains exactly as before:
reconciled on paper, not started. Per the protocol, this document now
stops and waits for the founder to authorize STATE_5 (D5) before any
further execution.

**Update (2026-09-02, D5/STATE_5 executed under FREKCORE_EXECUTION_
PROTOCOL_V1)**: per `EXECUTE_D5=TRUE, EXECUTE_STATE_6=FALSE`, D5 —
Technical Evidence Report / Juridical Framing — is now IMPLEMENTED, not
just reconciled. `docs/decisions/0008-d5-technical-evidence-report-
founder-decisions-implemented.md` is the full record. In brief:
`backend/technical_evidence_report/` (new module) preserves the
historical "notaire de fait, jamais juge de droit" *intent*
(`node09_juridique.py`'s own `NEVER_STATEMENTS`/`ALWAYS_STATEMENTS`
lists, real and largely correct) while replacing its blind-trust
*behavior*: `AttestationRequest` took `sha256_signal`/`vector_dimensions`/
`artiste_id`/`timestamp_ms`/GPS values directly from the request body
with no database lookup and no verification of any kind — confirmed by
reading `create_attestation` directly, not assumed — and
`to_legal_text()` rendered the unqualified overclaim "Ce fait est
mathematiquement certain et temporellement irrefutable." D5 is a pure
**consumer** of D1–D4 and D6, never creating new truth: a report is
composed only from a `subject_type`+`subject_id` resource reference
(`GenerateReportRequest` carries exactly that pair — verified by test
that extra caller-supplied fields never surface anywhere in the
generated report), resolved server-side against `db.frek_persons`/
`db.fk_objects`/`db.content_bindings`/`db.creative_lifecycle_events`/
`db.relationships`/`db.transport_envelopes`/`db.notary_blocks`. Sections
are labeled CLAIMED/OBSERVED/ATTESTED/COMPUTED/INFERRED/EVIDENCE/PROOF/
VERIFIED/UNKNOWN/NOT_VERIFIED/LEGAL_CONCLUSION_NOT_MADE — never flattened
to a single boolean, per D6's own requirement — and each D-state's own
legal-hardening rule is individually preserved in the report renderer: D1
validation stays labeled PARTIAL; D2's GENESIS/WORKSHOP/METAMORPHOSE/
EMISSION/LEGACY history always pairs with an explicit "not a legal
determination of authorship, ownership, or priority" statement; a D3
CULTURAL-layer relationship can never render as VERIFIED in the report
either (mirroring D3's own structural invariant, re-verified here by
test even against a hypothetically mislabeled record); a D4 SYNCED
envelope renders VERIFIED scoped explicitly to "transport-level integrity
and authority freshness for the envelope itself", never to the
underlying subject's ownership or authorship. A negation-aware
forbidden-phrase guard
(`technical_evidence_report/models.py:assert_no_forbidden_language`)
blocks IRREFUTABLE, PROVES OWNERSHIP, PROVES AUTHORSHIP, OFFICIAL
NOTARIAL ACT, QUALIFIED EIDAS TIMESTAMP, GUARANTEED ORIGINAL, UNFORGEABLE,
ABSOLUTE PROOF, and their French equivalents (case-insensitive) as a
pydantic field validator on every `ReportSection` — a section literally
cannot be constructed with an overclaim in it — verified against the
exact historical phrase as a regression fixture, and confirmed
negation-aware enough that the report's own fixed `LEGAL_DISCLAIMER` can
explicitly name and disclaim these same concepts ("It is NOT a notarial
act... NOT a qualified electronic timestamp...") without itself tripping
the guard, while a positive assertion of the identical phrase is still
rejected. Reuses, rather than reimplements: D6's `Claim`/`Evidence`
origin/kind fields directly to choose each section's `kind`;
`proof_engine.notary_adapter.proof_state_from_notary_block` against real
`db.notary_blocks` documents for the proof section, never reimplementing
the proof-state ladder; `permissions.models.Scope`/`ScopeType` directly,
per report section (not one report-level flag), for disclosure —
`PROOF_VISIBILITY != EVIDENCE_VISIBILITY`, `RELATIONSHIP_VISIBILITY !=
SUBJECT_METADATA_VISIBILITY`, `OBJECT_PUBLIC != ALL_PROVENANCE_PUBLIC`
are all structurally possible outcomes, not policy prose — the same
disclosed tradeoff D3 already made (`permissions.engine.decide()` not
wired, no `RoleGrant` persistence exists anywhere in this codebase).
`GET .../verify` is public and unauthenticated but returns shape only
(section kind/title, never statements/data, never raw evidence/
relationship/credential content) plus a recomputed integrity-hash match
(`VERIFICATION_MAY_BE_PUBLIC=TRUE` without violating
`DISCLOSURE_IS_AUTHORIZATION_SCOPED`); authorized retrieval redacts per
section and returns 404 (not a partial/empty body) when nothing is
visible, matching D3's own "404, not 403" privacy discipline. An
unresolvable resource reference returns 404, never a hollow report
describing nothing (`ARBITRARY_CALLER_SUPPLIED_FACTS_AS_CANONICAL_TRUTH
=FALSE`, fail-closed). Report integrity is a deterministic sha256 over a
canonical-JSON content subset (`technical_evidence_report/canonical.py`,
the same formula already independently kept in `fk/packager.py`,
`notary/chain.py`, and `offline_transport/canonical.py`), excluding
`verification_time` so re-verifying unchanged content never changes the
hash. 46 new unit tests, full unit suite green (400, up from 352 after
D4), coverage gate re-verified at 96.70%. `backend/frek/`'s own 1
historical `/juridique/attestation` route is **untouched** — zero lines
changed, confirmed by a static route-presence test and a static-import
guard (`BACKEND_FREK_CHANGED=NO`). All 5 preserved historical
capabilities (D1–D5) are now implemented; D6 (Evidence Semantics)
underlies all of them. Per the founder's own explicit instruction, D5
completion does **not** automatically authorize final freeze: the next
state the founder named is `STATE_6_HISTORICAL_COMPATIBILITY_
RECONCILIATION` (`EXECUTE_STATE_6=FALSE` this pass), explicitly not
Production Readiness, Wiring, or Deployment. Per the protocol, this
document now stops and waits for the founder to authorize STATE_6 before
any further execution.

**Update (2026-09-02, STATE_6/Historical Compatibility Reconciliation
executed under FREKCORE_EXECUTION_PROTOCOL_V1)**: per `EXECUTE_STATE_6=
TRUE, EXECUTE_STATE_7=FALSE`, Historical Compatibility Reconciliation is
now DONE. Full record: `docs/architecture/FREK_HISTORICAL_COMPATIBILITY_
MATRIX.md`. In brief: all 19 historical routes (re-verified from code
this pass: D1=3, D2=2, D3=7, D4=6, D5=1, matching the expected count)
each received an explicit disposition — 13 HARDEN (rate-limited via the
same `security.policies.check_rate_limit` every canonical route already
uses, made audit-visible via one new shared `legacy_route.invoked`
event, response shape otherwise unchanged), 4 ADAPTER (a genuine
canonical-module read or delegation added: D3's `/reseau/node/{id}`
cross-references canonical `relationship_graph` for OEUVRE nodes via
`bounded_neighbors`/`can_read` reused directly; D4's `/transmission/
protocols` and `/transmission/protocol/{protocol}` merge in canonical
`offline_transport.adapters.adapter_info()`; D4's `/transmission/
watermark` now calls canonical `offline_transport.watermark.
create_watermark_reference` directly, a strict response superset), and 2
HARDEN-with-a-disclosed-gap (D1's `/certify`+`/certify/upload` and D2's
`/genesis`+`/workshop` write sides cannot safely become full canonical-
write ADAPTERs without a further founder decision — D1's legacy
identity-minting has no existing `.fk` object to bind evidence to, and
D2's anonymous `artiste_id` has no session to authenticate as a
canonical `creative_lifecycle` actor without weakening that service's
own security model, per the founder's own explicit "Historical zero-auth
routes must NOT force canonical services to weaken their security
model" rule).

**Consumer discovery (this pass, whole-repository search)**: confirmed
real, live, local callers for the first time this reconciliation —
`frontend/src/pages/Certify.jsx` calls `POST /api/frek/certify`,
`frontend/src/pages/Verify.jsx` calls `GET /api/frek/verify/{frek_id}`,
both mounted at real frontend routes (`frontend/src/App.jsx`). This is
exactly the risk the founder's own `ABSENCE_OF_LOCAL_CALLER_EQUALS_NO_
CONSUMER=FALSE` rule anticipated, and it is why these two routes' response
changes are additive-only (new fields added, nothing removed or
restructured) — confirmed by a test pinning every field the real
frontend code reads. No other historical route has a confirmed local
caller; `ECOSYSTEM_WIDE_CONSUMER_AUDIT=INCOMPLETE` for all 19 (no other
CVLN repository is present in this workspace) — backward compatibility
stays mandatory regardless.

`backend/frek/` changed this state (`BACKEND_FREK_CHANGED=YES`, explicitly
permitted for STATE_6) — but only for hardening/compatibility: rate
limiting (`frek/legacy_compat.py`), audit visibility (a new shared event,
never duplicated alongside a canonical business event for the same call),
additive read-only canonical cross-references (never a write to any
canonical D1–D5 collection, confirmed by a static test), and — D5's own
route only — replacing its output's "mathematiquement irrefutable"
overclaim at the source (`node09_juridique.py:to_legal_text`, confirmed
clean against D5's own `assert_no_forbidden_language` guard). **Zero
routes deleted, zero historical vocabulary deleted, zero destructive API
migration** — `ROUTES_DELETED=0`, `CONCEPTS_DELETED=0`, locked in by a
static route-count regression test. 50 new unit tests, full unit suite
green (450, up from 400 after D5), coverage gate re-verified at 96.70%.
Per the founder's own explicit instruction, STATE_6 completion does
**not** automatically authorize STATE_7: the next state the founder
named is `STATE_7_API_SDK_CONTRACT_STABILIZATION`
(`EXECUTE_STATE_7=FALSE` this pass), explicitly not Production Readiness,
Wiring, or Deployment. Per the protocol, this document now stops and
waits for the founder to authorize STATE_7 before any further execution.

**Update (2026-09-03, STATE_7/API-SDK Contract Stabilization executed
under FREKCORE_EXECUTION_PROTOCOL_V1)**: per `EXECUTE_STATE_7=TRUE,
EXECUTE_STATE_8=FALSE`, API/SDK Contract Stabilization is now DONE. Full
record: `docs/architecture/FREKCORE_API_CONTRACT_V1.md` (the
authoritative endpoint matrix for the 11 capability areas the mission
named) plus 4 companion documents (`FREKCORE_SDK_CONTRACT_V1.md`,
`FREKCORE_EVENT_CONTRACT_V1.md`, `FREKCORE_ERROR_CONTRACT_V1.md`,
`FREKCORE_VERSIONING_POLICY.md`). `CANONICAL_INTERNAL_IMPLEMENTATION !=
PUBLIC_CONTRACT` is the organizing rule throughout: no D1–D6 route's own
behavior or response shape was changed this state
(`REWRITE_D1_D6_ARCHITECTURE=FALSE`, `BACKEND_FREK_CHANGED=NO`) — every
deliverable is either documentation, or new, unwired, pure-logic
coherence pieces (`backend/errors.py`'s canonical `ErrorCode`/
`CanonicalError` vocabulary; `permissions.models.ServiceIdentity`/
`DelegationGrant` + `permissions.delegation.delegation_permits()`, reusing
`Scope`/`Action` directly, `NO_PARALLEL_AUTHORITY_ENGINE=TRUE`, not wired
into any route — the same disclosed status `RoleGrant`/`decide()` have
had since Phase 2), or SDK extensions. Both SDKs grew from
Registry+Identity-read-only to also cover content_binding,
creative_lifecycle, relationship_graph, offline_transport, and
technical_evidence_report (one canonical create/generate + one canonical
read method per capability — deliberately lean, matching
`identity_client.py`'s own established precedent, not exhaustive
wrapping), with a canonical `FrekError` hierarchy (mapped from HTTP
status) now raised by every client method in both languages, including
the two pre-existing ones (a strictly additive change — `FrekError`
subclasses `httpx.HTTPStatusError` in Python; TypeScript's carries the
original `Response`). A real OpenAPI-generation contract test
(`backend/tests/test_api_contract.py`) confirms the canonical `/api/v1/
...` surface (46 endpoints) has no duplicate (method, path) pairs, all
19 legacy routes remain present in the generated schema, and a golden
snapshot genuinely detects a breaking contract change (not merely
exists). One draft inaccuracy was caught and corrected before
publication: an early pass of the API contract document claimed `GET
/api/v1/identity/{frek_id}` and the DID document route shared a path —
re-verified directly from `server.py`'s router mounts, they do not
(`did`/`vc` mount at their own separate `/did`/`/vc` prefixes) — the
published document states the corrected, verified finding. 33 new
backend unit tests, full unit suite green (483, up from 450 after
STATE_6), coverage gate re-verified at 96.91%; Python SDK suite green
(31, up from 18); TypeScript SDK suite green (38, up from 13). Per the
founder's own explicit instruction, STATE_7 completion does **not**
automatically authorize STATE_8: the next state the founder named is
`STATE_8_REGRESSION_EVIDENCE_MIGRATION_VALIDATION`
(`EXECUTE_STATE_8=FALSE` this pass), explicitly not Production Readiness,
Wiring, or Deployment. Per the protocol, this document now stops and
waits for the founder to authorize STATE_8 before any further execution.

**Update (2026-09-03, STATE_8/Regression-Evidence-Migration Validation
executed under FREKCORE_EXECUTION_PROTOCOL_V1)**: per `EXECUTE_STATE_8=
TRUE, BASELINE_HEAD=fc37516`, STATE_8 validated the integrated D1–D6 +
STATE_6 + STATE_7 baseline as one system rather than redesigning any of
it (`docs/validation/FREKCORE_STATE8_VALIDATION_PLAN.md` +
`FREKCORE_STATE8_VALIDATION_RESULTS.md` + `FREKCORE_MIGRATION_
VALIDATION.md` + `FREKCORE_FAILURE_MODE_MATRIX.md`). Full regression
re-run green (507 backend tests, up from 483, +24 genuinely new — audited
against the existing 62-file suite first, so nothing already covered
(offline-transport revocation/replay/conflict, D1 determinism/non-finite-
input safety, identity-reconciliation idempotency, and more) was
duplicated). STATE_7's `DELEGATED_AUTHORITY=PARTIAL` is now `VERIFIED`
(still unwired, UNIT_VERIFIED): `permissions.delegation.delegation_
authority_chain_valid()` composes the existing `decide()` with
`delegation_permits()` to prove the delegator actually held the
authority it purports to delegate, and that revoking the delegator's own
RoleGrant invalidates the delegation — `NO_PARALLEL_AUTHORITY_ENGINE=
TRUE` throughout. Real-MongoDB and real-OTS/Bitcoin-anchor validation
were both re-attempted, not assumed still blocked from D1–D6: both
remain `BLOCKED` (this sandbox now has no reachable Docker daemon at
all — `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`
— and the OTS calendar server is unreachable through the outbound proxy),
and mongomock is explicitly **not** substituted as equivalent evidence
(confirmed this state: it isolates state per client instance, unlike
real MongoDB) — the one genuinely real-infra-verified persistence layer
in this codebase is `storage.local.LocalFilesystemStorageProvider` (real
disk). All 19 `backend/frek/` legacy routes re-verified reachable,
correctly mapped to their D1–D5 canonical target, writing no independent
second truth, with response and identifier compatibility unchanged —
`backend/frek/`'s diff is empty this state too (`BACKEND_FREK_CHANGED=
NO`, same as STATE_7). One genuine docstring/code inconsistency was
found and fixed (a `DelegationGrant` docstring in `permissions/models.py`
overclaiming what `delegation_permits()` alone checks) — the one bounded
contract correction this state makes, not a redesign. `D1_VERIFIED=
PARTIAL` unchanged, no new scientific claim made. Per the founder's own
explicit instruction, STATE_8 completion does **not** automatically
authorize STATE_9: the next state the founder named is `STATE_9_FINAL_
HISTORICAL_ARCHITECTURAL_RECONCILIATION` (`EXECUTE_STATE_9=FALSE` this
pass). Per the protocol, this document now stops and waits for the
founder to authorize STATE_9 before any further execution.

---

## A. Executive summary

`backend/frek/` ("FREK v2") is not 19 unrelated legacy endpoints. Reading
every route's implementation (`backend/frek/routes.py`, `routes_advanced.py`,
and their 10 `nodes/node0X_*.py` backing modules) shows they express
**5 distinct, real, historically-documented ideas**, several of them not
represented anywhere in modern FREKCORE at all:

| Capability | Routes | One-line description | Modern FREKCORE equivalent |
|---|---|---|---|
| **D1 — Signal/Audio Fingerprint** | 3 | Turn an audio signal into a perceptual fingerprint, distinct from a cryptographic hash | NONE — `.fk`/`notary` hash files and manifests, never signal content |
| **D2 — Creative Lifecycle** | 2 | Prove intent and process before/during creation (GENESIS→WORKSHOP→...) — **IMPLEMENTED 2026-09-02** (`backend/creative_lifecycle/`) | PARTIAL — `frek_v1` has the same 5-stage vocabulary, but for event badges, not works (kept structurally separate) |
| **D3 — Relationship/Provenance Graph** | 7 | Auto-built graph of who-created-what-where-when — **IMPLEMENTED 2026-09-02** (`backend/relationship_graph/`) | NONE — `registry/` stores objects, never relations between them |
| **D4 — Offline Proof Transport** | 6 | Move a certification across BLE/NFC/WiFi/ultrasound without network — **IMPLEMENTED 2026-09-02** (`backend/offline_transport/`) | NONE — the closest is FREK V3/FAP's device-attestation model, complementary, now genuinely reused (not just complementary in theory) |
| **D5 — Human-Readable Technical Evidence** | 1 | Format a proof as a document a human/institution can read | PARTIAL — `notary` produces the real proof; this route formats unverified caller-supplied text |

Every one of the 5 shares the **same root technical defect**: none of
them persists anything durably today (`backend/frek/nodes/node04_memory.py`
falls back to pure Python process memory because it reads `MONGO_URL`
looking for a string that starts with `postgres`, which never happens in
this deployment — confirmed in `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`).
That shared defect is why the founder's prior "PostgreSQL/pgvector storage
gap" blocker language is retired here: the founder is not choosing a
database technology, the founder is confirming the *capabilities* survive,
and this document works out — per capability, not by fiat — what storage,
auth, and verification model each one actually needs going forward
(§M).

A sixth decision, **D6 — Evidence Semantics**, is not a historical
capability. It is the cross-cutting rule needed so the five capabilities
above (several of which produce *claims*, *inferences*, or *unverified
declarations*) never get silently upgraded to the status of a verified
fact merely by passing through FREKCORE. `proof_engine/models.py`'s
existing `ProofState` ladder (FINGERPRINT → LOCAL_PROOF → SIGNED_PROOF →
TIMESTAMP_PROOF → OPENTIMESTAMPS_PROOF → EXTERNAL_ANCHOR_PROOF) already
gives FREKCORE the "how strong is this proof" axis — D6 is about the
orthogonal "what kind of statement is this" axis (declared vs. observed
vs. computed vs. inferred vs. attested vs. verified), which nothing in
the codebase expresses today.

---

## B. Historical discovery — 19 routes → 5 capabilities

Full per-route detail in §D. Summary of the discovery (already presented
to the founder in the prior turn, restated here as the permanent record):

- **D1** (3 routes): `POST /api/frek/certify`, `POST /api/frek/certify/upload`,
  `GET /api/frek/verify/{frek_id}`
- **D2** (2 routes): `POST /api/frek/genesis`, `POST /api/frek/workshop`
- **D3** (7 routes): `GET /api/frek/advanced/reseau`, `/reseau/stats`,
  `/reseau/node/{node_id}`, `/reseau/neighbors/{node_id}`,
  `/reseau/artiste/{artiste_id}`, `/reseau/lieu/{lieu_id}`, `/reseau/path`
- **D4** (6 routes): `GET /api/frek/advanced/transmission`, `/transmission/protocols`,
  `/transmission/protocol/{protocol}`, `POST /transmission/packet`,
  `/transmission/watermark`, `/transmission/sync`
- **D5** (1 route): `POST /api/frek/advanced/juridique/attestation`

**Route-path correction**: `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`'s
table wrote the `routes_advanced.py` paths without their actual `/advanced`
segment (e.g. it wrote `GET /frek/reseau`). Verified against
`backend/server.py:229` (`app.include_router(frek_router, prefix="/api")`)
and the router nesting in `backend/frek/routes.py:20`
(`frek_router.include_router(advanced_router, prefix="")`, where
`advanced_router` itself carries `prefix="/advanced"`): the real, callable
paths are `/api/frek/...` for `routes.py` and `/api/frek/advanced/...` for
`routes_advanced.py`. This document uses the corrected paths throughout;
`FREK_LEGACY_ROUTE_AUDIT.md` is not rewritten (out of scope — pure
documentation reconciliation, not a route audit rewrite) but this
correction is the authoritative one going forward.

---

## C. Founder decisions D1–D6 (recorded verbatim in effect, condensed here)

| # | Decision | Disposition |
|---|---|---|
| D1 | Signal/Audio Fingerprint | PRESERVE + VALIDATE + HARDEN + ABSORB — **IMPLEMENTED 2026-09-01** (`backend/content_binding/`, `docs/decisions/0004-...`, `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`) |
| D2 | Creative Lifecycle | PRESERVE + ABSORB — **IMPLEMENTED 2026-09-02** (`backend/creative_lifecycle/`, `docs/decisions/0005-...`) |
| D3 | Relationship/Provenance Graph | PRESERVE + MIGRATE (split into D3-A Trust Graph, D3-B Cultural/Inferred Graph) — **IMPLEMENTED 2026-09-02** (`backend/relationship_graph/`, `docs/decisions/0006-...`) |
| D4 | Offline Proof Transport | PRESERVE + ADAPTER — **IMPLEMENTED 2026-09-02** (`backend/offline_transport/`, `docs/decisions/0007-...`) |
| D5 | Human-Readable Technical Evidence | PRESERVE INTENT + ABSORB + LEGAL HARDENING |
| D6 | Evidence Semantics | Cross-cutting rule, not a capability — governs how D1–D5 represent truth. **IMPLEMENTED 2026-09-01** (`proof_engine/evidence_semantics.py`) |

`DELETE_CONCEPT` is not used anywhere in this document — the founder has
foreclosed it for all five capabilities.

---

## D. Detailed 19-route mapping

Every route in a capability group shares nearly all 30 requested
dimensions (same storage gap, same auth gap, same target architecture) —
repeating identical prose 19 times would bury the 3 or 4 points that
actually vary route-to-route, which is the opposite of what a
reconciliation document is for. So: **each capability gets one full
30-point analysis**, followed by a **compact per-route table** carrying
only what differs (exact method/path, source function, and the couple of
points — like idempotency or example payload — that are genuinely
route-specific). Attributes 1–2 are given per-route in the table;
attributes 3–30 are the shared capability-level analysis.

### D1 — Signal / Audio Fingerprint

**3. Historical capability**: turn a raw audio signal into a
mathematical "fingerprint" (a 528-dimension vector: 512 FFT bands, RMS,
ZCR, 12 of 13 MFCC coefficients, spectral centroid, spectral flux — see
`backend/frek/nodes/node01_extraction.py`), then derive a permanent
identifier from it via three SHA-256 layers (signal hash, metadata hash,
chain hash — `node02_identity.py`).

**4. Historical semantics**: the vector is a *perceptual/signal*
fingerprint (survives re-encoding to a degree, not proven — see below),
while the three SHA-256 layers are *exact* cryptographic hashes over
specific byte sequences (the raw audio bytes, the metadata JSON, and a
chain string). The code's own naming calls the SHA-256-derived identifier
a "FREK-ID" — this is the origin of the historical overload the founder
has now resolved: **FREK-ID (canonical object identity) and Signal
Fingerprint (content/signal binding) must be modeled as two different
things going forward**, even though the historical code fused them into
one artifact.

**5. Unique intellectual/functional value**: nothing else in FREKCORE
computes a signal-domain fingerprint. `.fk` and `notary` hash *files* and
*manifests* — byte-exact, not signal-perceptual. The idea that a
fingerprint could recognize the same underlying sound through
re-recording/re-encoding — the actual unique value — is asserted but
**not demonstrated** by any test in this repository (see point 5 below,
"validation").

**6. Current FREKCORE equivalent**: `notary`'s hash-chain (`FrekChain`)
and `.fk`'s content-hash layer (`ProofLayer.content_hash`) both do
*exact* SHA-256 over file bytes — real, durable, already reused
repeatedly this session for new payload types. FREK V3/FAP
(`frek_v3/reference_verifier/`) does device-signed *attestation* of a
capture event, a different axis entirely (device trust, not content
similarity). Neither does perceptual signal matching.

**7. Overlap**: PARTIAL on "hash something to prove it existed"
(shared with `notary`/`.fk`), NONE on "recognize this signal even after
re-encoding" (the actual unique claim).

**8. Target primitive**: FREK Object → `content_bindings[]`, one entry
per binding type (`exact_hash`, `signal_fingerprint`, ...), each carrying
its own algorithm name, version, and confidence semantics — not a single
opaque `frek_id`.

**9. Target module/protocol/profile/adapter**: an **Audio Fingerprint
Profile** — a domain-specific extension consumed by `.fk`'s
`intelligence/` layer (already reserved, currently empty pending
FREKANSLA per `fk/models.py`'s own docstring: *"Reservee pour FREKANSLA.
Vide en v0.1"* — this session's own earlier finding). This is not core
FREKCORE kernel; it is exactly the kind of domain profile the founder's
ecosystem-wiring context calls out.

**10. Existing code reusable**: `node01_extraction.py`'s 6-algorithm
extraction pipeline (FFT/RMS/ZCR/MFCC/centroid/flux) is real,
self-contained signal-processing code with no storage dependency — directly
reusable as the extraction step. `node02_identity.py`'s SHA-256-over-bytes
layers are trivially reusable (already how `notary`/`.fk` hash things).

**11. Historical code requiring rewrite**: the FREK-ID generation format
(`FREK-{year}-{sequence:04d}-{hash8}-{hash8}`) uses an **in-process
sequence counter** (`Node04Memory._sequence_counter`, resets to 0 on
every restart) — this alone makes the historical ID format non-durable
independent of the storage question, and must not be carried forward
as-is. The chain-hash mechanism (`Node02Identity._last_frek_id`/
`_last_hash`, also plain instance attributes) is a **second, separate,
in-memory-only chain**, disconnected from `notary`'s real, tested,
MongoDB-backed hash chain — this is a duplicate mechanism to retire, not
a duplicate concept to delete: the *concept* (chained integrity) is
exactly what `notary.chain.append_block` already does correctly and
durably.

**12. Compatibility obligations**: none identified — no live client of
`/certify` was found referenced anywhere in `memory/INVENTORY.md`'s
"current production core" description (`reports/FREKCORE_CONTRADICTIONS.md`
C4). If the founder knows of an external caller, that changes this.

**13. Storage requirement**: the 528D vector needs a `VECTOR` type
storage engine, or a store with vector-similarity indexing. This is the
finding underlying the founder's storage-technology-neutral instruction
below (§M) — not necessarily MongoDB, not necessarily PostgreSQL.

**14. Vector requirement**: YES — a genuine similarity-search need,
unique to D1 (and D3-B, which consumes D1's vectors).

**15. Graph requirement**: NO directly (D3 consumes D1's output, D1
itself does not need graph storage).

**16. Authentication requirement**: `/certify` and `/certify/upload`
must be scoped to an issuing actor (device, app, or holder) — today
`grep -n "Depends|Header|x_admin|require_" backend/frek/routes.py` finds
zero matches, confirmed. `/verify` is a public read by nature (same
posture as `notary`'s own public verify endpoints).

**17. Authorization requirement**: who may certify on behalf of an
`artiste_id` is undefined historically — needs a real answer (self-issued
via a holder session? device-attested via FAP? both?) before hardening.

**18. Privacy/consent requirement**: `gps_lat`/`gps_lon`/`device_id` are
accepted and stored — real personal-data surface needing the same
consent model already built for `fingerprint`/`geo` this session
(`identity_engine`'s `X-FREK-Session`, holder-linked consent).

**19. Event emission**: NONE today (`grep -rn "eventbus\|audit_trail"
backend/frek/` → zero matches). A future implementation should emit via
the same `eventbus/producers.py` pattern already used for every other
FREKCORE mutation (`build_object_created_event`-shaped).

**20. Claim/evidence semantics**: this is where D6 binds directly to D1
— a fingerprint match is a *computed similarity*, never a *verified
identity of authorship*. The historical code's own PDF certificate text
("ATTESTATION FREK... Cette attestation certifie un fait technique. Elle
ne constitue pas une déclaration de droits") already states this
correctly in words; nothing in the code enforces the distinction
structurally.

**21. Proof requirements**: should reuse `proof_engine`'s existing
`ProofState` ladder unmodified — a certification event, once durably
notarized via `notary.chain.append_block`, is `LOCAL_PROOF`; a signal
fingerprint on its own, with no chain entry, is `FINGERPRINT`. No new
proof-state vocabulary needed (`proof_engine/models.py` already covers
this axis — confirmed by reading it this pass).

**22. Audit requirements**: a certification event is exactly the kind of
"sensitive mutation" `audit_trail`'s existing category scheme already
models (`work_lifecycle`, per `backend/audit/routes.py`'s `CATEGORIES`
dict added this session) — reusable without new categories.

**23. Offline semantics**: shared with D4 — a certification captured
offline (e.g. via FAP-attested hardware) needs the same offline-envelope
handling D4 defines; D1 does not need its own separate offline model.

**24. Replay/idempotency requirements**: none enforced today — the same
audio submitted twice produces two different FREK-IDs (different
timestamp → different metadata hash → different chain hash) rather than
being recognized as a duplicate. A real implementation needs an explicit
dedup/idempotency key, not assumed from the hash alone.

**25. Migration needs**: none — no durable historical data exists to
migrate (confirmed: everything is in-process memory, wiped on every
restart in every environment this session has run in).

**26. SDK/API impact**: none yet — neither SDK (`backend/sdk_python/`,
`sdk-typescript/`) wraps any `backend/frek/` route today; this would be a
net-new SDK surface, not a compatibility break.

**27. Security risks**: no auth (any caller can certify as any
`artiste_id`); no rate limit (`/certify` accepts up to 100MB per call,
uncapped call frequency) — a real DoS surface even before considering
data-integrity questions.

**28. Semantic-loss risk if mishandled**: HIGH if "Signal Fingerprint"
and "FREK-ID" stay conflated when D1 is finally built — every future
consumer (KORA, LabelOS, FREKANSLA) that asks "what identifies this
object" would get an answer entangled with "what does its content sound
like," which are different questions with different trust properties.

**29. Test strategy**: before any "this fingerprint is robust to
re-recording/compression/noise" claim is made, it needs the same kind of
evidence this session has insisted on elsewhere (golden vectors, measured
false-positive/false-negative rates under defined transformations — the
same bar `frek_v3/reference_verifier/`'s 16 golden vectors already meet
for FAP). None of that exists for D1 today.

**30. Final technical disposition**: **ABSORB** the concept
(fingerprint-as-content-binding) into the FREK Object model as a new,
additive `content_bindings` entry type, reusing `node01_extraction.py`'s
extraction code and `notary`'s existing durable chain — **not** a
`SUPERSEDE_IMPLEMENTATION` of `/certify` itself, since nothing modern
does what it does; **HARDEN** is required before any real traffic
(auth, rate limit, real storage, idempotency).

#### Per-route table

| # | Method/Path | Source (file:function) | Disposition |
|---|---|---|---|
| D1.1 | `POST /api/frek/certify` | `frek/routes.py:certify_audio` → `pipeline.certify` | ABSORB (concept) + HARDEN (before any use) |
| D1.2 | `POST /api/frek/certify/upload` | `frek/routes.py:certify_audio_upload` → `pipeline.certify` | Same as D1.1 — identical pipeline, different transport (multipart vs. base64) |
| D1.3 | `GET /api/frek/verify/{frek_id}` | `frek/routes.py:verify_frek_id` → `pipeline.verify` | ABSORB — the read-side of D1.1/D1.2, tied to the same disposition |

*(`GET /verify/{frek_id}/qr.png` and `GET /verify/{frek_id}/certificat.pdf`
are NOT among the 19 — they were already classified ADAPTER
candidate/PRESERVE in `FREK_LEGACY_ROUTE_AUDIT.md`; noted here only
because they are D1-adjacent presentation layers that should follow
D1's eventual `frek_id` shape once it changes.)*

**FUTURE ECOSYSTEM INTEGRATION IMPACT (D1)**

1. *What FREKCORE exposes*: a `content_bindings` read/write surface on
   the FREK Object — "does this signal bind to this object, and with what
   confidence."
2. *What remains inside FREKCORE*: the extraction algorithm's canonical
   parameters (band count, MFCC count, normalization) — these must be
   versioned and stable so two systems computing a fingerprint agree.
3. *What belongs in a protocol/profile/adapter*: the Audio Fingerprint
   Profile itself (FREKANSLA's domain), not the kernel.
4. *What consuming applications will use*: KORA/LabelOS asking "does this
   candidate match a known object" via a similarity query, not raw vector
   math.
5. *What must NOT be hardcoded into FREKCORE*: any specific
   music/audio-industry business logic (royalty splits, catalog matching
   rules) — FREKCORE answers "how similar," not "who owns the sample
   clearance."
6. *Likely SDK/API contract*: `POST /object/{id}/bindings`,
   `GET /object/{id}/bindings/similar?limit=N`.
7. *Third-party consumable*: YES — any external system with its own audio
   can ask FREKCORE "have you seen something like this," without becoming
   a CVLN application.
8. *Works without CVLN Intelligence OS*: YES — this is a FREKCORE
   primitive; the Intelligence OS would only orchestrate *which* consumer
   calls it and *why*.
9. *Works offline/degraded*: extraction itself is local/offline-capable
   (no network needed to compute a vector); the similarity search against
   the full corpus is not (needs the index), so this profile is
   online-only for its comparison step — consistent with FAP/D4's
   handling of "cryptographically valid ≠ currently verified."

---

### D2 — Creative Lifecycle (GENESIS / WORKSHOP)

**3. Historical capability**: declare creative intent before a work
exists (GENESIS), then log timestamped intermediate versions during
creation (WORKSHOP) — `backend/frek/nodes/node03_cycle.py`'s 5-stage
"luciole" model: GENESIS → WORKSHOP → METAMORPHOSE → EMISSION → LEGACY.

**4. Historical semantics**: *"FREK ne certifie pas un fichier à un
instant T. Il certifie une vie créative complète"* (module docstring).
Confirmed as a founding-era concept, not reconstructed after the fact:
`memory/assurance_package_v1.0/09_Version_History.md` (a document this
pass newly located and cross-referenced — see §Q) places *"Concept
Luciole (11 niveaux → 5 stades...)"* in **Phase 1, February 2026**, the
project's very first month, under a slightly different stage vocabulary
(GENESIS/EVIDENCE/BINDING/PROOF/LEGACY) later settled into
GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY — the exact vocabulary
`frek_v1/models.py`'s `STAGE_ORDER` uses today, confirmed identical by
direct comparison. This is real, demonstrable historical intent, not an
after-the-fact rationalization.

**5. Unique intellectual/functional value**: documenting the *process*
of creation (drafts, false starts, dated intermediate states) as evidence
of authorship priority — genuinely absent from every other FREKCORE
module.

**6. Current FREKCORE equivalent**: `frek_v1` uses the **identical**
5-stage vocabulary — but for an **event participant's badge lifecycle**
(CC2026), not a creative work. `identity_engine` has no staged lifecycle
at all. `backend/heritage/` is lifecycle-adjacent (declare → claim/transfer
across a person's lifetime) but models succession of *control over an
identity*, not creative process — a different concept sharing the same
general "declare intent → record dated milestones" shape, worth
cross-referencing but not merging.

**7. Overlap**: PARTIAL — same vocabulary, applied to a different kind of
subject (Person-as-participant vs. Work-as-creation). This is the same
"same lifecycle words, different subject kind" overload
`FREK_LEGACY_ROUTE_AUDIT.md`'s "second finding" already named.

**8. Target primitive**: an `Activity`/`Event` record on a FREK Object,
carrying `stage` (GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY),
`actor`, `claim` (the intention/notes), `timestamp`, and optional
`evidence` (a partial vector, an audio snippet hash) — not a bespoke
`CycleState` class parallel to `frek_v1`'s.

**9. Target module/protocol/profile/adapter**: a **Creative Lifecycle
Profile**, expressed as a sequence of `EVENT` + `CLAIM` records against
one FREK Object — reusing the Event/Claim primitives from the canonical
model evolution (§E), not a new parallel state machine.

**10. Existing code reusable**: the 5-stage enum and its ordering
(`Stade(IntEnum)`, `frek_v1/models.py:STAGE_ORDER`) are directly
reusable — both already agree on the vocabulary and order.

**11. Historical code requiring rewrite**: `Node03Cycle`'s in-memory
`CycleState` storage (dict keyed by `pre_id`) has no persistence and no
authority check on who may add a WORKSHOP version to someone else's
`pre_id`.

**12. Compatibility obligations**: none identified (no confirmed caller).

**13. Storage requirement**: append-only event log per object — exactly
what `notary.chain.append_block` already provides (already reused this
session for `identity_recovery`, `identity_reconciliation`, `renewal`,
`heritage_transfer`, `heritage_declare` payload types — GENESIS/WORKSHOP
would be two more payload types on the same generic, schema-free
extensibility point, not a new storage engine).

**14. Vector requirement**: only if a WORKSHOP entry carries a partial
audio fingerprint (D1-dependent, optional).

**15. Graph requirement**: NO directly — though D3's `DERIVED_FROM`/
`VERSION_OF` relations would naturally reference D2's stage history.

**16. Authentication requirement**: YES — `POST /genesis` and
`POST /workshop` must be scoped to a real actor (the historical code has
none: `grep` confirms zero auth on either route).

**17. Authorization requirement**: only the declaring actor (or an
explicit delegate) should be able to add a WORKSHOP version to a given
GENESIS — undefined historically.

**18. Privacy/consent requirement**: LOW — no GPS/device data in these
two routes specifically (unlike D1).

**19. Event emission**: NONE today; should emit via `eventbus` on each
stage transition, same pattern as `identity_engine`'s existing
stage-transition events.

**20. Claim/evidence semantics**: **directly** the founder's own
worked example — *"GENESIS ne signifie PAS automatiquement 'je suis
juridiquement l'auteur'... GENESIS peut établir: cet acteur identifiable
a enregistré telle assertion... à tel moment, avec telles preuves
disponibles."* This is a CLAIM (an assertion by an identified actor),
optionally strengthened by EVIDENCE (a partial fingerprint) and PROOF
(once notarized) — exactly the D6 vocabulary applied to this capability.

**21. Proof requirements**: same `ProofState` ladder as D1 — a
GENESIS/WORKSHOP entry becomes `LOCAL_PROOF` the moment it is
`append_block`-ed, same as any other notarized payload.

**22. Audit requirements**: reuses `audit_trail`'s `work_lifecycle`
category (already exists, added this session).

**23. Offline semantics**: a WORKSHOP entry created offline (in a studio
with no connectivity) is a real, plausible use case — should reuse D4's
offline envelope rather than defining its own.

**24. Replay/idempotency requirements**: adding the same WORKSHOP version
twice should not create two entries — needs an idempotency key (e.g. a
client-supplied `version_id`, which the historical `WorkshopVersion`
dataclass already has a field for but never enforces uniqueness on).

**25. Migration needs**: none (no durable historical data).

**26. SDK/API impact**: net-new surface, no break.

**27. Security risks**: unauthenticated write to an arbitrary `pre_id` —
anyone could add a fabricated WORKSHOP entry to another artist's GENESIS
declaration today.

**28. Semantic-loss risk if mishandled**: HIGH if GENESIS is ever
presented to a user as "legal proof of authorship" rather than "a dated
claim, optionally evidenced" — this is precisely the CLAIM≠PROOF
confusion D6 exists to prevent, and precisely the confusion the historical
PDF certificate text (D5) already tries, informally, to avoid.

**29. Test strategy**: regression tests should assert the stage ordering
invariant (`GENESIS < WORKSHOP < METAMORPHOSE < EMISSION < LEGACY`, no
skipping backward) — the same invariant this session already
tests for `frek_v1`'s stage transitions (`test_frek_v1_renew_unit.py`'s
sibling coverage), reusable pattern.

**30. Final technical disposition**: **ABSORB** the concept as an
Event/Claim sequence on the FREK Object, reusing `notary.chain.
append_block` for durability and `frek_v1`'s already-proven stage
vocabulary — **HARDEN** (auth, idempotency) required before real use.

#### Per-route table

| # | Method/Path | Source (file:function) | Disposition |
|---|---|---|---|
| D2.1 | `POST /api/frek/genesis` | `frek/routes.py:start_genesis` → `pipeline.start_genesis` → `node03.start_genesis` | ABSORB + HARDEN |
| D2.2 | `POST /api/frek/workshop` | `frek/routes.py:add_workshop_version` → `pipeline.add_workshop` → `node03.add_workshop_version` | ABSORB + HARDEN (same disposition, tied to D2.1's `pre_id`) |

**FUTURE ECOSYSTEM INTEGRATION IMPACT (D2)**

1. *Exposes*: an Event/Claim history per object — "show me how this
   object came to be."
2. *Remains inside FREKCORE*: the stage vocabulary and its ordering
   invariant (shared truth every consumer needs to agree on).
3. *Protocol/profile/adapter*: Creative Lifecycle Profile — domain logic
   for what a "WORKSHOP version" specifically contains belongs to the
   producing application (e.g. FREKANSLA), not the kernel.
4. *Consuming applications*: LabelOS could query "what's the creative
   history of this master"; Academy is unlikely to need this at all — a
   real example of why this must be a profile, not a mandatory kernel
   feature.
5. *Must NOT be hardcoded*: any specific art-form's creative process
   (music vs. visual art vs. writing have different meaningful
   "intermediate versions") — the kernel only records
   actor+claim+timestamp+evidence, generically.
6. *Likely SDK/API contract*: `POST /object/{id}/lifecycle/{stage}`,
   `GET /object/{id}/lifecycle`.
7. *Third-party consumable*: YES.
8. *Works without CVLN Intelligence OS*: YES.
9. *Works offline/degraded*: YES, via D4's envelope.

---

### D3 — Relationship / Provenance Graph

**3. Historical capability**: an auto-built graph — 5 node types
(Œuvre, Artiste, Lieu, Époque, Fréquence), 17 relation types
(`cree_par`, `similar_to`, `derive_de`, `collabore_avec`, `influence`,
`accueille`, `tendance`, `cluster`, ...) — `backend/frek/nodes/
node06_reseau.py`.

**4. Historical semantics**: *"FREK ne vit pas seul. Chaque FREK-ID est
un nœud dans un graphe vivant."* A complete, deliberate relational model
— not a sketch. **INTENTION HISTORIQUE NON PROUVÉE au-delà du code**: no
document in `memory/` or `frek_v3/docs/` was found describing this graph
before it was implemented; the intention is real and detailed, but its
evidence is the code itself, not an antecedent design document.

**5. Unique intellectual/functional value**: relationship modeling
between cultural entities (creators, works, places, eras) — completely
absent elsewhere.

**6. Current FREKCORE equivalent**: NONE. `registry/` stores objects
and their `namespace`/`owner_id`; `.fk` has exactly one informal
relational field, `based_on: Optional[str]` (`fk/models.py:61`) — a
single, untyped derivation pointer, not a relation model. Confirmed by
grep: no `relation_id`/`predicate`/`subject`/`object` model exists
anywhere in the codebase today.

**7. Overlap**: NONE with any durable modern store; PARTIAL conceptual
overlap with `.fk`'s single `based_on` field (which is one specific case
of D3-A's `DERIVED_FROM`).

**8. Target primitive**: **split in two**, per the founder's explicit
D3-A/D3-B distinction:

- **D3-A (Trust/Provenance Graph)**: a typed relation record —
  `subject`, `predicate`, `object`, `source` (who declared/observed/
  attested it), `authority` (under what authority), `timestamp`,
  `provenance`, `evidence`, `verification_status`, `visibility`,
  `lineage`. This can carry real trust weight (`CREATED_BY`,
  `CERTIFIED_BY`, `ISSUED_BY`, `OWNED_BY`) because each relation records
  who is vouching for it and under what authority.
- **D3-B (Cultural/Inferred Graph)**: relations like `SIMILAR_TO`,
  `INFLUENCED_BY`, `RESONATES_WITH` — outputs of computation or human
  judgment, never auto-promoted to D3-A's trust status. `node06_reseau.py`'s
  own 17 relation types split cleanly along this line: `cree_par`,
  `emis_a`, `accueille` are D3-A-shaped (who did what, where, under whose
  authority); `similar_to`, `influence`, `resonance_avec`, `tendance`,
  `cluster*` are D3-B-shaped (computed/inferred).

**9. Target module/protocol/profile/adapter**: D3-A is close enough to
universal (provenance is core to FREKCORE's own canonical definition) to
be a **core module**, consumed by the Registry and `.fk`. D3-B is a
**derived-intelligence system** per the founder's explicit instruction —
it consumes D3-A's verified inputs plus D1's fingerprints, but is not
core kernel (same category as Cultural Fingerprint, Recommendation,
Trend analysis — all explicitly named as NOT-core by the founder).

**10. Existing code reusable**: the **17-relation taxonomy itself** is
real, well-thought-out domain modeling — directly reusable as the seed
vocabulary for D3-A/D3-B's predicate sets, even though the storage engine
under it must change entirely.

**11. Historical code requiring rewrite**: everything storage- and
query-related (`GraphNode`/`GraphEdge` in-memory dicts, `find_path`'s
BFS over in-memory adjacency) — none of it persists, none of it has an
access-control check.

**12. Compatibility obligations**: none identified.

**13. Storage requirement**: relationship/graph-query storage — genuinely
a different storage shape than document storage (see §M) — this is the
component of the founder's `ARCHITECTURE CIBLE` diagram most likely to
justify a technology distinct from whatever stores FREK Objects.

**14. Vector requirement**: D3-B specifically (similarity-based edges
consume D1's vectors); D3-A does not.

**15. Graph requirement**: YES, explicitly and centrally — the one
capability among the five whose storage need is unambiguous.

**16/17. Authentication/authorization requirement**: every read route
today (`grep` confirms all 7 are auth-free) exposes potentially private
relationship data (who collaborates with whom, what an artist created
where) with zero access control — this is D3's most acute security gap,
not merely a persistence gap.

**18. Privacy/consent requirement**: HIGH — per the founder's own
explicit "a true relation is not automatically public" instruction.
`permissions/models.py`'s existing `ScopeType` enum (`GLOBAL` /
`ORGANIZATION` / `ENTITY` / `OBJECT`) is the reusable primitive for this
— confirmed by reading `permissions/models.py` this pass — rather than
inventing a parallel `PUBLIC`/`HOLDER_ONLY`/`PRIVATE` visibility system
as the founder's own draft suggested. **REUSE, do not parallel-build.**

**19. Event emission**: NONE today; each new relation should emit an
event, same `eventbus` pattern.

**20. Claim/evidence semantics**: this is the central D6 application —
D3-A relations carry `verification_status` (declared/observed/attested/
verified), D3-B relations are explicitly `INFERRED` and must never
silently promote to `VERIFIED`.

**21. Proof requirements**: a D3-A relation backed by a notarized event
(e.g. `CERTIFIED_BY` derived from an actual `notary` block) inherits that
block's `ProofState`; a D3-A relation that is merely *declared* by an
actor with no supporting block is `FINGERPRINT`-equivalent at best — the
existing `ProofState` ladder applies unmodified.

**22. Audit requirements**: relation creation/deletion is exactly the
kind of event `audit_trail` should record — reuse existing categories,
likely `work_lifecycle` or a graph-specific category if evidence
justifies one (not decided here — technical reconciliation item, §T).

**23. Offline semantics**: relations discovered/declared offline (e.g. a
device recording "this work was performed at this GPS location") need
D4's offline envelope to travel, then resolve into a D3-A record on sync.

**24. Replay/idempotency**: a relation should be idempotent on
`(subject, predicate, object, source)` — declaring the same relation
twice should not duplicate it.

**25. Migration needs**: none (no durable historical data).

**26. SDK/API impact**: net-new surface.

**27. Security risks**: the current unauthenticated read surface is the
most acute — 7 routes exposing potentially sensitive relational data
with zero access control, worse than D1/D2's write-side gaps because it
is a *read* exposure of data that may already exist for other reasons
(e.g. GPS-linked location history).

**28. Semantic-loss risk**: HIGH if D3-A and D3-B are merged into one
undifferentiated graph — every consumer would then have to independently
re-derive "is this relation trustworthy or just a similarity score,"
exactly the mistake the founder's split explicitly prevents.

**29. Test strategy**: regression tests should assert the D3-A/D3-B
separation holds structurally (a D3-B relation type can never appear with
a D3-A `verification_status` of `VERIFIED`), and that visibility scoping
is enforced per relation, not per route.

**30. Final technical disposition**: **PRESERVE + MIGRATE** — the
17-relation taxonomy is preserved as vocabulary; the storage/query
mechanism is fully migrated to a real, access-controlled, D3-A/D3-B-split
architecture reusing `permissions`' existing `ScopeType`.

#### Per-route table

| # | Method/Path | Source (file:function) | D3-A or D3-B example | Disposition |
|---|---|---|---|---|
| D3.1 | `GET /api/frek/advanced/reseau` | `routes_advanced.py:reseau_info` → `node06.get_stats` | Overview (both) | MIGRATE |
| D3.2 | `GET /api/frek/advanced/reseau/stats` | `routes_advanced.py:reseau_stats` → `node06.get_stats` | Overview (both) | MIGRATE |
| D3.3 | `GET /api/frek/advanced/reseau/node/{node_id}` | `routes_advanced.py:get_node` → `node06.get_node` | Either, depends on node type | MIGRATE |
| D3.4 | `GET /api/frek/advanced/reseau/neighbors/{node_id}` | `routes_advanced.py:get_neighbors` → `node06.get_neighbors` | Both (mixed result set) | MIGRATE |
| D3.5 | `GET /api/frek/advanced/reseau/artiste/{artiste_id}` | `routes_advanced.py:get_artiste_graph` → `node06.get_artiste_graph` | Both | MIGRATE |
| D3.6 | `GET /api/frek/advanced/reseau/lieu/{lieu_id}` | `routes_advanced.py:get_lieu_activity` → `node06.get_lieu_activity` | D3-A (`accueille`) | MIGRATE |
| D3.7 | `GET /api/frek/advanced/reseau/path` | `routes_advanced.py:find_path` → `node06.find_path` | Both (path may cross either kind of edge) | MIGRATE |

**FUTURE ECOSYSTEM INTEGRATION IMPACT (D3)**

1. *Exposes*: relation queries (`who is X related to, and how`) with
   explicit provenance/visibility per relation.
2. *Remains inside FREKCORE*: the D3-A trust-relation model and its
   verification-status tracking (core trust primitive).
3. *Protocol/profile/adapter*: D3-B (cultural/inferred graph, similarity,
   trend analysis) is a derived-intelligence consumer, not kernel.
4. *Consuming applications*: KORA ("who has authority to publish this"),
   LabelOS ("what rights relationships exist"), CVLN Intelligence OS
   (orchestrating D3-B analytics) — each reading only the relation types
   relevant to it.
5. *Must NOT be hardcoded*: business-specific relation semantics (e.g. a
   record-label-specific contract relation) — FREKCORE exposes generic
   typed relations with provenance, not label-business logic.
6. *Likely SDK/API contract*: `GET /object/{id}/relations`,
   `POST /relations` (scoped, authenticated), `GET /relations/path`.
7. *Third-party consumable*: YES, subject to visibility scoping per
   relation.
8. *Works without CVLN Intelligence OS*: YES for D3-A (core trust);
   D3-B's higher-value analytics likely benefit from but do not strictly
   require it.
9. *Works offline/degraded*: relation declaration can be queued offline
   (via D4) and reconciled on sync; relation *query* needs connectivity.

---

### D4 — Offline Proof Transport

**3. Historical capability**: move a FREK certification across
BLE/NFC/WiFi-local/ultrasound/cellular without requiring live network
connectivity — `backend/frek/nodes/node07_transmission.py`, with an
explicit 3-phase hardware roadmap (2026 software-only → 2027 SDK →
2028+ native chip).

**4. Historical semantics**: *"Le FREK-ID voyage avec le signal — comme
un passeport fréquentiel."* The `OfflineCertification` dataclass's own
`local_storage_path` field (never wired to actual disk I/O) shows local
persistence was anticipated at design time, even though never
implemented. **INTENTION HISTORIQUE NON PROUVÉE au-delà du code and its
coherence with the separately-documented FREK V3/FAP hardware vision** —
no antecedent document specifying NODE07 itself was found, but the
3-phase hardware roadmap is directly consistent with `frek_v3/`'s own,
separately and more rigorously documented hardware-maturity roadmap
(this session's own `FAP_PROOF_ENGINE_RECONCILIATION.md` addendum).

**5. Unique intellectual/functional value**: FREK proof surviving
*physically*, without network, including hidden in the audio signal
itself (ultrasonic watermark) — nothing else in FREKCORE addresses "how
does a certification survive with no connectivity."

**6. Current FREKCORE equivalent**: NONE for multi-channel transport
specifically. FREK V3/FAP (`frek_v3/`) covers a related but distinct
problem — a *device* signing a capture event with a hardware-rooted key
(DRK→AK, per this session's crypto-architecture reconciliation) — that is
about *whose device produced this*, not *how does the resulting proof
travel*. Complementary, not overlapping, confirmed by re-reading both.

**7. Overlap**: NONE on transport; PARTIAL/complementary on "a device
attests something offline" (FAP handles the attestation, D4 would handle
the transport of that attestation).

**8. Target primitive**: a **FREK Transport Envelope** — the kernel-owned
data shape that travels (identity/issuer reference, evidence/proof
references, signature, timestamp, sequence, counter, nonce, replay
protection, dedup key) — with **transports as pluggable adapters**
(BLE/NFC/WiFi/QR/audio/ultrasound/cellular/future), per the founder's
explicit CORE VS ADAPTERS instruction.

**9. Target module/protocol/profile/adapter**: the envelope is core (or
close to it — a genuinely universal "how does trust data travel when
disconnected" concern); each transport is an adapter, never a kernel
dependency.

**10. Existing code reusable**: `node07_transmission.py`'s
`TransmissionPacket.to_bytes()`/`from_bytes()` compact binary
serialization (a real, working, tested-shape wire format: 64+32+8+1+8
bytes) is directly reusable as a starting point for the envelope's wire
format. The `TransmissionProtocol` enum (5 real transport identifiers)
is directly reusable as the adapter registry's seed vocabulary.

**11. Historical code requiring rewrite**: `create_ultrasonic_watermark`,
`sync_pending`, and the packet-creation flow are all in-memory
simulations today — nothing is actually transmitted over Bluetooth/NFC;
this is interface-complete, backend-empty code (`OfflineCertification.
local_storage_path` is set but never read from or written to disk,
confirmed by grep).

**12. Compatibility obligations**: none identified.

**13. Storage requirement**: a local queue/log for pending offline
items, plus sync-state tracking — a different shape again from D1's
vector store or D3's graph store (see §M).

**14/15. Vector/graph requirement**: NO directly (D4 transports whatever
evidence D1/D2/D3 produced; it does not itself need vector or graph
storage).

**16/17. Authentication/authorization requirement**: the envelope itself
must carry the issuer's signature (so a received packet can be
authenticated without a live connection to FREKCORE) — none of the
historical routes implement this; `create_packet` accepts caller-supplied
`sha256_signal` with no signature at all.

**18. Privacy/consent requirement**: transmitted packets carry
`gps_condensed` — same location-data handling requirement as D1.

**19. Event emission**: `sync_pending` should emit a batch of events on
successful reconciliation, one per synced item — reusing the existing
per-mutation event pattern, not inventing a batch-event shape from
scratch unless evidence shows one is needed.

**20. Claim/evidence semantics**: **directly** the founder's worked
example — *"CRYPTOGRAPHICALLY VALID ≠ CURRENTLY AUTHORIZED ≠ FULLY
VERIFIED."* An offline-received envelope may have a valid signature yet
reference a credential that was revoked after the device went offline —
the envelope's status must distinguish `signature_valid` /
`issuer_known` / `status_freshness` / `offline_accepted` /
`online_reconciled` / `rejected_after_reconciliation`, reusing the
concept, not necessarily these exact names (per the founder's own
instruction not to force exact enum names).

**21. Proof requirements**: an offline-accepted envelope is provisionally
below `LOCAL_PROOF` until reconciled (it hasn't reached `notary` yet);
once synced and `append_block`-ed, it inherits the normal `ProofState`
ladder.

**22. Audit requirements**: sync/reconciliation events belong in
`audit_trail`, likely under `operational_access` or a new category if the
technical-reconciliation phase finds evidence for one.

**23. Offline semantics**: this capability's entire reason to exist —
already covered above.

**24. Replay/idempotency requirements**: **explicitly named in the
historical packet format itself** (nothing implements it) — a
`counter`/`nonce` scheme, same shape as FAP's own replay protection
(`frek_v3/reference_verifier`'s counter/nonce handling, already reconciled
this session) is the natural reuse target rather than inventing a
second, FREK-Transport-specific replay mechanism.

**25. Migration needs**: none.

**26. SDK/API impact**: net-new; likely the SDK surface most different
in *kind* from the others (needs a client-side offline queue, not just
an HTTP wrapper).

**27. Security risks**: unsigned packets, no replay protection, and (for
the watermark specifically) **no experimental validation whatsoever**
that the ultrasonic encoding is actually inaudible, robust, or reliably
decodable — the founder's own instruction not to claim robustness without
validation applies with full force here.

**28. Semantic-loss risk**: MEDIUM — the offline-first *vision* is well
captured historically; the risk is building transport adapters before the
envelope's trust semantics (point 20) are solid, which would lock in the
wrong contract for every future adapter.

**29. Test strategy**: envelope-level tests (signature verification,
replay rejection, reconciliation state transitions) can be written and
proven without any real Bluetooth/NFC hardware — exactly the same
"reference-implementation-first" discipline this session already applied
to FAP.

**30. Final technical disposition**: **ADAPTER** — the envelope is a
near-core primitive; each transport (BLE/NFC/WiFi/ultrasound/cellular)
is explicitly an adapter around it, never baked into the kernel.

#### Per-route table

| # | Method/Path | Source (file:function) | Disposition |
|---|---|---|---|
| D4.1 | `GET /api/frek/advanced/transmission` | `routes_advanced.py:transmission_info` → `node07.get_stats` | ADAPTER (overview) |
| D4.2 | `GET /api/frek/advanced/transmission/protocols` | `routes_advanced.py:get_protocols` → `node07.get_all_protocols` | ADAPTER (registry read) |
| D4.3 | `GET /api/frek/advanced/transmission/protocol/{protocol}` | `routes_advanced.py:get_protocol_info` → `node07.get_protocol_info` | ADAPTER (registry read) |
| D4.4 | `POST /api/frek/advanced/transmission/packet` | `routes_advanced.py:create_transmission_packet` → `node07.create_packet` | ADAPTER + HARDEN (needs signature) |
| D4.5 | `POST /api/frek/advanced/transmission/watermark` | `routes_advanced.py:create_watermark` → `node07.create_ultrasonic_watermark` | ADAPTER + VALIDATE (no experimental evidence today) |
| D4.6 | `POST /api/frek/advanced/transmission/sync` | `routes_advanced.py:sync_pending` → `node07.sync_pending` | ADAPTER + HARDEN (reconciliation semantics undefined today) |

**FUTURE ECOSYSTEM INTEGRATION IMPACT (D4)**

1. *Exposes*: an offline transport envelope contract and a sync/
   reconciliation endpoint.
2. *Remains inside FREKCORE*: envelope schema, signature/replay/
   reconciliation semantics.
3. *Protocol/profile/adapter*: every specific transport (BLE/NFC/etc.) is
   an adapter; the watermark specifically is a Luciole/FAP-adjacent
   adapter, not core.
4. *Consuming applications*: Wallet (receiving an offline credential
   presentation), Luciole/FAP hardware (producing offline-captured
   evidence), any festival/field-deployment scenario across the
   ecosystem.
5. *Must NOT be hardcoded*: any specific hardware SDK's wire format —
   FREKCORE owns the envelope, not the radio protocol.
6. *Likely SDK/API contract*: `POST /transport/envelope` (create),
   `POST /transport/sync` (reconcile a batch), transport-specific client
   libraries outside the kernel.
7. *Third-party consumable*: YES — this is precisely the kind of
   primitive an external organization could adopt without becoming a
   CVLN application (emit/verify FREK-compatible offline envelopes
   independently).
8. *Works without CVLN Intelligence OS*: YES.
9. *Works offline/degraded*: this capability **is** the offline/degraded
   case.

---

### D5 — Human-Readable Technical Evidence (Attestation)

**3. Historical capability**: format supplied technical data (signal
hash, artist ID, timestamp, GPS) into a legally-careful, human-readable
document — `backend/frek/nodes/node09_juridique.py:create_attestation`.

**4. Historical semantics**: the founding doctrine, stated precisely:
*"FREK ne joue pas sur le terrain juridique. Il joue sur le terrain
technique. Un fait technique n'est pas attaquable juridiquement. FREK est
un notaire de fait — jamais un juge de droit."* With an explicit NEVER
list (*"cet artiste est l'auteur"*, *"cette œuvre est originale"*, *"ces
droits lui appartiennent"*) and an explicit ALWAYS list (*"ce signal a
été soumis par cet identifiant, à ce timestamp"*). This is real,
well-preserved founding IP.

**5. Unique intellectual/functional value**: **the doctrine's wording**,
not the route's behavior — the wording is precious; the route itself adds
nothing verifiable.

**6. Current FREKCORE equivalent**: PARTIAL, and the important finding
of this section — `backend/notary/` is the real, modern attestation
mechanism: it durably writes into a hash chain, can anchor to Bitcoin,
and is already reused for every notarization this session has built
(identity recovery, reconciliation, renewals, heritage). The historical
`/juridique/attestation` route, by contrast, **verifies nothing and
stores nothing** — it accepts whatever `sha256_signal`/`artiste_id`/
`timestamp_ms` the caller supplies (even fabricated) and reformats them
into official-sounding prose, with no lookup against any actual
certification. Confirmed by reading `create_attestation`'s full
implementation (`node09_juridique.py:266-290`): it is a pure formatting
function over its inputs, no data access at all.

**7. Overlap**: PARTIAL/naming-collision with `notary` (both use the
word "attestation") but functionally the two do not overlap at all today
— one is a real proof mechanism, the other is unverified text formatting.

**8. Target primitive**: a **Technical Evidence Report**, generated from
FREKCORE's own already-verified records (`evidence_id`/`proof_id`/
`frek_id`/`object_id`/`credential_id`/`event_id` references) — never from
caller-supplied raw claims.

**9. Target module/protocol/profile/adapter**: a report-generation layer
sitting **above** `notary`/Proof Engine/Registry — consuming their
already-verified state, not a peer to them.

**10. Existing code reusable**: the PDF-generation code
(`frek/routes.py:get_certificat_pdf`, using `reportlab`) is real, working
document-generation infrastructure — reusable as the rendering layer once
fed verified data instead of raw lookup results. The doctrine text itself
(NEVER/ALWAYS lists, the 5 protection layers in `node09_juridique.py`) is
directly reusable as the report's disclaimer language.

**11. Historical code requiring rewrite**: `create_attestation`'s entire
body — it must look up and verify referenced evidence/proof/credential
IDs against FREKCORE's actual stored state before formatting anything,
which is a full rewrite, not a hardening pass.

**12. Compatibility obligations**: none identified.

**13. Storage requirement**: none new — reads existing `notary`/
`proof_engine`/`registry` state; the report itself may be worth
persisting for reproducibility (what did this report say when issued),
which is a document-store concern, not vector/graph.

**14/15. Vector/graph requirement**: NO.

**16/17. Authentication/authorization requirement**: who may request a
report about a given object needs a real answer (the object's holder?
anyone, since the underlying facts are meant to be publicly verifiable?)
— undefined historically, needs founder or evidence-based resolution.

**18. Privacy/consent requirement**: a report surfaces GPS/personal data
that may itself be holder-consented for other purposes but not
necessarily for inclusion in a shareable report — needs its own consent
check, not inherited automatically.

**19. Event emission**: report generation should itself be an audited
event (who requested a report about what, when) — currently none.

**20. Claim/evidence semantics**: this route is the **clearest possible
illustration** of D6's entire purpose. Today it takes a CLAIM (whatever
the caller says) and dresses it as if it were a VERIFIED fact, with
zero intermediate check. The rebuilt version must walk CLAIM → EVIDENCE
→ PROOF → VERIFIED explicitly, and the report must say, for each
assertion in it, which of those levels it actually reached.

**21. Proof requirements**: report must cite the actual `ProofState` of
each fact it includes — never uniformly "this fact is proven."

**22. Audit requirements**: report generation logged via `audit_trail`.

**23. Offline semantics**: not applicable — a report is inherently an
online lookup + render operation.

**24. Replay/idempotency**: not applicable in the same sense; re-issuing
a report for the same object at a later time is expected to legitimately
differ if underlying state changed (e.g. proof upgraded from
`OPENTIMESTAMPS_PROOF` to `EXTERNAL_ANCHOR_PROOF`).

**25. Migration needs**: none.

**26. SDK/API impact**: net-new.

**27. Security risks**: today, none *cryptographic* (it stores nothing to
attack) — the real risk is **reputational/legal**: the route can dress
fabricated data in FREKCORE's own doctrine language, undermining the
doctrine it claims to embody.

**28. Semantic-loss risk**: HIGH — this is the one capability where
getting the reconciliation wrong doesn't just lose a feature, it actively
damages trust in every other FREKCORE guarantee, because it borrows their
vocabulary.

**29. Test strategy**: tests must assert that the report generator
*refuses* to include any assertion it cannot trace to an actual
FREKCORE record, and that its `ProofState` labeling per assertion is
accurate against fixtures.

**30. Final technical disposition**: **ABSORB the intent + LEGAL
HARDENING** — the concept (a readable technical-evidence document,
grounded in FREKCORE's own careful legal doctrine) survives; the
implementation is fully rebuilt on top of already-verified data.
`SUPERSEDE_IMPLEMENTATION` is deliberately not used here even though
`notary` is the modern, better mechanism, because the *target* capability
(a formatted, human-readable report) is not something `notary` itself
produces — `notary` supplies the verified facts a rebuilt D5 would
report on. This is "reuse the trust primitive, keep the presentation
concept" — not a straight supersession.

#### Per-route table

| # | Method/Path | Source (file:function) | Disposition |
|---|---|---|---|
| D5.1 | `POST /api/frek/advanced/juridique/attestation` | `routes_advanced.py:create_attestation` → `node09.create_attestation` | ABSORB INTENT + LEGAL HARDENING (full rewrite over verified data) |

**FUTURE ECOSYSTEM INTEGRATION IMPACT (D5)**

1. *Exposes*: a report-generation endpoint over already-verified
   FREKCORE state.
2. *Remains inside FREKCORE*: the doctrine language (NEVER/ALWAYS
   claims) and the mapping from internal `ProofState` to a plain-language
   confidence statement.
3. *Protocol/profile/adapter*: report *templates* (per audience — a
   partner's legal team vs. a public verifier) are adapters over one core
   evidence-lookup mechanism.
4. *Consuming applications*: any partner needing to present FREKCORE's
   guarantees externally (KORA, LabelOS, an institutional partner,
   auditors) — a genuinely universal need, unlike D1/D3-B.
5. *Must NOT be hardcoded*: jurisdiction-specific legal conclusions
   (the historical doctrine's own discipline already models this
   correctly — "technical fact, never a legal right").
6. *Likely SDK/API contract*: `GET /object/{id}/evidence-report`
   (or `/verification-report`).
7. *Third-party consumable*: YES — arguably the single most
   externally-useful of the five capabilities, since every consumer
   eventually needs to *show* someone else what FREKCORE guarantees.
8. *Works without CVLN Intelligence OS*: YES.
9. *Works offline/degraded*: NO (inherently an online lookup+render).

---

## E. Canonical truth semantics

Per the founder's evolved model:

```
IDENTITY → AUTHORITY → OBJECT → EVENT → CLAIM/ASSERTION
→ PROVENANCE → EVIDENCE → PROOF → VERIFICATION
```

Audited against what already exists (per the explicit instruction: audit
before creating new classes/enums):

| Concept | Existing primitive | Status |
|---|---|---|
| IDENTITY | `identity_engine`, `frek_v1`, `did/` | EXISTS (3 systems, reconciliation ongoing per C1) |
| AUTHORITY | `permissions/models.py`'s `Role`/`Scope`/`Action` | EXISTS, not wired to any route yet |
| OBJECT | `registry/` (namespaced objects), `.fk` (FREK Object) | EXISTS |
| EVENT | `eventbus/` (`EventEnvelope`, `build_X_event()`) | EXISTS |
| CLAIM/ASSERTION | **No dedicated primitive found.** `.fk`'s `based_on`, `frek_v1`'s stage transitions, and the historical D2/D5 routes all implicitly carry claims without a named "claim" object | **GAP** — this is the one genuinely new concept the evolved model requires |
| PROVENANCE | `.fk`'s `provenance.creation` layer, `based_on` | EXISTS, informally |
| EVIDENCE | Nothing named "evidence" today; closest is a `notary` block's `payload_data` | **GAP**, but adjacent to existing storage |
| PROOF | `proof_engine/models.py`'s `ProofState`/`ProofReceipt` | EXISTS, already a clean 6-level ladder |
| VERIFICATION | `did/vc.py`'s verify functions, `notary`'s `/chain/verify` | EXISTS, distributed across modules |

**Finding**: 7 of 9 concepts already exist under some name. The evolved
model's real, additive requirement is **CLAIM** and **EVIDENCE** as
first-class, explicitly-named things — not a wholesale new architecture.
This matches the founder's own instruction not to invent classes
reflexively: the gap is narrow and specific, not the whole model.

**PROV compatibility (Agent/Entity/Activity)**: a conceptual mapping,
recorded for future interoperability without renaming FREK's own
vocabulary:

| PROV-O | FREK vocabulary | Note |
|---|---|---|
| `prov:Agent` | Identity (person/org/device) | Direct match |
| `prov:Entity` | FREK Object | Direct match |
| `prov:Activity` | Event (GENESIS/WORKSHOP/CERTIFY/...) | Direct match |
| `prov:wasGeneratedBy` | D3-A `CREATED_BY`/`EMIS_A` | Direct match |
| `prov:wasDerivedFrom` | `.fk`'s `based_on`, D3-A `DERIVED_FROM` | Direct match |
| `prov:wasAttributedTo` | D3-A `CREATED_BY`/`OWNED_BY` | Direct match |

No FREK term needs renaming to achieve this — the mapping is available
if/when external interoperability is pursued, not required now.

---

## F. Fingerprint architecture

See D1 (§D) for the full analysis. Target shape:

```
AUDIO / SIGNAL
       |
       +----------------------+
       |                      |
       v                      v
Crypto Hash            Signal Fingerprint
(exact integrity,      (perceptual/signal binding,
 .fk/notary today)      NEW, D1)
       |                      |
       +----------+-----------+
                  |
             FREK OBJECT (.fk)
                  |
             Provenance (D3-A)
                  |
              Evidence (NEW, §E)
                  |
             Proof Engine (EXISTS)
                  |
             FREK-Chain / Notary (EXISTS)
                  |
          Timestamp / Anchor (EXISTS)
                  |
             Verification (EXISTS, distributed)
```

No property of the historical fingerprint algorithm (re-encoding
resistance, noise resistance, collision rate) is asserted as proven in
this document — see D1 point 29 and §Q for what validation work remains.

---

## G. Creative Lifecycle architecture

See D2 (§D). Target: Event+Claim records against a FREK Object, reusing
the existing GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY vocabulary
(already proven consistent with `frek_v1`), notarized via the existing
`notary.chain.append_block` extensibility point — no new storage engine,
no new stage vocabulary, no new state machine framework.

---

## H. Trust Graph vs. Cultural/Inference Graph

See D3 (§D) for the full split rationale. Key structural rule going
forward: **a relation's type determines which graph it belongs to, and a
relation never moves from D3-B to D3-A automatically** — a `SIMILAR_TO`
edge, however strong the computed similarity, is not promotable to a
trust relation without an actual attesting act (e.g. a human curator or
institution explicitly certifying the similarity, which would then create
a *separate* D3-A `CERTIFIED_BY` relation referencing the D3-B one as its
evidence — not a mutation of the D3-B edge itself).

---

## I. Offline/Transmission architecture

See D4 (§D). Core/adapter split diagram:

```
FREK TRANSPORT ENVELOPE (core)
  identity/issuer ref · evidence/proof refs · signature
  timestamp · sequence · counter · nonce
  replay protection · dedup key
  offline acceptance state · reconciliation state
        |
        +---------+---------+---------+---------+
        |         |         |         |         |
      NFC        BLE      WiFi       QR      Ultrasound   (adapters)
                                                  |
                                            Luciole/FAP
                                          (device attestation,
                                           reconciled separately,
                                           frek_v3/)
```

FAP is not duplicated: FAP answers "can this device be trusted and did it
sign this," D4's envelope answers "how does that signed thing travel and
get reconciled when connectivity returns." A FAP-signed evidence package
is one possible payload *inside* a D4 envelope, not a competing
mechanism.

---

## J. Watermark semantics

Per the founder's explicit instruction: **WATERMARK ≠ PROOF**.

```
WATERMARK (a locator/pointer, hidden in the signal)
   |
   v
EVIDENCE / OBJECT REFERENCE (what the watermark points to)
   |
   v
SIGNED / VERIFIED DATA (the actual proof, elsewhere)
   |
   v
FREKCORE VERIFICATION
```

No claim of inaudibility, robustness, or reliable decodability is made
for the historical ultrasonic watermark — `create_ultrasonic_watermark`
(`node07_transmission.py`) computes a struct-packed byte sequence with no
DSP encoding/decoding logic and no experimental validation anywhere in
this repository. This is recorded as an explicit gap (§T), not asserted
as a working capability.

---

## K. Technical Evidence Report / attestation architecture

See D5 (§D). The rebuilt flow, once built:

```
Report request: {evidence_id | proof_id | frek_id | object_id | credential_id | event_id}
        |
        v
Lookup against Registry / Notary / Proof Engine / Credentials (EXISTING, VERIFIED state only)
        |
        v
Per-assertion ProofState labeling (existing 6-level ladder)
        |
        v
Render: Technical Evidence Report / FREK Verification Report /
        FREK Technical Attestation / Verifiable Evidence Record
        (naming TBD at build time — avoid notarial/legal-status terms
         that overclaim, per the founder's explicit list)
```

The historical "Cultural Notary Tech" / "Intelligent Notarial Layer"
vocabulary is preserved as **architecture/history**, not as the label on
the public-facing document — the founder's own instruction distinguishes
preserving the vision from mislabeling the product.

**Anchoring provider transparency** (also raised under D5's doctrine):
the report must name its actual mechanism per fact —

```
ANCHORING / TIMESTAMP PROVIDERS (extensible registry)
  - FREK-Chain (local hash chain, EXISTS)
  - OTS (OpenTimestamps, EXISTS, network-blocked in this sandbox)
  - Bitcoin (via OTS upgrade, EXISTS)
  - external qualified provider (FUTURE, none integrated today)
```

No mechanism reports a status (e.g. "qualified timestamp") it does not
actually hold — this is already `proof_engine`'s own design discipline
(`ProofState` never claims more than the evidence supports); D5 must
inherit it rather than re-deciding it.

---

## L. Privacy / access implications

Cross-cutting across D1 (GPS/device_id), D3 (relationship visibility),
D4 (GPS in transmitted packets), D5 (report may surface consented data
for an unintended audience):

- **Reuse target**: `permissions/models.py`'s `ScopeType`
  (GLOBAL/ORGANIZATION/ENTITY/OBJECT) plus `identity_engine`'s
  `linked_objects` + `X-FREK-Session` holder-consent pattern (already
  built and tested this session for `fingerprint`/`geo`) are the two
  existing primitives capable of carrying every privacy requirement named
  above — no new parallel privacy system is justified by the evidence
  gathered in this pass.
- **Gap**: neither primitive today expresses "visible to this relation's
  two parties only" (D3's `PARTIES_ONLY` case) — this is a genuine,
  narrow extension to `ScopeType`, not a new system, if the technical
  reconciliation phase confirms the need.

---

## M. Storage strategy

Per the founder's explicit instruction: **no storage technology decision
is forced here.** What the evidence in §D actually shows, capability by
capability:

| Capability | Storage shape needed | Forced technology? |
|---|---|---|
| Identity/Object (existing) | structured/document | NO change — MongoDB, as today |
| Event/Lifecycle (D2) | append/event log | NO change — `notary.chain.append_block` already serves this |
| Proof/Audit (existing) | append-only, tamper-evident | NO change — `notary`/`audit_trail` already serve this |
| D3 Graph | relationship/query storage | **Genuinely different shape** — a document store can technically hold edges, but efficient path/neighbor queries (D3.4, D3.7) are what graph-shaped storage or a graph-query layer over the existing store is *for*. Not decided here — flagged as a real technical-reconciliation item (§T), not defaulted to either MongoDB or PostgreSQL |
| D1 Fingerprint vectors | vector/similarity search | **Genuinely different shape** — same open question as D3; MongoDB's own vector-search capability (if evidenced as sufficient) vs. a dedicated vector store is a technical-reconciliation item, not decided here |
| D4 Offline queue | local queue / log / sync state | NO forced technology — likely device-local storage (mobile app's own store) plus a small server-side reconciliation log; not a new central database concern |

**Explicit conclusion**: the historical PostgreSQL+pgvector choice is
retired as a *forced* technology (per the founder's instruction), but
D1/D3's underlying storage-shape needs (vector similarity, graph query)
are real and were not invented by the historical prototype — they are
inherent to what those two capabilities do. The technical-reconciliation
phase must evaluate options against FREKCORE's actual current storage
(MongoDB's vector-search and `$graphLookup` capabilities specifically)
before assuming a new engine is required at all.

---

## N. Existing-component reuse map

Consolidated from every "existing code reusable" / "reuse" point in §D:

| Component | Reused by | How |
|---|---|---|
| `notary.chain.append_block` | D1, D2, D3, D5 | Generic, schema-free durable append point — already the session's established pattern for every new payload type |
| `proof_engine.ProofState` ladder | D1, D2, D3, D5 | Unmodified reuse — the "how strong is this proof" axis already exists correctly |
| `permissions.ScopeType` | D3, L | Reused for relation/report visibility instead of a new visibility enum |
| `identity_engine`'s `linked_objects` + `X-FREK-Session` | D1, D3, L | Reused holder-consent pattern (already proven for `fingerprint`/`geo`) |
| `eventbus/producers.py` pattern | D1, D2, D3, D4 | `build_X_event()` → `EventEnvelope`, same shape as every existing producer |
| `audit_trail`'s category scheme | D1, D2, D3, D4, D5 | Reuse existing categories where they fit; new category only if evidence justifies (technical-reconciliation item) |
| `frek_v1.STAGE_ORDER` vocabulary | D2 | Directly reused, already identical to the historical D2 vocabulary |
| `node01_extraction.py`'s DSP pipeline | D1 | Real, storage-independent extraction code, directly reusable |
| `node06_reseau.py`'s 17-relation taxonomy | D3 | Reused as seed vocabulary for D3-A/D3-B predicates |
| `node07_transmission.py`'s packet wire format + protocol enum | D4 | Reused as envelope/adapter-registry starting point |
| `.fk`'s `intelligence/` layer (reserved, empty) | D1 | Natural home for fingerprint output once FREKANSLA/D1 exists |
| `.fk`'s `based_on` field | D3-A | One existing, informal case of `DERIVED_FROM` |
| FAP / `frek_v3/reference_verifier` (counter/nonce replay) | D4 | Reused replay-protection concept, not a new mechanism |
| `reportlab` PDF generation (`frek/routes.py`) | D5 | Reused rendering layer |

Nothing in §D proposes a new component without first checking this list.

---

## O. Standards / interoperability mapping

Covered in §E (PROV-O mapping). No additional standard was found with
evidence of a concrete need beyond that — W3C PROV is the one directly
relevant to D2/D3's Agent/Entity/Activity shape and is already
substantially compatible without renaming FREK vocabulary.

---

## P. Security requirements

Consolidated from §D's "security risks" points, ranked by what §D found:

1. **D3's read exposure** (7 unauthenticated routes surfacing relational
   data, including location) is the most acute — a *read*-side privacy
   gap on data that may already be sensitive for unrelated reasons.
2. **D1's write exposure** (unauthenticated certify, 100MB/call, no rate
   limit) is a real DoS surface independent of the identity questions.
3. **D2's write exposure** (unauthenticated GENESIS/WORKSHOP, no
   ownership check on `pre_id`) allows fabricating entries against
   another actor's declared work today.
4. **D4's unsigned envelope** (no signature, no replay protection) means
   a captured/replayed packet cannot be distinguished from a fresh one.
5. **D5's overclaim risk** is not a cryptographic vulnerability but a
   trust/reputational one — formatting unverified data in doctrine
   language.

None of these are fixed in this pass (no code changed) — they are the
concrete "what HARDEN means" list for whichever technical-reconciliation
items get picked up first.

---

## Q. Migration / compatibility strategy

- **No durable historical data exists to migrate** for any of the 5
  capabilities — confirmed repeatedly in §D (everything is in-process
  memory, wiped every restart, in every environment this session has run
  in).
- **No confirmed external caller** of any of the 19 routes was found
  (`memory/INVENTORY.md`'s "current production core" list, re-checked
  this pass, does not name `backend/frek/`) — so no backward-compatibility
  obligation is currently evidenced. If the founder knows of a live
  integration this document does not, that changes §D's disposition for
  the affected routes specifically.
- **New source located this pass**: `memory/assurance_package_v1.0/`
  (10 documents: architecture overview, security model, proof-of-existence
  audit, performance audit, resilience audit, field-test template,
  business model, external review, version history, hash registry) was
  not previously cross-referenced anywhere in `reports/`/`docs/` before
  this pass. `09_Version_History.md` supplied D2's historical-origin
  evidence (§D). The other 9 documents were not read in full during this
  pass (out of scope for this specific founder request — this reconciliation
  targets the 19 routes/5 capabilities, not a second exhaustive
  documentation sweep) and are flagged in §T as a real, separate follow-up
  item, since `03_Proof_of_Existence_Audit.md`, `04_Performance_Audit.md`,
  and `05_Resilience_Audit.md` in particular may carry further
  reconcilable evidence given `09_Version_History.md`'s own account that
  they cover "Sprint E/F/G" — the same historical audit cycle this
  session's earlier resilience-fix work (P1 fixes) already partially
  drew from via `memory/RESILIENCE_REPORT_v1.0.md`, suggesting overlap or
  a more complete source worth checking before assuming the earlier pass's
  4-item P1 list was exhaustive.

---

## R. Test strategy

Per capability, from §D's point 29:

- **D1**: golden-vector-style tests (fixed input → expected fingerprint),
  plus measured (not asserted) robustness under defined transformations,
  same evidentiary bar as FAP's 16 golden vectors.
- **D2**: stage-ordering invariant tests, idempotency-key enforcement
  tests.
- **D3**: D3-A/D3-B separation-holds tests, visibility-scoping-enforced
  tests.
- **D4**: envelope signature/replay/reconciliation-state tests, runnable
  without real transport hardware (reference-implementation-first, same
  discipline as FAP).
- **D5**: report-generator refuses unverifiable assertions; per-assertion
  `ProofState` labeling matches fixtures.

All of the above are **not implemented in this pass** — recorded here as
the test strategy a future implementation pass must follow, per the
"documentation only" scope of this mission.

---

## S. Semantic-loss analysis

Consolidated from §D's point 28, ranked by risk if the reconciliation is
done carelessly:

1. **D5** (HIGH) — reputational: mislabeling unverified data as doctrine-
   backed damages trust in every other FREKCORE guarantee.
2. **D3** (HIGH) — conceptual: merging Trust and Cultural/Inferred graphs
   removes the one distinction that makes D3-A trustworthy at all.
3. **D1** (HIGH) — conceptual: re-conflating Signal Fingerprint with
   FREK-ID recreates the exact historical overload this reconciliation
   exists to resolve.
4. **D2** (HIGH, narrower) — the CLAIM≠PROOF confusion specifically, if
   GENESIS is ever presented as legal proof of authorship.
5. **D4** (MEDIUM) — building transport adapters before the envelope's
   trust semantics are solid would lock in a wrong contract broadly.

---

## T. Ordered implementation plan (evaluated, not yet started)

Founder's preferred sequencing (§ "IMPLEMENTATION PLAN") checked against
this pass's dependency evidence — **no reordering needed**, the proposed
sequence matches what §D independently found:

0. **Evidence semantics foundation (D6) — DONE (2026-09-01)** —
   CLAIM/EVIDENCE as first-class concepts (§E's identified gap) now exist
   (`backend/proof_engine/evidence_semantics.py`, 24 tests, 100% coverage
   on the new file) so D1/D2/D3/D5 have somewhere correct to attach their
   assertions once each is separately authorized.
1. **Canonical bindings/object model — DONE (2026-09-01)** — realized as
   `backend/content_binding/models.py:ContentBinding`, a standalone
   record in its own `db.content_bindings` collection, referencing an
   existing `.fk` object's `frek_id` — not the illustrative
   `content_bindings[]` array-embedded-in-the-object shape originally
   sketched in §D1 point 8. Considered and rejected: populating `.fk`'s
   own `media.items[].sha256` (exact-hash axis, already exists) and
   `intelligence.fingerprints` (signal axis, already reserved for
   FREKANSLA per `fk/models.py`'s own docstring) directly — that would
   require reopening `.fk`'s already-signed `ProofLayer` (its
   `root_hash` covers every layer including `intelligence`), a materially
   more invasive change to a working, tested, production path than this
   state's scope justified. The standalone-record design keeps both axes
   just as structurally distinct, at the cost of one extra lookup instead
   of an inline field — a real, disclosed tradeoff, not an oversight.
2. **Fingerprint integration (D1) — DONE (2026-09-01)** — see the
   2026-09-01 D1 update above and `docs/decisions/0004-...`.
3. **Creative Lifecycle (D2) — DONE (2026-09-02)** — see the 2026-09-02
   D2 update above and `docs/decisions/0005-...`.
4. **Relationship/provenance graph (D3) — DONE (2026-09-02)** — see the
   2026-09-02 D3 update above and `docs/decisions/0006-...`.
5. **Offline transport envelope + sync (D4) — DONE (2026-09-02)** — see
   the 2026-09-02 D4 update above and `docs/decisions/0007-...`.
6. **Technical evidence report (D5) — DONE (2026-09-02)** — see the
   2026-09-02 D5 update above and `docs/decisions/0008-...`. Depended on
   everything above existing in verifiable form (it reports on them) —
   correctly last among the five capabilities, and it is a pure consumer
   of D1–D4/D6, never a sixth independent truth source.
7. **DONE (2026-09-02) — Compatibility adapters for historical routes
   (STATE_6)** — see the 2026-09-02 STATE_6 update above and `docs/
   architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`.
8. **Migration/persistence** — confirmed near-empty scope by §Q (nothing
   durable to migrate); mostly a "pick and wire the actual storage engine"
   step per §M's still-open D1/D3 technical question.
9. **DONE (2026-09-03) — SDK integration (STATE_7)** — see the
   2026-09-03 STATE_7 update above and `docs/architecture/
   FREKCORE_SDK_CONTRACT_V1.md`. Both SDKs now cover every D1–D5
   capability, lean-wrapped.
10. **DONE (2026-09-03) — Regression/evidence tests, full cross-module
    pass (STATE_8)** — per §R, written alongside each capability
    throughout D1–D5/STATE_6/STATE_7, then validated as one integrated
    system this state: see the 2026-09-03 STATE_8 update above and
    `docs/validation/FREKCORE_STATE8_VALIDATION_RESULTS.md`
    (`backend/tests/test_api_contract.py` remains this step's own
    STATE_7 golden-snapshot contribution, re-run green; `backend/tests/
    test_state8_validation.py` and the 7 new delegated-authority
    full-chain tests in `tests/test_permissions.py` are STATE_8's own).
11. **Freeze reassessment** — after 0–10 (now all done); this document's
    own verdict (§U, and `reports/21_FREEZE_ASSESSMENT.md`) is **NOT
    READY FOR FINAL FREEZE — STATE_9 FINAL HISTORICAL ARCHITECTURAL
    RECONCILIATION REQUIRED**, per the founder's own explicit framing
    that STATE_8 completion does not by itself authorize final freeze.

**This document did not start step 0 when first written; steps 0–10 (D6,
the canonical bindings model, D1, D2, D3, D4, D5, Historical
Compatibility Reconciliation, API/SDK Contract Stabilization, and
Regression/Evidence/Migration Validation) have since been executed**,
each under the founder's explicit, separate authorization
(`EXECUTE_D6=TRUE`, then `EXECUTE_D1=TRUE`, then `EXECUTE_D2=TRUE`, then
`EXECUTE_D3=TRUE`, then `EXECUTE_D4=TRUE`, then `EXECUTE_D5=TRUE`, then
`EXECUTE_STATE_6=TRUE`, then `EXECUTE_STATE_7=TRUE`, then
`EXECUTE_STATE_8=TRUE`) — see the 2026-09-01/2026-09-03 updates at the
top of this document. Step 11 (freeze reassessment, in the sense of a
founder-authorized final freeze) is the founder's own next-named state,
`STATE_9_FINAL_HISTORICAL_ARCHITECTURAL_RECONCILIATION` — not started,
requiring its own separate founder authorization before execution —
`EXECUTE_STATE_9=FALSE` as of this update.

---

## U. Final freeze impact

The `FREEZE READY` verdict recorded in `reports/21_FREEZE_ASSESSMENT.md`
(HEAD `ce12398`) was correct under its own scope: at that point, the 19
`backend/frek/` routes were `NEEDS_FOUNDER_DECISION` — genuinely
undecidable without founder input, and therefore correctly excluded from
"what remains, is founder- or environment-blocked."

The founder has now made that decision: all five underlying capabilities
are **required**, not optional. This changes the target scope of "what
FREKCORE must contain before freeze" through legitimate founder
governance — it does not mean the earlier verdict was wrong when it was
made. `reports/21_FREEZE_ASSESSMENT.md` is updated accordingly (§ below)
to `NOT READY FOR FINAL FREEZE — D1–D6 RECONCILIATION REQUIRED`, with this
document as the technical reconciliation record and §T as the ordered
path back toward a freeze verdict.

---

## Reuse audit — explicit confirmation

Per the mission's "REUSE BEFORE BUILD" instruction, every component named
in it was checked before any target primitive was proposed in §D–§K:

FREK-ID (identity_engine, frek_v1) — checked, referenced in D1/D2.
Registry — checked, referenced in D3/E. `.fk`/FREK Object Model —
checked, referenced in D1/D3/F. Credentials/VC (`did/vc.py`) — checked,
referenced in D4/E. FREK-Chain/Notary — checked, referenced throughout
(the single most-reused component). Proof Engine — checked, referenced
throughout (`ProofState` ladder reused unmodified). Permission Engine —
checked, referenced in D3/L (`ScopeType` reused instead of a new
visibility enum). Audit Trail — checked, referenced throughout (existing
categories reused). Event Bus — checked, referenced throughout
(`build_X_event()` pattern reused). Storage abstraction
(`backend/storage/`) — checked; not directly applicable (file/blob
storage, not vector/graph/document — noted, not force-fit). FAP /
`frek_v3` — checked, referenced in D1/D4 (replay protection, device
attestation boundary). Luciole documented architecture — checked,
referenced in D2/D4 (stage vocabulary, hardware roadmap). SDKs — checked,
confirmed zero current `backend/frek/` wrapping (§D's repeated finding).
Resilience/offline work, chain watchdog — checked; the watchdog's
periodic-integrity-check pattern is a plausible reuse candidate for
verifying D1/D3's eventual storage stays consistent, flagged as a
technical-reconciliation item rather than assumed.
