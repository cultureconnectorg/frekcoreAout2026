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
| Identity lifecycle: revoke | **PARTIAL** | `frek_v1/identity.py:200` has `POST /{frek_id}/revoke`; `identity_engine` has none (confirmed, `reports/02_GAP_ANALYSIS.md` Phase 1, re-confirmed Phase 3) |
| Identity lifecycle: renew/update | **PARTIAL** | Same split as revoke: `frek_v1` has `/renew` (`frek_v1/identity.py:256`); `identity_engine` has none |
| Identity lifecycle: merge | **MISSING** | No merge logic in either system (grep negative, Phase 1 and re-confirmed) |
| Identity lifecycle: archive | **MISSING** | No archive logic in either system |
| Identity linking (objects to identity) | **IMPLEMENTED** | `identity_engine/routes.py: POST /link-object`, `GET /{frek_id}/objects` |
| Pseudonymous / anonymous identities | **IMPLEMENTED** | `backend/moment/routes.py` — explicit doctrine: "anonyme, sans auth", `PUBLIC_CLIENT_ID = "public-window-1"` |
| Organization identities | **DOCUMENTED_ONLY** (schema exists, no backing store) | `backend/registry/schemas/v1/frek.organization.schema.json` (Phase 1) defines the shape; no `POST`/persisted-instance route exists anywhere in the codebase to actually create one |
| Device identities | **PARTIAL** | `backend/fingerprint/routes.py: POST /observe/device` records device-observation data, but there is no first-class "device identity" record type distinct from a FREK-ID |
| Identity recovery | **MISSING** | No recovery flow found (`heritage/claim` is inheritance-style transfer to a *beneficiary*, not self-recovery — see Cultural Provenance below) |
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
| Issuer / Holder / Verifier roles | **IMPLEMENTED conceptually, not as first-class permission roles** | The DID/VC/EUDI code implements the *protocol* roles; `backend/permissions/models.py`'s `Role` enum (Phase 2/3) does not include Issuer/Holder/Verifier — a gap between the two systems, not yet reconciled |
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
| Reconciliation with current Proof Engine | **NOT DONE — explicitly flagged, not duplicated** | `backend/proof_engine/` (Phase 2/3) does not reference FAP concepts at all; this matrix does not recommend merging them blind — see `reports/FREKCORE_COMPLETION_BACKLOG.md` P2 |
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
| Reconciliation with historical object types | **PARTIAL** | `frek.artist/track/album/work/certificate/organization/wallet/event` (Registry, new) vs. `.fk`'s `object_type` enum (`song, album, event, heritage, photo, captation, document, artwork, other`, `backend/fk/models.py:18-19`, pre-existing) — **these are two different taxonomies that were not reconciled into one**. A `frek.track` (Registry) and a `.fk` with `object_type="song"` describe overlapping but not identical things |
| Persisted instance store | **MISSING** | Schema-only, confirmed repeatedly since Phase 1 |

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

## Scope note

This matrix covers every domain the directive named. It does not enumerate every individual historical document line-by-line into a numbered `requirement_id` table — with 30+ backend modules, a decade of `memory/` and `frek_v3/docs/` documents, and this session's remaining budget, that would either take many more hours of reading or produce a table padded with low-information entries. What is here is real: every row was checked against actual code (`grep`, direct file reads, or live requests against the real server this session booted), not inferred from a document's claim alone. Continuing this matrix to full per-document coverage is `reports/FREKCORE_COMPLETION_BACKLOG.md`'s P2 item "Complete exhaustive documentation reconciliation."
