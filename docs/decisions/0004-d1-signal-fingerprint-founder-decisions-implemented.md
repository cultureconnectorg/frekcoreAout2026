# 0004 — Founder Decision D1: Signal Fingerprint / Content Binding (APPROVED, IMPLEMENTED)

Status: **DECIDED, IMPLEMENTED**. Records the founder's D1 decision from
`FREKCORE_EXECUTION_PROTOCOL_V1` §STATE_1 (2026-09-01) and how it was
carried out. Background: `reports/FREKCORE_HISTORICAL_CAPABILITY_
RECONCILIATION.md` §D "D1 — Signal / Audio Fingerprint" (the reconciliation
pass that first surfaced D1 as one of 5 historical capabilities requiring
a founder decision, out of the 19 `backend/frek/` routes).

## Founder decision, verbatim (paraphrased from the execution protocol)

**D1 = PRESERVE + VALIDATE + HARDEN + ABSORB.** The historical audio-
fingerprint capability (`backend/frek/nodes/node01_extraction.py`'s real
528-dimension 6-algorithm extraction pipeline) must be preserved. It must
not be treated as validated merely because historical code exists. It
must be structurally separated from FREK-ID:

    FREK_ID_EQUALS_SIGNAL_FINGERPRINT = FALSE
    OBJECT_IDENTITY_EQUALS_CONTENT_BINDING = FALSE
    CRYPTOGRAPHIC_HASH_EQUALS_SIGNAL_FINGERPRINT = FALSE

Target shape: `FREK_OBJECT.content_bindings[]`, each binding carrying its
own algorithm, algorithm_version, and evidence/provenance references —
not a single opaque `frek_id` fused from a hash. No overclaiming any
robustness property (compression, noise, re-recording, collision
resistance) without test evidence; `UNKNOWN` stays `UNKNOWN`.

## What was implemented

**`backend/content_binding/`** (new module) — the canonical, hardened D1
implementation:

- `extraction.py` — `exact_hash()` (SHA-256, the exact-integrity axis)
  and `compute_signal_fingerprint()` (the perceptual/signal axis),
  REUSING `frek/nodes/node01_extraction.py`'s real 6-algorithm pipeline
  verbatim rather than reimplementing it. A real defect found during this
  pass's own validation run (a too-short clip silently produces `NaN`
  instead of raising) is closed here with an explicit finite-value guard
  — see `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md` §2 for the full
  finding and fix.
- `models.py` — `ContentBinding`, composed of the real D6 `Claim`/
  `Evidence` primitives (`proof_engine/evidence_semantics.py`, built the
  prior state and reused here, not reimplemented) plus `exact_hash` and
  `signal_fingerprint` as two structurally distinct fields, never merged.
- `routes.py` — `POST /api/v1/content-binding/{frek_id}` (create, holder-
  or-admin authorized, idempotent on `(frek_id, exact_hash)`),
  `GET /api/v1/content-binding/{frek_id}` (list, public),
  `GET /api/v1/content-binding/binding/{binding_id}` (detail, public).
  `frek_id` must already exist as a real `.fk` Cultural Object
  (`db.fk_objects`) — this route **never mints an identifier**, closing
  the historical FREK-ID/fingerprint conflation structurally, not just in
  documentation.

**Persistence**: plain MongoDB (`db.content_bindings`) — no PostgreSQL,
no pgvector, no new database technology. These 3 routes only ever need
exact lookup by `frek_id` or `binding_id`, never similarity search (that
is D3-B/resonance's concern, out of D1's scope), so the historical
pgvector requirement does not apply here.

**Notarization**: best-effort via the existing `notary.chain.append_block`
(through `notary/service.py:notarize_event`) — a binding starts at
`proof_engine.ProofState.FINGERPRINT` ("a hash exists, nothing else") and
upgrades to `LOCAL_PROOF` once durably chained. No new proof-state
vocabulary; `proof_engine/models.py` is unchanged.

**Security hardening beyond the historical routes**: authenticated
(holder session via `identity_engine`'s existing `linked_objects`
pattern, or admin-key override — the historical `/certify` had none),
payload size bounded (25MB vs. the historical unbounded-up-to-100MB),
rate-limited (`content_binding_create`, 30/hour by default — the
historical route had none at all), idempotent (resubmitting identical
content returns the existing binding instead of minting a new one, unlike
the historical routes which minted a new identifier every time).

**Events/audit**: `content_binding.created` — a real producer
(`eventbus/producers.py:build_content_binding_created_event`), registered
in `registry/events/event_registry.json`, subscribed into the Audit Trail
(`server.py`'s `_AUDIT_TRAIL_EVENT_TYPES`) alongside every other real
producer.

## What was explicitly NOT done (per the founder's own prohibitions)

- **`backend/frek/routes.py`'s `POST /certify`, `POST /certify/upload`,
  `GET /verify/{frek_id}` were not touched.** Zero lines changed. They
  remain live exactly as before (unauthenticated, in-memory, minting
  their own identifier) — a separate, later ecosystem-consumer audit
  decides their fate, not this state.
- No route deletion, no deprecation, no migration of historical data
  (none exists durably to migrate — confirmed, everything was in-process
  memory).
- D2 (Creative Lifecycle), D3 (Relationship/Provenance Graph), D4
  (Offline Proof Transport), D5 (Technical Evidence Attestation) were not
  started. `backend/frek/` is otherwise untouched.
- No Production Readiness, Red/Blue/Purple, UI/UX, CVLN wiring, merge, or
  deploy.

## Verification

- `backend/tests/test_content_binding_unit.py` (26 tests) and
  `backend/tests/test_content_binding_extraction_unit.py` (7 tests) —
  mongomock + monkeypatched extraction, no live server/Mongo/librosa
  needed. Cover: FREK-ID/fingerprint separation, object-identity
  stability across algorithm versions, exact-hash/signal-fingerprint
  distinctness, algorithm versioning, idempotency, D6 evidence semantics
  (structural — real `Claim`/`Evidence` objects, not lookalikes),
  persistence, auth, route-shadowing, legacy-identifier compatibility.
- `backend/tests/test_eventbus.py` and `test_audit_trail.py` extended
  with the new producer's contract and audit-trail wiring.
- `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md` — real-librosa validation
  pass (librosa installed once, manually, in this sandbox; not part of
  CI) producing honest DEMONSTRATED/PARTIALLY_DEMONSTRATED/NOT_TESTED
  evidence per property, including the one real defect found and fixed.
- Full unit suite green; coverage gate (registry/eventbus/permissions/
  audit_trail/proof_engine/storage/observability) re-verified ≥90%.

## What this ADR does not do

It does not validate the signal-fingerprint algorithm's robustness beyond
what `FREKCORE_D1_VALIDATION_EVIDENCE.md` explicitly demonstrates — lossy-
compression robustness, re-recording robustness, and a real collision-rate
study all remain `NOT_TESTED`, honestly. It does not decide the historical
3 routes' eventual fate (preserve-as-legacy-adapter vs. eventual
deprecation) — that is a future, separately-authorized ecosystem-consumer
audit. It does not start D2–D5.
