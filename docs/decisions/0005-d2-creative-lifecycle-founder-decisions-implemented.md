# 0005 — Founder Decision D2: Creative Lifecycle (APPROVED, IMPLEMENTED)

Status: **DECIDED, IMPLEMENTED**. Records the founder's D2 decision from
`FREKCORE_EXECUTION_PROTOCOL_V1` §STATE_2 (2026-09-02) and how it was
carried out. Background: `reports/FREKCORE_HISTORICAL_CAPABILITY_
RECONCILIATION.md` §D "D2 — Creative Lifecycle" (the reconciliation pass
that first surfaced D2 as one of 5 historical capabilities requiring a
founder decision, out of the 19 `backend/frek/` routes).

## Founder decision, verbatim (paraphrased from the execution protocol)

**D2 = PRESERVE + ABSORB.** The historical GENESIS/WORKSHOP/METAMORPHOSE/
EMISSION/LEGACY creative-provenance vocabulary
(`backend/frek/nodes/node03_cycle.py`) must be preserved verbatim, never
renamed. It must be structurally separated from identity:

    CREATIVE_LIFECYCLE_EQUALS_IDENTITY_LIFECYCLE = FALSE
    GENESIS_EQUALS_LEGAL_AUTHORSHIP = FALSE
    GENESIS_EQUALS_LEGAL_OWNERSHIP = FALSE
    GENESIS_EQUALS_ABSOLUTE_PRIORITY = FALSE

A collision with `frek_v1`'s own use of the same vocabulary (participant/
badge lifecycle) had to be **verified, not assumed**, and the two kept
structurally separate if confirmed. The lifecycle's real state-machine
shape (LINEAR / EVENT_BASED / HYBRID) had to be **derived from the
historical code, not invented**. D6 (Claim/Evidence) and D1 (signal
fingerprint extraction) had to be reused, never reimplemented
(`D2_CONSUMES_D1=TRUE`, `D2_REIMPLEMENTS_D1=FALSE`). D1 must remain
`D1_VERIFIED=PARTIAL` unless D2 genuinely produces new D1 evidence — it
does not, and this ADR does not claim otherwise.

## Collision verification (evidence, not assumption)

Confirmed by direct code reading: `frek_v1/models.py:FrekStage` +
`STAGE_ORDER` already use the identical 5-word vocabulary for a
**participant/badge lifecycle** — `frek_v1/stages.py`'s
`POST /identity/{frek_id}/stage` writes `db.frek_stages`, notarized as
`payload_type="stage_transition"`, and `backend/badges/routes.py` writes a
badge's `current_stage: "GENESIS"` directly. This is a real, in-production
collision on vocabulary, not on subject or mechanism: a badge's GENESIS
and a creative object's GENESIS describe different kinds of subject.
`backend/creative_lifecycle/` is therefore a **fully separate system**:
own collection (`db.creative_lifecycle_events`, never `db.frek_stages`),
own notarization `payload_type` (`"creative_lifecycle"`, never
`"stage_transition"`), own authority model (`identity_engine` holder
sessions, never `frek_v1` OAuth2 clients). Same vocabulary, deliberately
not merged — see `creative_lifecycle/models.py`'s module docstring for the
full record.

## State-machine shape: HYBRID (derived, not invented)

Read directly from `frek/nodes/node03_cycle.py`'s own guard logic:

- WORKSHOP is repeatable, but guarded: only allowed while current stage is
  GENESIS or WORKSHOP itself (`node03_cycle.py:150-151`).
- METAMORPHOSE has **no stage guard at all** — callable as long as the
  `pre_id` exists (`submit_final()` checked directly: no stage check).
  Preserved deliberately, not tightened.
- EMISSION is **strictly guarded**: only allowed when the *current* stage
  is exactly METAMORPHOSE (`node03_cycle.py:262-263`), re-checked fresh
  each call — not "was METAMORPHOSE ever reached".
- LEGACY requires the parent to already carry an assigned `frek_id_final`
  (i.e. to have reached EMISSION at some point), no further stage check.

