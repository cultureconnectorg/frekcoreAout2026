# 0007 — Founder Decision D4: Offline Proof Transport / Synchronization (APPROVED, IMPLEMENTED)

Status: **DECIDED, IMPLEMENTED**. Records the founder's D4 decision from
`FREKCORE_EXECUTION_PROTOCOL_V1` §STATE_4 (2026-09-02) and how it was
carried out. Background: `reports/FREKCORE_HISTORICAL_CAPABILITY_
RECONCILIATION.md` §D "D4 — Offline Proof Transport" (the reconciliation
pass that first surfaced D4 as one of 5 historical capabilities requiring
a founder decision, out of the 19 `backend/frek/` routes).

## Founder decision, verbatim (paraphrased from the execution protocol)

**D4 = PRESERVE_ADAPTER.** The historical FREK multi-channel transmission
vision (`backend/frek/nodes/node07_transmission.py`) must be preserved,
but implemented correctly as a transport-independent, cryptographically
verifiable evidence-envelope and synchronization capability. FREKCORE
defines the trust semantics; transport technologies (NFC/BLE/WiFi/QR/
audio/ultrasound) stay adapters, never kernel dependencies:

    OFFLINE_TRUST_EQUALS_TRANSPORT_TECHNOLOGY = FALSE
    CRYPTOGRAPHICALLY_VALID_EQUALS_CURRENTLY_AUTHORIZED = FALSE
    CRYPTOGRAPHICALLY_VALID_EQUALS_FULLY_VERIFIED = FALSE
    SIGNED_EQUALS_TRUSTED = FALSE
    RECEIVED_EQUALS_ACCEPTED = FALSE
    ACCEPTED_OFFLINE_EQUALS_FINAL_RECONCILIATION = FALSE
    WATERMARK_EQUALS_PROOF = FALSE

FAP reuse was mandatory (`REUSE_FAP=TRUE, DUPLICATE_FAP=FALSE`); D6/D1/D2/
D3 had to be consumed, never reimplemented; the 6 historical transmission
routes had to be preserved untouched.

## Historical discovery (evidence, not a prior summary)

Read directly from `backend/frek/nodes/node07_transmission.py` and the
transmission section of `backend/frek/routes_advanced.py`:

- **5 transport protocols declared**: BLE, NFC, WIFI_LOCAL, ULTRASONIC,
  CELLULAR. QR — named in this state's own mission brief as a possible
  adapter — was never part of the historical vocabulary.
- **`TransmissionPacket` carries no real cryptographic signature.**
  `signature_short` is `sha256_signal[:8]` — an unverified, caller-
  supplied 8-character hash prefix, not a signature over the packet's
  own bytes. No signing key, no verify function, no device identity
  check exists anywhere in the file. This is the single most important
  finding: the historical "packet" was never a cryptographically
  verifiable artifact in the first place.
- **No nonce, no sequence number, no replay protection at all.**
- **`sync_status` has 3 values** (`pending`/`synced`/`failed`) — no
  conflict, no rejection-with-reason, no revalidation-needed state.
- **`sync_pending()`'s own comment admits it is a simulation** — it
  always succeeds unconditionally, does no real network call, no
  authority re-check, no conflict detection.
- **Storage is pure Python-process memory**, wiped on every restart —
  identical to every other `backend/frek/` node's storage story (D1–D3).
- **The ultrasonic watermark is write-only.** `UltrasonicWatermark`
  FSK-modulates a truncated SHA-256 hash into an 18kHz+ carrier and
  asserts `"inaudible": frequency_hz >= 17000` — an unmeasured claim. No
  decode/extraction function exists anywhere in the file — a write-only
  watermark with no reader cannot function as a locator, identifier, or
  content binding in practice.
- **Zero authentication** on all 6 historical routes — confirmed by grep,
  consistent with D1–D3's own historical-route findings.

## FAP reuse (the real headline of this state)

