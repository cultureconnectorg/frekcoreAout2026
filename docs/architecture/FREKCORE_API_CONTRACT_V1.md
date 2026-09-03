# FREKCORE API Contract — v1

STATE_7 (API/SDK Contract Stabilization, `FREKCORE_EXECUTION_PROTOCOL_V1`,
2026-09-03). This is the authoritative canonical API surface matrix for the
integration areas the founder's STATE_7 mission names: Identity, Authority,
Object, Content Binding, Creative Lifecycle, Relationship/Provenance, Claim,
Evidence, Proof, Verification, Credential, Offline Transport, Technical
Evidence Report, Audit/Events, and Legacy Compatibility.

**Scope note**: FREKCORE's `server.py` mounts ~30 routers beyond this list
(badges, jetons, staff, geo, EUDI, ecosystem, standards, fingerprint,
investor, heritage, moment, PDF batch, ...). Those are real, live,
independently-owned platform capabilities, not part of the 11 areas STATE_7
names — cataloging them is out of this bounded state's scope
(`GENERAL_REAUDIT=FALSE`). They keep whatever contract status their own
prior phases gave them.

`CANONICAL_INTERNAL_IMPLEMENTATION != PUBLIC_CONTRACT`: the columns below
describe what a consumer may depend on. Internal module layout may change
later without notice; this table is the thing that may not change without
following the versioning/compatibility policy in
`docs/architecture/FREKCORE_VERSIONING_POLICY.md`.

**STATUS legend**: `STABLE` (versioned, tested, safe to build on) ·
`EXPERIMENTAL` (real, tested, may still change shape) ·
`INTERNAL` (not meant for external consumers) ·
`LEGACY_COMPATIBILITY` (the 19 historical `backend/frek/` routes — kept
working, not the integration surface for new consumers).

All STABLE/EXPERIMENTAL endpoints below are mounted at `/api/v1/...`. All
LEGACY_COMPATIBILITY endpoints are mounted at `/api/frek/...` (outside the
`v1` path namespace, by design — see "API versioning" below).

---

## API versioning

**Policy**: FREKCORE versions its canonical HTTP API at the path level —
`/api/v1/...`. A breaking change (see `FREKCORE_VERSIONING_POLICY.md` for
the exact SAFE/POTENTIALLY_BREAKING list) ships as `/api/v2/...` alongside
the still-live `/api/v1/...`, never as a silent in-place change to `v1`.
This is a **declared policy, not yet exercised** — no `v2` exists because
no v1 canonical endpoint has needed a breaking change yet; this document
establishes the rule STATE_7 commits to, ahead of the first time it's
needed.

The 19 historical `backend/frek/` routes are **not** renamed into `/api/v1/`
— they stay at their historical `/api/frek/...` paths, explicitly classified
`LEGACY_COMPATIBILITY` (not "v0" or "deprecated v1" — they were never part
of the versioned contract to begin with, per STATE_6's own founder rule
`DESTRUCTIVE_API_MIGRATION_ALLOWED=FALSE`). New consumers integrate against
`/api/v1/...`; `/api/frek/...` exists for the confirmed real callers found
in STATE_6 (see `docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`)
and is never the recommended integration path for anyone else.

---

## 1. Identity & Authority — `identity_engine` (`/api/v1/identity`)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `/init` | Create a FREKIdentity | none (bootstrap) | not idempotent (mints a new identity each call) | `identity.created` | STABLE |
| POST | `/{frek_id}/register/begin` | WebAuthn passkey registration, step 1 | holder session | N/A (challenge issuance) | — | STABLE |
| POST | `/{frek_id}/register/complete` | WebAuthn passkey registration, step 2 | holder session + WebAuthn assertion | N/A | — | STABLE |
| POST | `/authenticate/begin` | WebAuthn login, step 1 | none | N/A | — | STABLE |
| POST | `/authenticate/complete` | WebAuthn login, step 2 | WebAuthn assertion | N/A | — | STABLE |
| GET | `/me` | Caller's own identity | holder session | read-only | — | STABLE |
| GET | `/search` | Enumerate identities | admin key | read-only | — | INTERNAL (admin-only enumeration surface, not a public integration point) |
| GET | `/{frek_id}` | Public identity view (`_to_public()`, never credentials) | none | read-only | — | STABLE |
| GET | `/{frek_id}/objects` | Objects linked to an identity | holder session (own identity only) | read-only | — | STABLE |
| POST | `/link-object` | Link a `.fk`/moment object to caller's identity | holder session | idempotent (linking twice is a no-op) | — | STABLE |
| POST | `/{frek_id}/revocation` | Revoke an identity | holder session or admin | idempotent (already-revoked is a no-op) | `identity.revoked` | STABLE |
| PATCH | `/{frek_id}` | Update `display_name`/`metadata` | holder session or admin | not idempotent (partial update) | `identity.updated` | STABLE |
| POST | `/{frek_id}/archive` | Archive an identity | holder session or admin | idempotent | — | STABLE |
| POST | `/{frek_id}/reconcile` | Non-destructive cross-identity/cross-system link | holder session (target) or admin | append-only, safe to retry | `identity.reconciled` | STABLE |
| GET | `/{frek_id}/reconciliations` | List an identity's reconciliation records | holder session or admin | read-only | — | STABLE |

