# 0008 — Founder Decision D5: Technical Evidence Report / Juridical Framing (APPROVED, IMPLEMENTED)

Status: **DECIDED, IMPLEMENTED**. Records the founder's D5 decision from
`FREKCORE_EXECUTION_PROTOCOL_V1` §STATE_5 (2026-09-02) and how it was
carried out. Background: `reports/FREKCORE_HISTORICAL_CAPABILITY_
RECONCILIATION.md` §D "D5 — Technical Evidence Report / Juridical
Framing".

## Founder decision, verbatim (paraphrased from the execution protocol)

**D5 = PRESERVE_INTENT_ABSORB_LEGAL_HARDEN.** The historical "notaire de
fait, jamais juge de droit" (notary of fact, never judge of law)
principle (`backend/frek/nodes/node09_juridique.py`) must be preserved as
*intent*, but its blind-trust *behavior* must not be — a report must
never be a notarial act, legal judgment, copyright registration, legal
authorship/ownership proof, or qualified eIDAS timestamp; cryptographic
validity must never be conflated with legal validity, current authority,
or real-world claim truth. D5 is purely a **consumer** of D1–D4 and D6 —
it must never create new truth, only explain existing canonical truth,
resolved only from a resource ID reference, never from arbitrary
caller-supplied "facts". The 11 founder FALSE-equations (reproduced in
`technical_evidence_report/models.py`'s own module docstring) had to be
enforced structurally, not just documented; a bounded list of report
subject types had to be respected without inventing new ones; sections
had to be labeled CLAIMED/OBSERVED/ATTESTED/COMPUTED/INFERRED/EVIDENCE/
PROOF/VERIFIED/UNKNOWN/NOT_VERIFIED/LEGAL_CONCLUSION_NOT_MADE, never
flattened to a single "verified" boolean (an explicit D6 requirement);
public verification had to be possible without exposing authorization-
scoped disclosure content; the historical `/juridique/attestation` route
had to be preserved untouched this state.

## Historical discovery (evidence, not a prior summary)

Read directly from `backend/frek/routes_advanced.py`'s
`POST /api/frek/advanced/juridique/attestation` and its backing
`backend/frek/nodes/node09_juridique.py`:

- `AttestationRequest` takes `sha256_signal`, `vector_dimensions`,
  `artiste_id`, `timestamp_ms`, `gps_lat`, `gps_lon` **directly from the
  HTTP request body** — the route handler does no database read, has no
  auth dependency, and performs no lookup against any canonical FREKCORE
  state whatsoever.
- `Node09Juridique.create_attestation` is a pure string-formatting
  function over exactly those caller-supplied values — it never
  independently retrieves or verifies anything.
- `TechnicalAttestation.to_legal_text()` renders, verbatim: *"Ce fait est
  mathematiquement certain et temporellement irrefutable."* — precisely
  the class of unqualified overclaim (IRREFUTABLE wording, produced from
  unverified caller input) this state's mission brief names as the exact
  defect to never repeat. The founder's expected historical finding was
  confirmed from code, not assumed.
- The module's own *stated* framework (its `NEVER_STATEMENTS`/
  `ALWAYS_STATEMENTS` lists: never claims authorship, ownership,
  originality, rights, or legal registration) is real and largely
  correct — the defect is narrower than the intent. The *behavior* (blind
  trust of caller input, plus one overclaiming phrase) does not match the
  *stated* intent, which is exactly why the founder's disposition is
  PRESERVE_INTENT=TRUE, PRESERVE_BLIND_TRUST_BEHAVIOR=FALSE rather than a
  blanket rewrite or deletion.

## What was implemented

**`backend/technical_evidence_report/`** (new module):

- `models.py` — `ReportSubjectType` (the founder's own bounded list:
  FREK_IDENTITY, FREK_OBJECT, CONTENT_BINDING,
  CREATIVE_LIFECYCLE_HISTORY, RELATIONSHIP_RECORD, CREDENTIAL,
  EVIDENCE_RECORD, PROOF, OFFLINE_TRANSPORT_ENVELOPE,
  COMBINED_EVIDENCE_PACKAGE — reproduced exactly, none invented),
  `SectionKind` (the mission's own D6 sectioning vocabulary, no
  collapsing boolean), `FORBIDDEN_PHRASES` + `assert_no_forbidden_
  language` (a negation-aware, case-insensitive overclaim guard —
  positive assertions of a forbidden phrase are rejected, while the
  fixed `LEGAL_DISCLAIMER`'s own explicit negations of those same
  concepts, e.g. "It is NOT a notarial act", are allowed), `ReportSection`
  (kind/title/statements/data/`visibility: Scope`, statements/title
  validated against the guard at construction — a section literally
  cannot be built with an overclaim in it), `SourceReferences` (resource
  ID references only), `TechnicalEvidenceReport` (report_id,
  report_schema_version, generator_version, generated_at,
  verification_time, subject_type, subject_id, source_refs, sections,
  legal_disclaimer, report_hash, is_snapshot, requested_by,
  requested_authority).