Because METAMORPHOSE is unguarded and EMISSION only checks the *current*
stage, the real historical machine allows
`GENESIS → WORKSHOP → METAMORPHOSE → EMISSION → METAMORPHOSE → EMISSION →
LEGACY`: re-entering METAMORPHOSE after EMISSION makes a second, genuinely
new EMISSION callable again. This is `LIFECYCLE_MODEL = HYBRID` (not
`LINEAR`, not free-form `EVENT_BASED`) and is preserved as a real,
supported capability, not treated as a bug — see
`creative_lifecycle/service.py`'s guard functions and
`docs: models.py`'s module docstring for the full finding.

A real defect in an early draft was caught by this state's own test suite,
not assumed away: the EMISSION endpoint's first idempotency check scanned
the *entire* event history for a prior EMISSION with the same
`fk_frek_id`, which silently defeated the HYBRID re-entry flow above (a
second, legitimate EMISSION after re-entering METAMORPHOSE was wrongly
returned as a dedup of the first). Fixed by removing that history-wide
scan: the `can_emit` guard already structurally prevents an illegitimate
back-to-back double-emission (a second call without an intervening
METAMORPHOSE finds the current stage is EMISSION and gets a 409), so no
additional idempotency check is needed at that step. See
`creative_lifecycle/routes.py:emit`'s comment and
`tests/test_creative_lifecycle_unit.py::TestHybridReentry` /
`test_second_emission_after_reentry_is_a_new_event_not_a_dedup`.

## What was implemented

**`backend/creative_lifecycle/`** (new module):

- `models.py` — `LifecycleStage` (the historical 5-word enum, verbatim),
  `STAGE_ORDER`, `ContentBindingRef` (lightweight exact-hash + signal-
  fingerprint reference for pre-`.fk` stages), `LifecycleEvent` (composed
  of real D6 `Claim`/`Evidence` primitives, never reimplemented —
  `event_id`, `pre_id`, `stage`, `sequence`, `actor_id`, `authority`,
  `claim`, `evidence`, `content_binding_ref`, `fk_frek_id`, `data`,
  `proof_state`), `LifecycleSummary` (read-model).
- `service.py` — pure, dependency-free guard functions
  (`can_start_workshop`, `can_metamorphose`, `can_emit`,
  `can_declare_legacy`, `latest_stage`) encoding exactly the HYBRID model
  above, plus `coherence_score`/`cosine_similarity` ported from
  `node03_cycle.py:_calculate_coherence`.
- `routes.py` — `POST /api/v1/creative-lifecycle/genesis` (mints a
  provisional `pre_id`, never a `frek_id`), `POST /{pre_id}/workshop`,
  `POST /{pre_id}/metamorphose`, `POST /{pre_id}/emission` (binds to an
  existing `.fk` object — never mints one), `POST /{pre_id}/legacy`,
  `GET /{pre_id}` (full event history, public).

**Object identity discipline**: EMISSION requires an existing `.fk`
Cultural Object (`db.fk_objects`) and only ever *references* its
`frek_id` — this module never mints a FREK Object identity itself,
preserving `FREK_ID_SEPARATED` semantics exactly like D1.

**Authority**: GENESIS — any authenticated `identity_engine` holder or
admin (self-attested, matching the historical "l'artiste déclare"
framing). Subsequent stages — the GENESIS actor (self-match) or admin
only; broader multi-contributor authorization (`CONTRIBUTION != OWNERSHIP`)
is real-world plausible but explicitly out of this state's scope (D3's
relationship-graph territory).

**Persistence**: plain MongoDB (`db.creative_lifecycle_events`), no new
database technology. Event-sourced: the current stage is always derived
from the latest event (`service.latest_stage`), never a separately
mutable field — history is never overwritten or destroyed.