`identity_engine` is also the **Credential** capability area for D5's own
purposes (`Credential` report subject type = WebAuthn passkeys attached to
a `FREKIdentity`, `technical_evidence_report/service.py:
build_credential_section`) — there is no separate "Credential API"; a
credential is always read through its owning identity (counts only, never
raw public keys — see `FREKCORE_ERROR_CONTRACT_V1.md`'s privacy notes).
`did`/`vc` (`/api/v1/identity/{frek_id}` DID document,
`/api/v1/vc/{frek_id}` + `/api/v1/vc/verify`) is a **separate**,
EUDI/OID4VCI-shaped Verifiable Credential surface — real, tested, but not
the D5 "Credential" concept; documented here for completeness, status
EXPERIMENTAL (not independently verified against a real EUDI reference
wallet, per `FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`).

## 2. Object — `.fk` Cultural Object (`/api/v1/fk`)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `/create` | Mint a new `.fk` Cultural Object (the one real FREK-ID minter) | none (public creation, rate-limited) | not idempotent (mints a new object each call) | `object.created` | STABLE |
| POST | `/verify` | Verify a `.fk` archive's signature/hashes | none | read-only | — | STABLE |
| GET | `/detail/{frek_id}` | Public object metadata | none | read-only | — | STABLE |
| GET | `/{frek_id}/download` | Re-download a server-kept `.fk` archive | none | read-only | — | STABLE |
| GET | `/stats` | Aggregate `.fk` stats | none | read-only | — | STABLE |
| GET | `/pubkey` | FREKCORE's own Ed25519 institutional public key | none | read-only | — | STABLE |

## 3. Content Binding (D1) — `content_binding` (`/api/v1/content-binding`)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `/{frek_id}` | Bind computed exact-hash + signal-fingerprint evidence to an existing `.fk` object (multipart: `audio` file + optional `legacy_identifier`) | holder (owner/linked) or admin | **idempotent on (`frek_id`, `exact_hash`)** — resubmitting identical content returns the existing binding, never a duplicate | `content_binding.created` | STABLE |
| GET | `/binding/{binding_id}` | Fetch one binding by its own id | none (evidence data, public-readable by design — see `content_binding/models.py`) | read-only | — | STABLE |
| GET | `/{frek_id}` | List all bindings for an object | none | read-only | — | STABLE |

`D1_VERIFIED=PARTIAL` — unchanged by STATE_7 (see D1 Scientific Status
below). `FREK_ID_EQUALS_SIGNAL_FINGERPRINT=FALSE`, structurally enforced
(a binding always references an existing `frek_id`, never mints one).

## 4. Creative Lifecycle (D2) — `creative_lifecycle` (`/api/v1/creative-lifecycle`)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `/genesis` | Declare creative intent (new `pre_id`) | holder or admin | not idempotent (starts a new cycle each call) | `creative_lifecycle.recorded` | STABLE |
| POST | `/{pre_id}/workshop` | Record an intermediate version (multipart audio) | holder (owner) or admin | append-only, safe to retry (each call records a new WORKSHOP version by design) | `creative_lifecycle.recorded` | STABLE |
| POST | `/{pre_id}/metamorphose` | Submit the version being finalized | holder or admin | idempotent on identical final content (mirrors D1's own dedup discipline) | `creative_lifecycle.recorded` | STABLE |
| POST | `/{pre_id}/emission` | Bind the cycle to an existing `.fk` object (`fk_frek_id`) | holder or admin | idempotent (re-emitting to the same `fk_frek_id` is a safe no-op — the EMISSION-idempotency defect STATE_2 found and fixed) | `creative_lifecycle.recorded` | STABLE |
| POST | `/{pre_id}/legacy` | Declare a downstream derivative | holder or admin | append-only | `creative_lifecycle.recorded` | STABLE |
| GET | `/{pre_id}` | Full event history for one cycle | none (history is public-readable, matches D1's own disclosure stance) | read-only | — | STABLE |

GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY never imply legal
authorship/ownership/absolute priority — enforced by D6 evidence semantics
throughout (every event carries a `Claim`/`Evidence` pair, never a bare
assertion of fact).

## 5. Relationship / Provenance, Claim, Evidence (D3) — `relationship_graph` (`/api/v1/relationships`)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `` (root) | Assert a relationship (creates or appends an `Assertion` to an existing (subject, predicate, object) slot) | holder (self-assertable origins only) or admin | **idempotent on (subject, predicate, object, actor, origin)** — the identical retry is a no-op, a different actor is preserved as independent provenance | `relationship.recorded` | STABLE |
| GET | `/historical-taxonomy` | The historical 17-relation-type disposition record | none | read-only | — | STABLE |
| GET | `/{relationship_id}` | One relationship (visibility-filtered) | optional (redacted by `Scope`) | read-only | — | STABLE |
| GET | `/{relationship_id}/history` | Full assertion history | optional (redacted) | read-only | — | STABLE |
| GET | `/entity/{entity_id}/neighbors` | Bounded neighbor query (both directions) | optional (redacted) | read-only | — | STABLE |
| GET | `/entity/{entity_id}/outgoing` | Bounded outgoing edges | optional (redacted) | read-only | — | STABLE |
| GET | `/entity/{entity_id}/incoming` | Bounded incoming edges | optional (redacted) | read-only | — | STABLE |
| GET | `/traverse/path` | Bounded shortest-path traversal | optional (redacted) | read-only | — | STABLE |
| POST | `/{relationship_id}/verify` | Mark a **TRUST**-layer relationship VERIFIED | admin (or authorized attester) | idempotent (already-VERIFIED is a no-op) | `relationship.recorded` | STABLE |
| POST | `/{relationship_id}/revoke` | Revoke an assertion | holder (own assertion) or admin | idempotent | `relationship.recorded` | STABLE |

**Claim/Evidence** are not a separate HTTP surface — they are D6's own
`proof_engine.evidence_semantics` primitives, embedded directly inside
every D1/D2/D3/D4 record (`ContentBinding.claim`/`.evidence`,
`LifecycleEvent.claim`, `Assertion.claim`/`.evidence`,
`TransportEnvelope.claim`/`.evidence`). They are read wherever their
owning record is read, never through a standalone `/claims` or
`/evidence` endpoint — inventing one would be a second, parallel
representation of the same D6 data (`REWRITE_D1_D6_ARCHITECTURE=FALSE`
territory), not a coherence gap.
`TRUST_PROVENANCE_GRAPH_EQUALS_CULTURAL_INFERENCE_GRAPH=FALSE`: a
CULTURAL-layer relationship structurally can never reach `VERIFIED`.

## 6. Offline Transport (D4) — `offline_transport` (`/api/v1/offline`)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `/envelopes` | Create + Ed25519-sign a transport envelope | holder (self-assertable origins) or admin | not idempotent (mints a new envelope + sequence number each call — by design, matching a real offline device's own monotonic counter) | `offline_transport.envelope_recorded` | STABLE |
| GET | `/protocols` | Per-protocol adapter metadata (historical + new) | none | read-only | — | STABLE |
| POST | `/watermark` | Historical ultrasonic watermark reference (never proof) | holder or admin | idempotent (pure function of `frek_id`) | — | STABLE |
| POST | `/devices` | Register a FAP device (admin) | admin | idempotent (upsert) | — | STABLE |
| POST | `/devices/{device_id_hex}/revoke` | Revoke a FAP device | admin | idempotent | — | STABLE |
| GET | `/envelopes/queue` | Pending/needs-revalidation envelopes for an issuer | holder (own) or admin | read-only | — | STABLE |
| GET | `/envelopes/{envelope_id}` | One envelope | holder (issuer) or admin | read-only | — | STABLE |
| POST | `/envelopes/{envelope_id}/receive` | RECEIVE + LOCAL_VALIDATION | holder (issuer) or admin | **idempotent** — a pure re-evaluation of the same envelope | — (surfaces in the next state transition's event) | STABLE |
| POST | `/envelopes/{envelope_id}/sync` | SYNC + FINAL_RECONCILIATION | holder (issuer) or admin | **idempotent** — an already-SYNCED/REJECTED retry returns the existing outcome, never re-runs side effects | `offline_transport.envelope_recorded` | STABLE |

`CRYPTOGRAPHICALLY_VALID_EQUALS_FULLY_VERIFIED=FALSE`: a valid signature
alone caps at `CRYPTO_VALID_BUT_STATUS_STALE`, never `LOCALLY_ACCEPTABLE`,
without explicit unexpired freshness.

## 7. Technical Evidence Report (D5) — `technical_evidence_report` (`/api/v1/reports`)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `/technical-evidence` | Generate a report from a `subject_type`+`subject_id` resource reference | holder or admin | not idempotent (mints a new immutable snapshot + `report_id` each call by design — see "Report immutability" in `FREKCORE_VERSIONING_POLICY.md`) | `technical_evidence_report.recorded` | STABLE |
| GET | `/technical-evidence/{report_id}` | Retrieve a snapshot, redacted per caller | holder/admin (per-section `Scope`) | read-only | `technical_evidence_report.recorded` | STABLE |
| GET | `/technical-evidence/{report_id}/verify` | **Public verification** — shape only, integrity-hash match | none | read-only | `technical_evidence_report.recorded` | STABLE |

`VERIFICATION_MAY_BE_PUBLIC=TRUE, DISCLOSURE_IS_AUTHORIZATION_SCOPED=TRUE`
— see "Public verification contract" in `FREKCORE_VERSIONING_POLICY.md`.

## 8. Proof / Verification — `notary` (`/api/v1/notary`), `proof_engine` (no HTTP surface)

| Method | Path | Capability | Auth | Idempotency | Events | Status |
|---|---|---|---|---|---|---|
| POST | `/notarize` | Append a block to FREK-Chain for arbitrary `payload_type`/`payload_id`/`payload_data` | internal callers only (every D1–D5 route calls this server-side; not intended as a direct external write surface) | append-only | — | INTERNAL |
| GET | `/block/{height}` | One chain block | none | read-only | — | STABLE |
| GET | `/blocks` | List blocks | none | read-only, paginated (see Pagination contract) | — | STABLE |
| GET | `/proof/{payload_id}` | Proof for a payload (local chain proof + OTS if anchored) | none | read-only | — | STABLE |
| GET | `/proof/{payload_id}/ots` | Raw OpenTimestamps proof bytes | none | read-only | — | STABLE |
| POST | `/anchor/sweep`, `/anchor/upgrade`, `/anchor/force-upgrade`, `/anchor/{height}` | Bitcoin-anchoring operational controls | admin | idempotent (safe re-sweep) | — | INTERNAL (operational, not a consumer-facing integration point) |
| GET | `/chain/status` | Chain health summary | none | read-only | — | STABLE |
| GET | `/chain/events` | Distinct `event_id`s notarized | none | read-only | — | STABLE |
| GET | `/chain/verify` | Full chain integrity check | none | read-only | — | STABLE |
| GET | `/health`, `/source/health` | Health probes | none | read-only | — | INTERNAL |

`proof_engine.evidence_semantics`/`proof_engine.models`/
`proof_engine.notary_adapter` have **no HTTP surface of their own** — they
are the shared vocabulary (`Claim`, `Evidence`, `AuthorityStatus`,
`ProofState`) every D1–D5 module's own HTTP responses already expose
inline. `ProofState`/`VerificationResult` remain the canonical proof-state
ladder; nothing in STATE_7 adds a rival one.

## 9. Audit / Events — `audit_trail` (write-only, no HTTP surface), `audit` (`/api/v1/audit`, read-only legacy aggregation), `eventbus`/`registry/events` (contract, not a callable API)

| Method | Path | Capability | Auth | Status |
|---|---|---|---|---|
| — | — | `audit_trail`: subscribes to the Event Bus, writes append-only `AuditEvent` records. **No HTTP read endpoint exists for it.** | N/A | INTERNAL / disclosed gap (see below) |
| GET | `/{frek_id}` | Human-readable timeline (frek_stages + scans + transactions + notary_blocks) | none | STABLE, but explicitly **not** the same thing as `audit_trail`'s own authoritative event log — see `audit/routes.py`'s own module docstring | LEGACY-ADJACENT (predates the D-state work, not one of the 19, kept as-is) |
| GET | `/agent/{agent_id}/actions` | Timeline filtered by agent | none | same caveat | LEGACY-ADJACENT |
| GET | `/event/{event}/recent` | Timeline filtered by event type | none | same caveat | LEGACY-ADJACENT |

**Disclosed gap (real, not fixed this state — `REWRITE_D1_D6_ARCHITECTURE
=FALSE`, `GENERAL_REAUDIT=FALSE` cover this)**: `backend/audit_trail/` is
write-only from the HTTP surface's perspective — it has no
`GET /api/v1/audit-trail/*` of its own. Today, reading the authoritative
audit log means a direct MongoDB read of `audit_trail_events`, not a
canonical API call. `backend/audit/routes.py`'s `/api/v1/audit/*` is a
**different, older, explicitly non-authoritative** convenience
aggregation (per its own docstring) — do not conflate the two.
`AUDIT_LOG != BUSINESS_EVENT` is preserved either way: `EventEnvelope`s on
the bus are the business-event contract (`FREKCORE_EVENT_CONTRACT_V1.md`);
`AuditEvent`s are their audit-trail projection, a strict subset written by
`audit_trail/subscribers.py`, never the reverse.

## 10. Legacy Compatibility — the 19 historical `backend/frek/` routes

Full per-route disposition/status: `docs/architecture/
FREK_HISTORICAL_COMPATIBILITY_MATRIX.md` (STATE_6). Summary for this
contract: **all 19 are classified `LEGACY_COMPATIBILITY`**, mounted at
`/api/frek/...` (outside `/api/v1/`), never renamed, never deleted. New
integrations should use the canonical `/api/v1/...` endpoints above; the
19 exist for the two confirmed real local callers
(`frontend/src/pages/Certify.jsx`, `Verify.jsx`) and any ecosystem
consumer not yet auditable from this workspace.

---

## Duplicate/overlapping canonical routes — checked, none found colliding

Verified directly from `server.py`'s router mounts (path+prefix), not
assumed: `identity_engine.routes.identity_router` mounts at
`/api/v1/identity`, while `did.routes.did_router`/`vc_router` mount at
their own, separate `/api/v1/did` and `/api/v1/vc` prefixes — `GET
/api/v1/identity/{frek_id}` (public identity view, credential-stripped)
and `GET /api/v1/did/{frek_id}` (W3C DID document for the same identity)
are two distinct paths, not a path collision, and not a semantic
duplicate either: one answers "who is this identity" (FREKCORE's own
canonical view), the other answers "what does this identity look like as
a W3C DID document" (an interoperability projection). **Canonical for
"who is this identity" is `identity_engine`'s own
`/api/v1/identity/{frek_id}`**; DID/VC is an additive, standards-interop
surface, not a competing identity source — a consumer needing DID/VC
interop uses `/did`/`/vc` deliberately, not by accident.

**Audit read** (`backend/audit/routes.py` vs. `backend/audit_trail/`, see
§9 above) is the one real ambiguity this pass found, and it is resolved by
explicit non-authoritative labeling rather than by removing either route:
removing `audit/routes.py` would be an undocumented scope expansion into
ops-tooling this state does not own, and giving `audit_trail` an HTTP
surface is a real, disclosed future gap, not silently built here without
evidence it's needed by name.

No other capability area exposes more than one canonical endpoint for the
same operation.

---

## D1 scientific status (unchanged)

`D1_IMPLEMENTED=TRUE`, `D1_VERIFIED=PARTIAL` — this contract document does
not upgrade that status. This document and the SDK/OpenAPI surface never
describe the signal fingerprint as robust under conditions not
demonstrated in `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`
(compression, re-recording, and collision-rate robustness remain
`NOT_TESTED`).
