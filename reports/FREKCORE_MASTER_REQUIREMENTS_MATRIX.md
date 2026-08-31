# FREKCORE — Master Requirements Matrix

Per the Documentation-as-Backlog directive. This is a **first-pass, evidence-based reconciliation** of documented FREKCORE capabilities against actual code — organized by domain rather than as an exhaustive numbered `requirement_id` list against every line of every historical document (30+ modules and a decade-spanning documentation set make a literally exhaustive line-by-line pass outside this session's remaining scope; see the "Scope note" at the end).

Status values used: `IMPLEMENTED`, `VERIFIED` (implemented + exercised with real evidence this session), `PARTIAL`, `DOCUMENTED_ONLY`, `MISSING`, `BLOCKED`, `DEPRECATED`, `SUPERSEDED`, `REJECTED`.

## Identity

**Founder directive update** (`docs/decisions/0001-founder-decisions-2026-08-31.md`): the table below predates the founder's explicit resolution of C1 ("reconcile, don't replace" — `identity_engine` is a modern *authentication* engine, not a redefinition of FREK-ID itself) and the deeper reconstruction in `docs/architecture/FREK_ID_CANONICAL_MODEL.md` and `docs/architecture/FREK_ID_RECONCILIATION.md`, including a new finding (Contradiction C6): the canonical architecture spec (`frek_v3/docs/FREK_Architecture_Integree_v0.2.md`) calls for **typed** DIDs (`did:frek:person-`, `org-`, `device-`, `app-`), but `backend/did/document.py` implements an untyped `did:frek:{frek_id}` — reclassify "typed DID subjects" as **DOCUMENTED_ONLY**, distinct from the `did:frek` method row below (which is real and untyped).

| Capability | Status | Evidence |
|---|---|---|
| FREK-ID (generic identifier concept) | **IMPLEMENTED** — but by **two non-interoperating systems** | See `reports/FREKCORE_CONTRADICTIONS.md` C1: `backend/frek_v1/` and `backend/identity_engine/` both mint "FREK-ID"-shaped identifiers into different collections |
| `did:frek` DID method | **VERIFIED** | `backend/did/routes.py`, `backend/standards/manifest.py:13` (`ISSUER_DID = "did:frek:frekcore"`), `backend/spec/routes.py:216` ("Methode DID 'did:frek:{frek_id}' deterministe, conforme W3C DID Core 1.0"). Live-tested this phase: `GET /.well-known/jwks.json` returned `200 OK` against the mongomock-backed real server |
| Identity lifecycle: create | **VERIFIED** | `identity_engine`: `POST /init` (live-tested, `reports/15_DEPENDENCY_REMEDIATION.md`); `frek_v1`: `POST /emit` |
| Identity lifecycle: resolve | **IMPLEMENTED** | `identity_engine`: `GET /{frek_id}`, `GET /me`; `frek_v1`: `GET /{frek_id}/status`, `/detail` |
| Identity lifecycle: revoke | **IMPLEMENTED (both systems, 2026-08-31)** | `frek_v1/identity.py:200` has `POST /{frek_id}/revoke` (client-initiated); `identity_engine` now has `POST /{frek_id}/revocation` (holder-initiated-by-default, admin override — distinct path, see `docs/architecture/FREK_ID_RECONCILIATION.md`'s P1 update for why not `/revoke`, a path `frek_v1` already owns at this shared prefix). Notarized, idempotent, immutable, live-tested (`backend/tests/test_identity_lifecycle.py`) |
| Identity lifecycle: renew/update | **IMPLEMENTED, VERIFIED conformant 2026-08-31** | `docs/decisions/0003-identity-lifecycle-founder-decisions-implemented.md` §2: `frek_v1`'s `/renew` (`frek_v1/identity.py:256`) verified to already match the founder's approved semantics — `expires_at`/`renewed_at` only, `frek_id` never touched (`backend/tests/test_frek_v1_renew_unit.py`). `identity_engine` has no expiry concept by design (`FREKIdentity` has none); its answer to credential rotation is the existing `register_begin`/`register_complete` "add a Passkey while holding a session" path, now named as such. `identity_engine`'s `update` (display_name/metadata, distinct from renew) remains **IMPLEMENTED**: `PATCH /{frek_id}`, holder-initiated-by-default, refused once revoked, live-tested |
| Identity lifecycle: merge | **REJECTED (true fusion) / IMPLEMENTED (reconciliation) 2026-08-31** | `docs/decisions/0003-...md` §1: destructive merge/fusion of two identities is explicitly rejected by founder decision. The approved replacement — non-destructive reconciliation (`POST /{frek_id}/reconcile`, `GET /{frek_id}/reconciliations`) — is implemented: append-only, dual holder-session consent for same-system targets, admin-only for cross-system (`frek_v1`) targets, idempotent, notarized, `identity.reconciled` event (9 tests, `backend/tests/test_identity_reconcile_unit.py`) |
| Identity lifecycle: archive | **IMPLEMENTED (identity_engine only, 2026-08-31)** | `POST /{frek_id}/archive` — holder-initiated-by-default, admin override, idempotent, refused once revoked (not the reverse); a new capability not modeled on any existing one, no `frek_v1` analog, no `unarchive` flow yet. Live-tested (`backend/tests/test_identity_lifecycle.py`) |
| Identity linking (objects to identity) | **IMPLEMENTED** | `identity_engine/routes.py: POST /link-object`, `GET /{frek_id}/objects` |
| Pseudonymous / anonymous identities | **IMPLEMENTED** | `backend/moment/routes.py` — explicit doctrine: "anonyme, sans auth", `PUBLIC_CLIENT_ID = "public-window-1"` |
| Organization identities | **IMPLEMENTED (2026-08-31)** | `backend/registry/schemas/v1/frek.organization.schema.json` (Phase 1) defines the shape; `POST /api/v1/registry/objects/frek.organization` (this P1 pass's instance store, see FREK Registry section below) now persists one |
| Device identities | **PARTIAL** | `backend/fingerprint/routes.py: POST /observe/device` records device-observation data, but there is no first-class "device identity" record type distinct from a FREK-ID |
| Identity recovery | **IMPLEMENTED 2026-08-31** | `docs/decisions/0003-...md` §3: `register_begin`/`register_complete` now accept an `X-Admin-Key` override, closing the real gap that a holder who lost every Passkey had no path back into their own identity (7 tests, `backend/tests/test_identity_recovery_unit.py`). Distinct from `heritage/claim` (inheritance-style transfer of control to a *different* beneficiary, `frek_v1`-only — see `docs/architecture/FREK_ID_ENTITY_TAXONOMY.md` §2.1) — recovery restores the SAME holder's own access, never regenerates `frek_id`, and is notarized/audited (`identity.recovered`) |
| Identity assurance levels | **MISSING** | No LOA (level-of-assurance) concept found in code |

## Credentials / Digital Identity Interoperability

| Capability | Status | Evidence |
|---|---|---|
| Verifiable Credentials (issuance) | **IMPLEMENTED** | `backend/did/routes.py` (`vc_router`), `backend/did/vc.py` |
| Verifiable Credentials (verification) | **IMPLEMENTED** | `vc_router.post("/verify")`, live-tested this phase (route reachable, 200 on well-formed request per Phase 1/2 audits) |
| Verifiable Presentations | **MISSING** | `grep -rn "Verifiable Presentation\|VerifiablePresentation" backend/` → no matches |
| Selective disclosure | **IMPLEMENTED**, but via Merkle proofs, not SD-JWT for the VC path | `backend/passport/service.py:disclose()` (Merkle-path selective disclosure over Passport claims) — a real, working, different mechanism than SD-JWT |
| SD-JWT / SD-JWT VC | **IMPLEMENTED**, scoped to the EUDI plugin only | `backend/eudi/sdjwt.py`, `POST /credential/verify-sdjwt` (`backend/eudi/routes.py:161`) — this is a *separate* selective-disclosure mechanism from Passport's Merkle approach, used only in the OID4VCI/EUDI code path |
| Credential status / revocation | **PARTIAL** | VC verification checks the underlying identity's `revoked` flag transitively where the identity system supports it (`frek_v1`); no dedicated Status List 2021-style mechanism found |
| FREK-ID subject/entity taxonomy | **Documented 2026-08-31** — see `docs/architecture/FREK_ID_ENTITY_TAXONOMY.md` for the full per-entity breakdown (Person, Institution, Role, Cultural Object, Device, Wallet, Software Agent, Physical Asset, Location, Certificate, Staff, Project) with OBSERVED/DOCUMENTED/DECIDED/PROPOSED/NOT-FOUND classification per entity | Built before implementing `docs/decisions/0003-...md`'s MERGE/RENEW/RECOVERY, so those decisions apply to the correct entity scope (Person/Institution identities in `identity_engine`, the only entity type with its own credentials) rather than assuming every FREK-ID behaves like a human account |
| Issuer / Holder / Verifier roles | **Connected 2026-08-31, deliberately not as `Role` enum members** | `backend/permissions/protocol_roles.py` (P2) adds a typed `ProtocolRole` vocabulary plus a documented mapping to `Role` — not new `Role` values, since no DID/EUDI route calls `permissions.engine.decide()` yet (see that file's own docstring for why adding enforceable roles with no route behind them would be scope no route needs). The mapping's honest current answer for all three is `None` (not a CVLN `Role` today) — Issuer is the platform itself (`did/vc.py` hardcodes `did:frek:frekcore`), Holder is the base case of having a FREK-ID, Verifier is a public unauthenticated read. 4 new unit tests, 100% coverage on the new module |
| Trust anchors / trust lists | **MISSING** | No trust-list/trust-anchor registry found (`grep -rn "trust_list\|trust_anchor" backend/` → no matches) |
| EUDI Wallet (OID4VCI) | **PARTIAL, correctly labeled** | `backend/eudi/routes.py` implements `credential-offer`, `token`, `credential`, `credential/verify-sdjwt` — real OpenID4VCI-shaped endpoints. **Not independently verified against a real EUDI reference wallet or conformance suite this session** — per this mission's own rule ("Do NOT claim EUDI/eIDAS compatibility unless technically proven"), this is PARTIAL, not VERIFIED |
| OpenID4VP | **MISSING** | `grep -rn "OpenID4VP\|openid4vp\|vp_token" backend/` → no matches — only the issuance side (OID4VCI) exists, not presentation |
| eIDAS 2.0 compliance | **DOCUMENTED_ONLY, NOT PROVEN** | `backend/did/routes.py` and `backend/eudi/` have comments referencing "eIDAS 2.0" (e.g. `backend/did/routes.py` header per Phase 1 audit) but no conformance testing evidence exists in this repository. **This matrix explicitly does not claim eIDAS compliance** |

## Cryptography

| Capability | Status | Evidence |
|---|---|---|
| Ed25519 signing | **VERIFIED** | `backend/passport/keys.py`; live-tested this phase (`GET /api/v1/health/deep` → `ed25519_key.ok: true` against the mongomock-backed real server) |
| ECDSA P-256 | **DOCUMENTED_ONLY in this repo** | Referenced in `frek_v3/reference_verifier/` (hardware attestation spec) — `frek_v3` is explicitly isolated from `backend/` (Phase 1 finding, `ecosystem/registry.json`'s `frek_v3` entry: "NO backend endpoint yet") |
| Key rotation | **MISSING** | No rotation tooling found for the Ed25519 signing key (`reports/05_SECURITY_REPORT.md` Phase 1, unchanged) |
| Key revocation | **MISSING** | Same as above |
| PUF-derived keys | **DOCUMENTED_ONLY, isolated** | `frek_v3/reference_verifier/` — hardware-only concept, Phase 2/3/4 (Rust/FPGA/ASIC) never reached per `ecosystem/registry.json` |
| HKDF | **not found in `backend/`** | `grep -rn "HKDF\|hkdf" backend/` → no matches outside `frek_v3/` |
| Nonce/counter handling (replay protection) | **PARTIAL** | `backend/passport/merkle.py:gen_nonce_hex()` — per-claim nonces for Merkle leaves (prevents claim-guessing, not a session/message replay-protection nonce); WebAuthn's own challenge/counter mechanism (`identity_engine/service.py`) provides real replay protection for the Passkey ceremony specifically |

## FREK Attestation Protocol (FAP) / frek_v3

| Capability | Status | Evidence |
|---|---|---|
| FAP specification (DEVICE_ID, COUNTER, NONCE, DEVICE_TIME, fixed receipt structure) | **DOCUMENTED_ONLY, isolated reference implementation** | `frek_v3/reference_verifier/frek_constants.py`, `frek_types.py`, `frek_verifier.py` — a real, tested (16 golden test vectors per `ecosystem/registry.json`) reference implementation exists, but it is **explicitly isolated from `backend/`** — no HTTP endpoint, no integration with `backend/proof_engine/` or `backend/notary/` |
| Reconciliation with current Proof Engine | **DONE 2026-08-31** | `docs/architecture/FAP_PROOF_ENGINE_RECONCILIATION.md` — full point-by-point mapping (FREK Object/.fk, FREK-ID, provenance, signatures, device identity, counters/nonces/replay, Proof Engine, FREK-Chain, timestamps/anchors, offline verification). Headline finding: FAP's device-attestation levels and the Proof Engine's `ProofState` are orthogonal trust axes, not competing systems — no code conflict exists, and the integration shape (additive fields, `notary.chain.append_block`'s existing generic `payload_type` extensibility point) needs no new architectural pattern. Not implemented (no hardware to test against, correctly out of scope) — this is the reconciliation, not the build |
| Hardware capture credential (Luciole device, PUF key, `FREKCaptureCredential`) | **DOCUMENTED_ONLY** | `frek_v3/docs/FREK_Architecture_Integree_v0.2.md` §3.7 specifies a full pipeline (PUF-derived Ed25519 signing key → hardware-signed `FREKCaptureCredential` issued by `did:frek:device-<id>`); no corresponding backend module or route found anywhere in `backend/`. See `docs/architecture/FREK_ID_CANONICAL_MODEL.md` §3 |

## Proof / Notarial Layer

Fully covered in `reports/18_RUNTIME_VALIDATION.md` Priority 8 — summary: hash/fingerprint **VERIFIED**, local receipt **VERIFIED**, signed receipt **IMPLEMENTED** (Passport, not block-level), trusted timestamp **PARTIAL** (local clock only, no TSA), OpenTimestamps **IMPLEMENTED but runtime-BLOCKED in this sandbox** (real code, network-policy-blocked from reaching calendar servers here), Bitcoin anchoring **NOT VERIFIED THIS PHASE** (depends on OTS reaching confirmation, real wall-clock hours). FREK-Chain hash-chaining is real; the Phase-1-era overclaim that blocks are individually Ed25519-signed was found and corrected (`reports/FREKCORE_CONTRADICTIONS.md` C2).

## Cultural Provenance

| Capability | Status | Evidence |
|---|---|---|
| Creator / contributor | **IMPLEMENTED** | `backend/fk/models.py:CreatorsLayer` (`primary_creator`, `contributors`) |
| Ownership / rights / splits | **IMPLEMENTED** | `backend/fk/models.py:RightsLayer` (`owner`, `co_owners`, `licenses`, `transfers`) |
| Derivation / versions / lineage | **PARTIAL** | `backend/fk/models.py:TimelineLayer`/`Version` (`based_on` field) covers simple version chains; no explicit "derivative work" graph beyond that |
| Transformation history | **PARTIAL** | Same `TimelineLayer` — records versions with notes, not a structured transformation-type taxonomy |
| Event history (provenance events specifically) | **PARTIAL, conflated with business events** | See "Audit / Traceability" below — this codebase does not currently distinguish provenance events from business events from security audit events as three separate concerns; `backend/audit/routes.py` mixes stage transitions, scans, and transactions into one human timeline |
| Provenance graph (queryable relations: Produced By, Certified By, Published By, Licensed To, Sampled From, Version Of) | **MISSING as a queryable graph** | Only `based_on` (informal "Version Of") exists structurally; the other relation types named in Phase 1's Bloc 1 spec (`reports/02_GAP_ANALYSIS.md` row 2b) were never built |
| Heritage / long-term preservation & transfer | **IMPLEMENTED** | `backend/heritage/routes.py` — declare/claim/transfer/lineage endpoints, real and tested in Phase 1 audits |

## .FK

| Capability | Status | Evidence |
|---|---|---|
| Manifest / identity / content / provenance / rights / proof layers | **VERIFIED** | `backend/fk/models.py` (7-layer model), `backend/fk/packager.py`; unit-tested (`backend/tests/test_fk.py`, 7 tests passing, Phase 2/3) |
| Credentials layer inside .fk | **MISSING** | No VC/credential field in `backend/fk/models.py` — the "intelligence" layer is reserved for FREKANSLA (audio analysis), not credentials |
| Offline verification | **VERIFIED** | `backend/tests/test_fk.py:test_survival_offline_verification`; `verifier/python/verify_passport.py`, `verifier/js/verify_passport.js` — standalone, no-backend-call verifiers, real and shipped |
| Deterministic validation | **VERIFIED** | `backend/tests/test_fk.py:test_canonical_json_deterministic` |
| Extensions | **PARTIAL** | `IntelligenceLayer` is explicitly reserved/extensible ("Reserved for FREKANSLA integration") but no formal extension-registration mechanism exists beyond "add a field" |
| Version / lineage at the container level | **IMPLEMENTED** | `ManifestFK.fk_version = "0.1"` — single current version, no migration path defined yet for a hypothetical `0.2` |

## FREK Registry

| Capability | Status | Evidence |
|---|---|---|
| Namespace schema catalog | **VERIFIED** | Phase 1/2/3, `backend/registry/` — 8 namespaces, 21+ unit tests |
| Reconciliation with historical object types | **RECONCILED (2026-08-31)** | `docs/architecture/FK_OBJECT_TAXONOMY_RECONCILIATION.md` — `frek.work.work_type`'s enum is an exact, verified mirror of `.fk`'s `OBJECT_TYPES` (`backend/fk/models.py:18-19`); every `object_type` maps to `frek.work` (generic) plus, for `song`/`album`/`event`, a specific namespace (`frek.track`/`frek.album`/`frek.event`). `backend/registry/fk_taxonomy.py` + `backend/tests/test_registry_fk_taxonomy.py` (24 tests) make this a checked fact, not a claim. Neither taxonomy's terms were renamed (`song` stays `song` in `.fk`, `frek.track` stays the Registry's own KORA-facing term) — see the doc's "what this pass does NOT do" section for the deliberately-out-of-scope auto-mirroring question. |
| Persisted instance store | **IMPLEMENTED (2026-08-31)** | `POST/GET /api/v1/registry/objects/{namespace}` + `GET .../{namespace}/{frek_id}`, `backend/registry/routes.py`, `registry_objects` collection, schema-validated before insert. Write authority: OAuth2 client with `registry:write` (ISSUER) or `identity_engine` holder session (OWNER, forced to own `owner_id`). No event published (see Event Bus section: `object.created` stays `.fk`'s own, per the catalog's `producer: "fk"`). Live-tested: `backend/tests/test_registry_objects.py` (18 tests). Closes `docs/interfaces/KORA.md`/`LABELOS.md`'s "PROPOSED, NOT IMPLEMENTED" resolver gap. |

## FREK Verified

| Capability | Status | Evidence |
|---|---|---|
| Embeddable trust/verification badge | **IMPLEMENTED under a different name** | `backend/seal/` — "FREK Certified Seal" (`GET /seal.js`, `GET /seal/demo`) is the real, shipped implementation of the concept `frek_v3/docs/` refers to elsewhere as "FREK Verified": an embeddable script that verifies offline (Ed25519 + Merkle) in the visitor's browser and renders a signed status badge. `grep -rn "FREK Verified\|frek_verified" backend/ frontend/src/` → **zero matches** — the term "FREK Verified" itself is not used anywhere in code, only in `frek_v3/docs/`. Treat "FREK Verified" (docs) = "FREK Certified Seal" (code) as the same capability under two names, not two capabilities |

## FREKRAW / FREKANSLA

| Capability | Status | Evidence |
|---|---|---|
| FREKRAW | **`not_installed`, contract only** — unchanged | `ecosystem/registry.json`'s own classification, `ecosystem/contracts/frekraw.md`. Confirmed this phase: no FREKRAW business logic exists anywhere in `backend/` (correctly — the mission's own rule says "Do not move FREKRAW business logic into FREKCORE") |
| FREKANSLA | **`not_installed`, contract only** — unchanged | `ecosystem/registry.json`, `ecosystem/contracts/frekansla.md`. `backend/fk/models.py:IntelligenceLayer` is the one reserved integration point ("Reserved for FREKANSLA integration"), consistent with "FREKANSLA must consume FREKCORE identity/provenance/proof primitives, not duplicate them" — the reservation is a hook, not an implementation, which is correct per that rule |

## Events, Certificates, Permissions, Audit — see dedicated reports

- Events: `reports/20_EVENT_PRODUCERS.md`.
- Certificates: `reports/02_GAP_ANALYSIS.md` Bloc 5 (still MISSING as a first-class Academy concept; `backend/badges/` is a distinct CC2026 event-badge system, not certificates) — unchanged this phase, re-confirmed.
- Permissions: `docs/PERMISSION_MATRIX.md`.
- Audit/traceability reconciliation: **business events** (`backend/core/`, `backend/counter/` — CC2026 scoring), **provenance events** (`backend/heritage/`, `.fk`'s `TimelineLayer`), and **security audit** (`backend/audit_trail/`, Phase 2/3, append-only actor-attributed) are three genuinely distinct concerns in this codebase today, but only `audit_trail` was *designed* with that distinction explicit from the start — `backend/audit/` (Phase 1, human timeline) mixes stage/scan/transaction history without a formal category field. Not collapsed further this phase; not yet fully separated either — flagged in the backlog.

## Historical FREK Capabilities (`backend/frek/`, founder decisions D1–D6, 2026-08-31)

Full reconciliation: `reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md`.
The founder has decided all 6 items below are **required** capabilities
FREKCORE must eventually carry. None is marked IMPLEMENTED here merely
because a historical `backend/frek/` prototype exists for it — per the
reconciliation report's own evidence, none of the five persists data
durably, none is authenticated, and none has been demonstrated (not
merely asserted) to have the properties its own historical docstrings
claim (e.g. "infalsifiable" fingerprint robustness — unproven; IVFFlat-
accelerated similarity search — the code always falls back to a linear
in-Python scan regardless of backend, contradicting its own docstring).

| Capability | Status | Evidence |
|---|---|---|
| Signal / Audio Fingerprinting (D1) | **DOCUMENTED_ONLY (prototype), FOUNDER-REQUIRED** | `backend/frek/nodes/node01_extraction.py`/`node02_identity.py` — real DSP extraction code, no durable storage, no auth, fingerprint-vs-identity conflation not yet resolved in code. Not IMPLEMENTED against the target model (§D1 of the reconciliation report) |
| Creative Lifecycle (D2) | **DOCUMENTED_ONLY (prototype), FOUNDER-REQUIRED** | `backend/frek/nodes/node03_cycle.py` — real 5-stage vocabulary (matches `frek_v1`'s exactly), in-memory only, no auth, no idempotency |
| Relationship / Provenance Graph (D3) | **DOCUMENTED_ONLY (prototype), FOUNDER-REQUIRED** | `backend/frek/nodes/node06_reseau.py` — real 17-relation taxonomy, in-memory only, all 7 read routes unauthenticated (the most acute privacy gap of the five per the reconciliation report §P) |
| Offline Proof Transport (D4) | **DOCUMENTED_ONLY (prototype), FOUNDER-REQUIRED** | `backend/frek/nodes/node07_transmission.py` — real packet wire format and protocol registry, transports simulated in-memory only (no actual BLE/NFC/etc. I/O), watermark encoding unvalidated experimentally |
| Human-Readable Technical Evidence (D5) | **DOCUMENTED_ONLY (prototype), FOUNDER-REQUIRED** | `backend/frek/nodes/node09_juridique.py:create_attestation` — formats caller-supplied, unverified data as an official-sounding document; verifies nothing against actual FREKCORE state. `backend/notary/` remains the real, modern attestation mechanism this route does not use |
| Evidence Semantics (D6) | **GAP, cross-cutting rule, FOUNDER-REQUIRED** | Not a capability with its own routes — a rule needed so D1–D5 (and everything else) never silently promote a CLAIM to a VERIFIED fact. `proof_engine.ProofState` already covers "how strong is this proof"; CLAIM/EVIDENCE as named concepts is the one genuinely new primitive the evolved canonical model (§E of the reconciliation report) requires |

## Scope note

This matrix covers every domain the directive named. It does not enumerate every individual historical document line-by-line into a numbered `requirement_id` table — with 30+ backend modules, a decade of `memory/` and `frek_v3/docs/` documents, and this session's remaining budget, that would either take many more hours of reading or produce a table padded with low-information entries. What is here is real: every row was checked against actual code (`grep`, direct file reads, or live requests against the real server this session booted), not inferred from a document's claim alone. Continuing this matrix to full per-document coverage is `reports/FREKCORE_COMPLETION_BACKLOG.md`'s P2 item "Complete exhaustive documentation reconciliation."