**D1 reuse**: `_compute_binding_ref` calls
`content_binding.extraction.exact_hash` / `compute_signal_fingerprint`
directly — the DSP pipeline is never reimplemented
(`D2_CONSUMES_D1=TRUE`, confirmed structurally by
`test_no_dsp_reimplementation_in_creative_lifecycle_source`, not just
claimed in a comment).

**Notarization/events/audit**: best-effort notarization via
`notary.service.notarize_event(payload_type="creative_lifecycle", ...)`;
a single unified event `creative_lifecycle.recorded`
(`eventbus/producers.py:build_creative_lifecycle_event`, `payload.stage`
distinguishes the five stages), registered in
`registry/events/event_registry.json`, subscribed into the Audit Trail
(`server.py`'s `_AUDIT_TRAIL_EVENT_TYPES`) alongside every other real
producer.

**Security**: authenticated (holder-or-admin, no unauthenticated write
path at all, unlike the historical GENESIS/WORKSHOP routes), payload
bounded at 25MB, rate-limited (`creative_lifecycle_write`, 60/hour by
default, shared across all five mutating endpoints), idempotent on
WORKSHOP (identical content dedups) and structurally protected on
EMISSION (see the HYBRID re-entry finding above).

## What was explicitly NOT done (per the founder's own prohibitions)

- **`backend/frek/routes.py`'s `POST /genesis`, `POST /workshop` were not
  touched.** Zero lines changed — confirmed by
  `test_historical_frek_routes_module_not_imported_by_creative_lifecycle`.
  They remain live exactly as before (in-memory, unauthenticated, minting
  their own `pre_id` counter).
- `frek_v1`'s participant/badge stage lifecycle (`db.frek_stages`,
  `badges/routes.py`) was not touched or merged with this module.
- No route deletion, no deprecation, no migration.
- D3 (Relationship/Provenance Graph), D4 (Offline Proof Transport), D5
  (Technical Evidence Attestation) were not started.
- No Production Readiness, Red/Blue/Purple, UI/UX, CVLN wiring, merge, or
  deploy.
- D1's own verification status is **not** silently upgraded by this
  state: `D1_VERIFIED` stays `PARTIAL` (per
  `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`) — D2 consumes D1's
  extraction functions but produces no new evidence about the signal
  algorithm's own robustness.

## Verification

- `backend/tests/test_creative_lifecycle_unit.py` (40 tests) — mongomock +
  monkeypatched D1 extraction, no live server/Mongo/librosa needed.
  Covers: creative≠identity lifecycle, GENESIS non-overclaim, canonical
  `.fk` object binding, actor/authority enforcement, unauthorized
  rejection, persistence, history never destroyed, the HYBRID re-entry
  flow, invalid-transition rejection (409s), idempotency, D6 reuse
  (structural round-trip through the real `Claim`/`Evidence` types), D1
  reuse (not recompute, checked structurally), event emission, historical
  vocabulary preserved, participant/badge separation, historical routes
  unchanged.
- `backend/tests/test_eventbus.py` and `test_audit_trail.py` extended with
  the new producer's contract and audit-trail wiring (now eight real
  producers, up from seven after D1).
- Full unit suite: 272 passed (was 230 after D1), 0 failed. Coverage gate
  (registry/eventbus/permissions/audit_trail/proof_engine/storage/
  observability) re-verified: 96.67% against 90%.
- flake8/black on `creative_lifecycle/` and its tests: clean. mypy's
  `Optional[db]`/pydantic-signature findings there match the exact
  pre-existing pattern already present in `content_binding/` and
  `security/policies.py` (confirmed via diff), not a regression, and
  `creative_lifecycle/` is outside CI's blocking mypy `MODULES` scope.

## What this ADR does not do

It does not decide `frek_v1`'s participant/badge lifecycle's own eventual
fate — that system is untouched and out of scope here. It does not extend
D1's own signal-algorithm validation (`D1_VERIFIED` stays `PARTIAL`). It
does not build the relationship/provenance graph LEGACY's `child_pre_id`/
`child_fk_frek_id` references imply — those stay bare references this
state, consumable by a future, separately-authorized D3. It does not
start D3–D5.