- `canonical.py` — deterministic canonical JSON (the same formula
  independently kept in `fk/packager.py`, `notary/chain.py`, and
  `offline_transport/canonical.py`) and `compute_report_hash`, hashed
  over content fields only (never `verification_time`, so re-verifying
  unchanged content does not change the hash; never `report_hash` itself,
  avoiding circularity).
- `service.py` — pure section builders (`build_identity_section`,
  `build_object_section`, `build_content_binding_section`,
  `build_creative_lifecycle_section`, `build_relationship_section`,
  `build_offline_transport_section`, `build_proof_section`,
  `build_credential_section`), each taking already-resolved plain data
  and encoding one D-state's own legal-hardening rule (see "Reuse
  discipline" below); `overall_caveat_section` (always appended last);
  `compose_report`; `can_read`/`redact_for_disclosure` (per-section
  visibility filtering, reusing `permissions.models.Scope`/`ScopeType`
  directly — the identical disclosed tradeoff D3 already made:
  `permissions.engine.decide()` is not wired, since no `RoleGrant`
  persistence exists anywhere in this codebase); `public_verification_
  view` (shape-only: section `kind`/`title`, never `statements`/`data`).
- `routes.py` — `POST /api/v1/reports/technical-evidence` (GENERATE:
  authenticated holder-or-admin, rate-limited, resolves
  `subject_type`+`subject_id` against `db.frek_persons`/`db.fk_objects`/
  `db.content_bindings`/`db.creative_lifecycle_events`/
  `db.relationships`/`db.transport_envelopes`/`db.notary_blocks`, never
  from the request body; persists an immutable snapshot; returns a
  disclosure-redacted view), `GET .../technical-evidence/{id}`
  (RETRIEVE: redacted per caller, 404 if nothing is visible — existence
  is not leaked beyond that), `GET .../technical-evidence/{id}/verify`
  (public, no session required, separately and more tightly rate-limited,
  returns `public_verification_view` plus a recomputed integrity-hash
  match).

## Reuse discipline (D1–D4/D6 consumed, never reimplemented)

- **D1**: `build_content_binding_section` renders `proof_state`/algorithm
  fields as-is and always states D1 validation is PARTIAL (per
  `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`) — never silently
  upgraded.
- **D2**: `build_creative_lifecycle_section` always pairs its factual
  stage-sequence statement with an explicit "not a legal determination of
  authorship, ownership, or priority" caveat.
- **D3**: `build_relationship_section` forces `kind=INFERRED` for any
  CULTURAL-layer relationship regardless of its own `status` field
  (structurally re-verified by test — even a CULTURAL relationship
  carrying `status="verified"` cannot yield `kind=VERIFIED` in the
  report). Only a TRUST-layer relationship with `status="verified"`
  reaches `kind=VERIFIED`.