`frek_v3/reference_verifier/` is a real, complete, independently tested
(`test_frek_verifier.py`) reference implementation of the FREK
Attestation Protocol: binary parser/serializer, real ECDSA-P256 signing/
verification over a deterministic canonical message, a device registry
with `ACTIVE`/`REVOKED`/`SUSPENDED` status, and a full verification
pipeline (structural validation → device identity check → registry
lookup → signature verification → counter/replay check → nonce check →
firmware check). Per `docs/architecture/FAP_PROOF_ENGINE_RECONCILIATION.
md`, FAP was real and complete but **isolated** — no `backend/` endpoint
had ever called it. `backend/offline_transport/fap_adapter.py` is that
first caller: it reuses FAP's own parser and `FrekVerifier` end to end
for the envelope's optional `device_attestation` layer — nothing
cryptographic is reimplemented. `frek_v3/reference_verifier/`'s own
modules use bare, non-relative imports and are consumed by their own
test suite the same way (the package directory itself on `sys.path`);
`fap_adapter.py` follows that exact, already-established pattern
(`_ensure_fap_importable()`) rather than inventing new packaging.
Verified genuinely: this state's own tests generate real, validly-signed
FAP proofs via FAP's own `SimulatedFrekDevice`, exercise tampering
(signature rejected), and exercise device revocation (caught freshly at
SYNC even when it wasn't revoked at RECEIVE time).

## What was implemented

**`backend/offline_transport/`** (new module):

- `models.py` — `TransportProtocol` (historical 5, verbatim, + QR/
  LOCAL_FILE/LOCAL_NETWORK/DEVICE_TO_DEVICE, new this state),
  `LocalValidationStatus` (INVALID / CRYPTO_VALID_BUT_STATUS_STALE /
  LOCALLY_ACCEPTABLE — the mission's own named LOCAL_VALIDATION
  outcomes), `SyncStatus` (PENDING/SYNCING/SYNCED/REJECTED/CONFLICT/
  NEEDS_REVALIDATION — the historical 3-value vocabulary is a strict,
  preserved subset), `DeviceAttestation`/`FreshnessInfo`,
  `TransportEnvelope` (the canonical envelope, composed of D6's real
  `Claim`/`Evidence` directly).
- `canonical.py` — deterministic canonical JSON (the identical formula
  already independently kept in `fk/packager.py:canonical_json` and
  `notary/chain.py:_canonical_json`, a third local copy following an
  established convention, not a new algorithm), and `signable_core` — a
  deliberate strict subset of the envelope (excludes `signature` itself,
  `transport_metadata`, and every receiver-side mutable field) so an
  envelope's signature stays valid across its whole offline journey even
  as freshness/sync_status/local_validation change underneath it.
- `fap_adapter.py` — the FAP reuse layer described above.
- `service.py` — pure functions: `compute_local_validation` (the
  structural point where a valid signature alone can reach at most
  CRYPTO_VALID_BUT_STATUS_STALE, never LOCALLY_ACCEPTABLE, unless
  freshness is explicitly current and unexpired), `is_replay`,
  `is_out_of_order`, `detect_conflict`.
- `adapters.py` — the transport adapter boundary: `encode_envelope`/
  `decode_envelope` are transport-independent (the identical signable
  core survives every protocol tag, verified by test); `adapter_info()`
  reuses `Node07Transmission.PROTOCOL_CONFIG` directly for the 5
  historical protocols, never reimplementing their range/power/latency
  facts. No adapter claims `hardware_verified=True` — this sandbox has
  no real BLE/NFC/QR/ultrasonic hardware.
- `watermark.py` — reuses the historical generator directly, wraps it
  with an honest `"proof": False, "validation_status": "NOT_TESTED"`
  annotation. `WATERMARK_EQUALS_PROOF=FALSE` is enforced structurally:
  no other module in `offline_transport/` imports this one.
- `routes.py` — `POST /api/v1/offline/envelopes` (CREATE+SIGN, Ed25519
  via `passport.keys` — the same signer behind `.fk`'s own
  `ProofLayer.signature`), `POST .../envelopes/{id}/receive`
  (RECEIVE+LOCAL_VALIDATION), `POST .../envelopes/{id}/sync`
  (SYNC+STATUS_REFRESH+AUTHORITY_CHECK+REPLAY/ORDERING/CONFLICT+FINAL_
  RECONCILIATION, the mission's own 11-step reconnect flow),
  `GET .../envelopes/{id}`, `GET .../envelopes/queue`,
  `POST/GET .../devices` (FAP device registration/revocation),
  `GET .../protocols`, `POST .../watermark`,
  `GET .../historical-taxonomy`-equivalent via `/protocols`.

**A real design defect caught by this state's own test suite**: an
earlier draft's EMISSION-idempotency-style conflict check for the
CONFLICT branch would have needed a hand-crafted second envelope with a
tampered `envelope_id` — which, since `envelope_id` is itself part of
the signed core, silently produced an *invalid signature* instead of a
genuine same-slot conflict, so the sync path rejected it for the wrong
reason (`signature_invalid` before ever reaching the conflict check).
Fixed by constructing the test's conflicting envelope as a second,
independently and validly signed envelope (mirroring what two real
offline devices picking the same local sequence number would actually
produce) rather than mutating a signed copy after the fact — this in
turn confirmed the route's own check ordering is correct: replay is
checked before conflict, matching a fail-fast security posture.

**Object identity discipline**: `TransportEnvelope` never mints a FREK
Object identity, D1 content binding, D2 lifecycle event, or D3
relationship — it only ever *references* an existing one (validated to
exist at CREATE time, and re-validated at SYNC time in case a reference
became invalid meanwhile).

**Persistence**: plain MongoDB (`db.transport_envelopes`,
`db.offline_issuer_state`, `db.fap_devices`) — `DO_NOT_FORCE_NEW_
DATABASE` honored, no RAM-only canonical queue (verified by test: a
second app instance sharing the same `db` sees the identical queue).

**Security hardening beyond the historical routes**: authenticated (no
unauthenticated write path at all, unlike every historical transmission
route), payload size bounded (`MAX_ENVELOPE_BYTES=64KB` on any inline
envelope bytes — references/hashes preferred over embedding large
artifacts), rate-limited (`offline_transport_write`, shared across
create/receive/sync), replay-protected (nonce + monotonic per-issuer
sequence), ordering-aware (out-of-order envelopes queue rather than
reconcile ahead of their predecessor), conflict-preserving (same-slot
disagreements are flagged, never silently overwritten), idempotent
(receive is a pure update; an already-synced sync retry is a safe no-op
that publishes no duplicate event).

**Notarization/events/audit**: best-effort notarization via
`notary.service.notarize_event(payload_type="offline_transport_
envelope", ...)`; one unified event `offline_transport.envelope_
recorded` (`payload.transition`/`payload.sync_status` distinguish
create/receive/sync), registered in `registry/events/event_registry.
json`, subscribed into the Audit Trail alongside every other real
producer (now ten, up from nine after D3).

## What was explicitly NOT done (per the founder's own prohibitions)

- **`backend/frek/routes_advanced.py`'s 6 historical transmission routes
  were not touched.** Zero lines changed — confirmed by a static-import
  test and a route-count regression guard.
- No cultural-fingerprint pipeline, no technical evidence report
  (`IMPLEMENT_TECHNICAL_EVIDENCE_REPORT=FALSE`), no CVLN wiring.
- D5 (Human-Readable Technical Evidence) was not started.
- No Production Readiness, Red/Blue/Purple, UI/UX, merge, or deploy.
- No hardware verification claimed anywhere — every transport adapter
  reports `hardware_verified: false`, honestly, since this sandbox has
  no real BLE/NFC/QR/ultrasonic hardware to test against.
- D1's own verification status is **not** silently upgraded — D4
  transports D1 references but never invokes D1's own extraction
  functions, so `D1_VERIFIED` stays `PARTIAL`.

## Verification

- `backend/tests/test_offline_transport_unit.py` (35 tests) — mongomock,
  real Ed25519 signing (`passport.keys`), real FAP ECDSA proofs
  (`frek_v3.reference_verifier.frek_device_sim.SimulatedFrekDevice`), no
  live server/Mongo needed. Covers: transport independence, canonical-
  serialization determinism, tampering detection, authority-freshness
  distinction (valid signature ≠ current authority), idempotent receive,
  sequence/nonce handling, out-of-order queuing, replay rejection,
  conflict preservation, device-time vs. issuance-time vs. verifier-time
  distinctness, offline-acceptance-≠-final-reconciliation, revocation
  caught freshly at sync, malformed/oversized/unknown-device/unsupported-
  algorithm safe handling, D6/D1/D2/D3 reuse (structural, not just
  claimed), audit/event-bus integration, historical-route preservation,
  adapter-cannot-override-verification, watermark-never-proof.
- `backend/tests/test_eventbus.py` and `test_audit_trail.py` extended
  with the new producer's contract and audit-trail wiring (now ten real
  producers, up from nine after D3).
- Full unit suite: 352 passed (was 315 after D3), 0 failed. Coverage
  gate (registry/eventbus/permissions/audit_trail/proof_engine/storage/
  observability) re-verified: 96.69% against 90%.
- flake8/black on `offline_transport/` and its tests: clean. mypy's
  `Optional[db]`/pydantic-signature findings there match the exact
  pre-existing pattern already present in `content_binding/`,
  `creative_lifecycle/`, and `relationship_graph/` (confirmed via diff),
  not a regression, and `offline_transport/` is outside CI's blocking
  mypy `MODULES` scope.

## What this ADR does not do

It does not claim any transport adapter is hardware-verified — BLE/NFC/
QR/ultrasonic/cellular all stay software-only, tested claims
(`HARDWARE_VERIFIED_ADAPTERS: NONE`). It does not build a real ultrasonic
audio-embedding path or watermark decoder (the historical generator is
reused verbatim; no reader existed before and none is added now). It
does not extend D1's own signal-algorithm validation (`D1_VERIFIED`
stays `PARTIAL`). It does not decide the historical 6 transmission
routes' eventual fate (compatibility adapter vs. eventual deprecation) —
that is a future, separately-authorized ecosystem-consumer audit. It
does not start D5.