- **D4**: `build_offline_transport_section` renders `sync_status=="synced"`
  as `kind=VERIFIED`, explicitly scoped in its own statement to
  "transport-level integrity and authority freshness for the envelope
  itself" — never a claim about the underlying subject's ownership or
  authorship. `LOCALLY_ACCEPTABLE` without `sync_status=="synced"` is
  rendered distinctly (OFFLINE_ACCEPTED != FINAL_RECONCILIATION,
  restated verbatim in the section's own statement).
- **D6**: every section's `kind` is chosen from the real `Claim.origin`/
  `Evidence.kind`/relationship `status`/transport `sync_status` values
  already on the record — no second, parallel classification is
  invented. `proof_state` rendering reuses `proof_engine.notary_adapter.
  proof_state_from_notary_block` directly against real
  `db.notary_blocks` documents, never reimplementing the proof-state
  ladder.

## Legal wording guard (the "LEGAL WORDING REGRESSION TESTS" mechanism)

`assert_no_forbidden_language` blocks (case-insensitive) IRREFUTABLE,
PROVES OWNERSHIP, PROVES AUTHORSHIP, OFFICIAL NOTARIAL ACT, QUALIFIED
EIDAS TIMESTAMP, GUARANTEED ORIGINAL, UNFORGEABLE, ABSOLUTE PROOF, and
their direct French equivalents (matching `node09_juridique.py`'s own
overclaim wording) — enforced as a pydantic field validator on
`ReportSection.statements`/`title`, so it is load-bearing at construction
time, not a decorative test-only check. It is negation-aware (a short
preceding window checked against markers like "not a"/"never a"/"n'est
pas") specifically so the fixed `LEGAL_DISCLAIMER` can explicitly name
and disclaim these same concepts ("It is NOT a notarial act... NOT a
qualified electronic timestamp...") without tripping its own guard —
verified by a dedicated test that the same phrase asserted *positively*
("This constitutes an official notarial act") is still rejected, so the
negation-awareness is not simply permissive. The exact historical
overclaim phrase found in `node09_juridique.py`'s `to_legal_text()` is
itself used as a regression fixture, confirming the guard would have
caught the historical defect.

## Disclosure (public verification vs. authorization-scoped content)

`ReportSection.visibility` reuses `permissions.models.Scope` **per
section**, not one report-level flag, so `PROOF_VISIBILITY !=
EVIDENCE_VISIBILITY`/`RELATIONSHIP_VISIBILITY != SUBJECT_METADATA_
VISIBILITY`/`OBJECT_PUBLIC != ALL_PROVENANCE_PUBLIC` are structurally
possible outcomes. `GET .../verify` is public and returns shape only
(section kind/title, never statements/data, never raw evidence,
relationship, or credential content) plus a recomputed integrity-hash
match — `VERIFICATION_MAY_BE_PUBLIC=TRUE` without
`DISCLOSURE_IS_AUTHORIZATION_SCOPED` being violated. `GET
.../technical-evidence/{id}` redacts per caller (`redact_for_disclosure`)
and returns 404 rather than an empty/partial body when nothing is
visible, matching D3's existing "404, not 403" privacy discipline.

## Canonical-input rule

`GenerateReportRequest` accepts exactly `subject_type` + `subject_id` —
verified by a test asserting its field set is exactly that pair, and by
an end-to-end test that stuffs extra arbitrary "facts" into the request
body and confirms none of them appear anywhere in the generated report.
An unresolvable reference returns 404, never a hollow report describing
nothing (`ARBITRARY_CALLER_SUPPLIED_FACTS_AS_CANONICAL_TRUTH=FALSE`,
fail-closed).

## What was explicitly NOT done (per the founder's own prohibitions)

- **`backend/frek/routes_advanced.py`'s `/juridique/attestation` route
  and `node09_juridique.py` were not touched.** Zero lines changed —
  confirmed by a static route-presence test and a static-import guard.
  `BACKEND_FREK_CHANGED=NO`.
- No PDF generator, no UI/UX rendering layer — the canonical structured
  `TechnicalEvidenceReport` model is the single source of truth; JSON is
  derived from it (`to_public_dict()`), nothing else was built.
- No new permission engine (`CREATE_REPORT_PERMISSION_SYSTEM=FALSE`) —
  `permissions.models.Scope`/`ScopeType` reused directly, same disclosed
  tradeoff as D3.
- No qualified eIDAS timestamp integration — `QUALIFIED_TIMESTAMP` is
  never asserted true anywhere in this module; no trust service provider
  is integrated.
- STATE_6 (Historical Compatibility Reconciliation) was not started, per
  the founder's own explicit `EXECUTE_STATE_6=FALSE` for this state. No
  Production Readiness, CVLN wiring, Red/Blue/Purple team, UI/UX, merge,
  or deploy.

## Verification

- `backend/tests/test_technical_evidence_report_unit.py` (46 tests) —
  mongomock, no live server/Mongo needed. Covers: historical route
  untouched, legal wording regression (forbidden phrases rejected,
  negation-aware disclaimer passes its own guard, negation-awareness
  does not defeat the guard, every built-in section builder's own output
  passes the guard), bounded subject types, canonical-input-only rule,
  fail-closed on unresolved references, authorization (generate requires
  holder/admin), D1/D2/D3/D4 reuse-discipline rules each individually
  tested, sectioning never flattened to a boolean, per-section
  disclosure filtering (stranger/owner/admin), end-to-end generate→get→
  verify, report-hash stability (reserialization-stable, independent of
  verification_time, changes with content), combined evidence package
  pulling across multiple D-states, rate-limit key registration, and
  eventbus/audit-trail wiring (event published even when notarization
  fails, never echoes section content).
- `backend/tests/test_eventbus.py` and `test_audit_trail.py` extended
  with the new producer's contract and audit-trail wiring (now eleven
  real producers, up from ten after D4).
- Full unit suite: 400 passed (was 352 after D4), 0 failed. Coverage gate
  (registry/eventbus/permissions/audit_trail/proof_engine/storage/
  observability) re-verified: 96.70% against 90%.
- flake8/black on `technical_evidence_report/` and its tests: clean.
  mypy's `Optional[db]` findings there match the exact pre-existing
  pattern already present in `content_binding/`, `creative_lifecycle/`,
  `relationship_graph/`, and `offline_transport/` (confirmed via diff),
  not a regression, and `technical_evidence_report/` is outside CI's
  blocking mypy `MODULES` scope.

## What this ADR does not do

It does not claim any generated report is a legal judgment, notarial
act, or qualified timestamp — every report carries the fixed
`LEGAL_DISCLAIMER` and a `LEGAL_CONCLUSION_NOT_MADE` section, always. It
does not claim real legal review occurred — this state is a technical/
software engineering pass, not a legal one; any future legal-language
sign-off is a separate, human decision outside this ADR's scope. It does
not decide the historical `/juridique/attestation` route's eventual fate
(compatibility endpoint vs. eventual deprecation) — that is part of the
founder's own explicitly-scheduled STATE_6 (Historical Compatibility
Reconciliation), not decided here. It does not start STATE_6.
