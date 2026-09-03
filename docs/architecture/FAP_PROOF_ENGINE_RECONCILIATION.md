# FAP ↔ Proof Engine Reconciliation

Per the founder's instruction: complete the architectural reconciliation
between the FREK Attestation Protocol (FAP, hardware capture/device
attestation) and this codebase's software-side Proof Engine
(`backend/proof_engine/`) and FREK-Chain (`backend/notary/`) — preserving
historical FAP guarantees, determining exactly how it relates to each
named concept, and resolving what evidence allows without inventing a
second proof system.

**Primary sources**: `frek_v3/docs/FREK_Attestation_Protocol_v0.1.md` — an
800-line, complete, self-contained hardware attestation specification
(binary proof format, key derivation, verification algorithm, threat
model, test vectors) — and `frek_v3/reference_verifier/` — a **real,
working Python reference implementation** of that exact spec (parser,
crypto primitives, verifier, a simulated device for generating test
proofs, a device registry, 16 golden test vectors — all passing,
`python -m pytest frek_v3/reference_verifier/test_frek_verifier.py`).
Correction of an earlier, wrong assumption made while researching this
pass: FAP is **not** unimplemented anywhere — `ecosystem/registry.json`
already correctly documents its status as `"specified_isolated"`, with
`"integration_points": []`. What is genuinely missing is not the
verification logic itself but its connection to `backend/` — confirmed
by `grep -rn "PUF\|FAP\|Attestation" backend/` (no matches outside
comments citing this exact gap) and the registry entry's own
`"note": "Isolated from /app/backend/... NO backend endpoint yet."` That
isolation, not an absence of implementation, is the starting fact this
reconciliation works from.

## The headline finding: FAP and the Proof Engine are not competing —
## they are two orthogonal trust axes that were always meant to compose

- **The Proof Engine's `ProofState`** (`backend/proof_engine/models.py`,
  reports/18_RUNTIME_VALIDATION.md's 6-level classification) answers:
  *how strongly is this hash's existence and timing anchored?*
  (`fingerprint → local_proof → signed_proof → timestamp_proof →
  opentimestamps_proof → external_anchor_proof`.) It says nothing about
  *who* or *what* produced the hash in the first place.
- **FAP's attestation levels (L0/L1/L2)** answer the complementary
  question: *how trustworthy is the SOURCE that produced this hash?*
  (L0 = software-only, no hardware root of trust; L1 = device-bound key,
  no secure boot; L2 = hardware-attested, PUF-derived key, firmware
  measured at boot.)

A single captured audio fingerprint can be **both**: FAP-L2-attested (the
capturing device proves, offline, that the hash it produced wasn't
tampered with before signing) **and** carried through the existing Proof
Engine pipeline exactly as any other input is today (hash-chained into
FREK-Chain, Ed25519-signed by FREKCORE's own institutional key, OTS-
submitted, Bitcoin-anchored). These are two independent, stackable proof
layers, not two answers to the same question — building FAP support does
not mean replacing or duplicating the Proof Engine, and building it later
does not require touching the Proof Engine's existing model at all.

## Point-by-point, per the founder's own list

| Concept | How FAP relates | Evidence |
|---|---|---|
| **FREK Object / `.fk`** | FAP's L2 proof (283 fixed bytes: `AUDIO_HASH`, `FINGERPRINT_HASH`, `CONTEXT_HASH`, `FIRMWARE_HASH`, device `PUB_KEY`, `SIGNATURE`) is exactly the kind of artifact the `.fk` spec's own `credentials`/`proofs` layers already have a named slot for (`FREK_Object_Model_Specification_v0.1.md` §2: `credentials.FREK VC` with `type: FREKCaptureCredential`). The real code's `fk/models.py` `ProofLayer` (`content_hash`, `signatures`, `BlockRef`, `BtcAnchor`) has no FAP-specific field today — additive, not a redesign, when built: one new optional field carrying the raw/parsed FAP proof. |
| **FREK-ID** | FAP's `DEVICE_ID` (16 bytes, UUIDv4-shaped) is a device identity, distinct from a Person's FREK-ID — matches `docs/architecture/FREK_ID_ENTITY_TAXONOMY.md` §2.6's finding that `did:frek:device-<uuid>` is DOCUMENTED_ONLY, never minted. FAP does not require device identities to be FREK-IDs to function (its own verification algorithm needs only a `device_registry: {device_id: pub_key}` mapping, §10.1) — typed device DIDs (Contradiction C6) and FAP integration are related but independently gated; neither blocks the other. |
| **Provenance** | FAP's `DEVICE_TIME` and `FIRMWARE_HASH` are *signed fields* attesting to capture context — exactly the provenance guarantees `.fk`'s `provenance.creation` (timestamp, lieu, device) layer already has a named slot for, per the Object Model spec. No code change needed to the `.fk` provenance *concept* — only to populate that layer with FAP data once hardware exists. (Corrected from an earlier draft of this document — see §"A corrected finding" below: `COUNTER`/`FIRMWARE_HASH` are signed data, not key-derivation inputs.) |
| **Signatures** | FAP uses **NIST P-256 / ECDSA**, raw `r\|\|s` (no ASN.1/DER), deliberately different from every other signature in this codebase (Ed25519 — `passport/keys.py`, `did/vc.py`, notary blocks). This is a **real, documented cryptographic divergence, not a contradiction to fix**: hardware key derivation from a PUF response needs a curve/scheme suited to constrained-device HKDF derivation; there is no requirement anywhere that every signature in the system use the same curve, and Ed25519 remains exactly what FREKCORE's own platform-level signing already correctly uses. "Do not silently replace historical cryptographic semantics" — this reconciliation does not touch FAP's P-256 choice, nor propose migrating the platform's Ed25519 to match it. |
| **Device identity** | See "FREK-ID" row above — `DEVICE_ID` plus the PUF-derived `DEVICE_ROOT_KEY` (§5.3, HKDF-SHA256 over `PUF_RESPONSE` + fab/wafer/die metadata) is FAP's own, complete device-identity model. Nothing in `backend/` today represents a device as an identity at all (confirmed, taxonomy §2.6) — FAP is the only place this concept is even specified. |
| **Counters / nonces / replay protection** | Fully self-contained inside FAP, verified entirely offline (§10.1's `verify_proof`): a monotonic per-device `COUNTER` (rejects `counter <= last_counter`) plus a verifier-supplied `NONCE` for the challenge-response mode. `grep -rn "counter\|nonce\|replay" backend/notary/ backend/proof_engine/` returns **no matches** — neither module has any counter/nonce/replay concept today, and none is needed for FAP's own protection to work; FAP does not depend on the Proof Engine gaining one. |
| **Proof Engine** | See headline finding above — orthogonal axis, not a replacement. When FAP is eventually implemented, the natural integration point is a **new, additive `ProofState`-adjacent field** on `ProofReceipt` (e.g. `device_attestation_level: Optional[Literal["L0","L1","L2"]]`) or a small sibling verifier module (`backend/fap/` or `proof_engine/fap_verifier.py`) that runs FAP's own `verify_proof` algorithm and hands its result to the existing pipeline as an input, not a fork of it. |
| **FREK-Chain** | `backend/notary/chain.py`'s `append_block(payload_type, payload_id, payload_data, ...)` is already a fully generic, schema-free extensibility point — the exact same one this session used for `identity_recovery`, `identity_reconciliation`, `renewal`, and (pre-existing) `heritage_transfer`. A FAP L2 proof would notarize as `payload_type="fap_capture_attestation"` with the parsed proof fields as `payload_data`. **Zero changes needed to `notary/chain.py` for this** — confirmed by reading its actual signature, not assumed. |
| **Timestamps / anchors** | FAP's `DEVICE_TIME` is the device's own local clock claim (§6: explicitly *not* trusted on its own — the spec's own §6.2 rules require the verifier's received-time and device-time to be reconciled, with drift bounds); FREK-Chain's `timestamp` and the OTS/Bitcoin anchor remain the actual trusted-timestamp mechanism, unchanged. FAP's device time is provenance metadata *about* the capture, not a competing timestamping authority — consistent with Proof Engine's own `TIMESTAMP_PROOF`/`OPENTIMESTAMPS_PROOF`/`EXTERNAL_ANCHOR_PROOF` states, which FAP does not touch or need to touch. |
| **Offline verification** | FAP is explicitly designed to be fully verifiable **without any FREKCORE involvement** (§10.2: "Aucun appel à FREK Core n'est nécessaire" — only the device's public key, ECDSA P-256 + SHA-256, and local counter state are needed). This is a genuine, deliberate FAP guarantee that must be preserved exactly as specified, not routed through the Proof Engine's own (online, MongoDB-backed) verification path — the two remain independently invocable, matching the spec's own design intent. |

## A refinement between the spec doc and the reference implementation

`frek_v3/reference_verifier/README.md`'s own "5 points verrouillés" table
records that the reference implementation refined `DEVICE_ID` from the
spec doc's independent 16-byte UUID-like field to
`Truncate(SHA-256(AK_pub), 16)` — derived from the device's own
attestation public key rather than assigned separately. This is an
internal evolution within the FAP work itself (the reference
implementation postdates and refines the spec doc, both under `frek_v3/`),
not a contradiction between FAP and this codebase's Proof Engine — noted
here for completeness, per "where the historical specification and
implementation disagree, document the contradiction," so a future reader
building against `frek_v3/` doesn't have to reconcile the two documents
themselves.

## What this reconciliation resolves vs. what remains

**Resolved from evidence, no founder decision needed**: FAP and the Proof
Engine are complementary, not competing; no code conflict exists because
neither currently touches the other; the eventual integration shape
(additive fields/payload types, not a redesign) is already implied by how
every other extensibility point in this codebase already works, so no new
architectural pattern needs inventing when hardware arrives.

**Not resolved here, and correctly not attempted**: this reconciliation
does **not** wire `frek_v3/reference_verifier/` into `backend/` (there is
no hardware to test against yet, and per this mission's own repeated
rule, building an unused integration with no evidence it is needed yet
would be inventing scope) and does not resolve Contradiction C6 (typed
device DIDs) — both remain open, tracked exactly where they already were
(`docs/architecture/FREK_ID_CANONICAL_MODEL.md` §4,
`docs/architecture/FREK_ID_ENTITY_TAXONOMY.md` §2.6). Neither blocks
freeze on its own: FAP has a real, tested, isolated implementation with
no consumer wired to it yet, and this reconciliation found no code-level
contradiction that needs fixing before that wiring happens — only clarity
about exactly where it plugs in (additive `ProofReceipt` field or sibling
verifier module, `payload_type="fap_capture_attestation"` on the existing
`notary.chain.append_block`, `frek_v3/reference_verifier`'s own
`FrekVerifier.verify()` reused directly rather than re-implemented), which
this document now records so the next pass that touches Luciole/FAP
hardware doesn't have to re-derive it.

## Addendum (2026-08-31, exhaustive documentation reconciliation pass)

Per the founder's instruction to reconcile every historical FREK document,
not just the primary spec: seven `frek_v3/docs/` documents had zero
cross-references anywhere in `reports/`/`docs/` before this pass
(confirmed by `grep -rl <filename> reports/ docs/`). All seven are
supporting material for the same FAP/hardware-attestation work this
document already reconciles — none introduces a requirement on
`identity_engine`, the Registry, or any other part of `backend/` beyond
what's already covered above. Reconciled here, in the order their own
internal cross-references imply:

### A real, resolvable contradiction found and fixed

**`FREK_Cryptographic_Architecture_Review_v0.1.md`** is an explicit,
authored correction to `FREK_Attestation_Protocol_v0.1.md` (both produced
in the same 2026-08-10 session per `BILAN_DISCUSSION_FREK_V3.md`'s own
account of its two deliverables). Its executive summary states directly:
*"corrige une construction présente dans le FREK Attestation Protocol
v0.1 : la Device Root Key ne doit en aucun cas dépendre du compteur
monotone ni du hash du firmware."* The correction: the Attestation Key
(AK) is derived once at boot from the Device Root Key (DRK) via HKDF and
stays stable for the device's life; `COUNTER` and `FIRMWARE_HASH` are
**signed fields** in the proof message, never key-derivation inputs —
mixing the two roles was identified as breaking firmware updates and
incident recovery.

This directly contradicted this document's own earlier §"Point-by-point"
table above (now corrected), which had repeated FAP v0.1's superseded
claim uncritically. Resolved from evidence, not a founder question: (1)
the Crypto Review is later, explicit, and reasoned; (2)
`frek_v3/reference_verifier/frek_crypto.py`'s actual working code
implements the corrected design (`derive_device_id(ak_pub)` — a stable
per-device key — not a per-proof, counter-bound one; `COUNTER`/
`FIRMWARE_HASH` appear in the signed `MESSAGE`, never in a KDF call).
The reference implementation being the ground truth for "what's actually
built" settles which of the two documents is authoritative.

### The full key hierarchy (preserved terminology, not previously recorded anywhere in `docs/`)

`FREK_Cryptographic_Architecture_Review_v0.1.md` §2 defines four
HKDF-derived keys, all descending from one immutable, PUF-derived,
never-exported **Device Root Key (DRK)** — domain-separated by HKDF
`info` string, never reused across roles:

- **Attestation Key (AK)** — signs FREK proofs (the one FAP L2 actually
  uses); public key exportable via `GET_IDENTITY`.
- **Firmware Key (FK)** — verifies firmware signatures at secure boot;
  per `FREK_V3_Engineering_Exploded_View_v0.2.md`'s own v0.1→v0.2
  correction #1, FK is actually **FREK Authority's own public key**
  baked in at manufacture, not a device-derived key — named here exactly
  as the corrected document names it, not the superseded v0.1 framing.
- **Communication Key (CK)** — optional internal bus encryption.

None of these are implemented in `backend/` (confirmed, same grep as the
rest of this document) — DOCUMENTED_ONLY, consistent with every other FAP
finding here.

### DSP/Fingerprint objective — a product decision already made within `frek_v3/` itself

`FREK_DSP_Fingerprint_Specification_v0.1.md` names four possible
fingerprinting objectives — **Identification** (exact-copy detection, zero
tolerance), **Similarity** (catalog/recommendation clustering),
**Provenance** (survives re-encoding, not re-capture — proves "this signal
came from this microphone at this instant"), **Resistance** (survives any
common transformation, streaming-service-grade robustness) — each with
real, named tradeoffs (false-positive/negative rate, DSP complexity). The
document's own §2 makes and justifies a recommendation: **Provenance
(Objective C)** as FREK V3's primary objective, because it is "the
objective most aligned with FREK's promise" and is realizable without a
neural model. This is a recorded architectural recommendation, not yet
confirmed as founder-locked the way the crypto/PUF/secure-boot design is
— `FREK_V3_Engineering_Exploded_View_v0.2.md`'s own final synthesis (§8)
lists "DSP Spec v0.1" under "À DÉFINIR" (still to be finalized), not
under "VERROUILLÉ" (locked) alongside the crypto/PUF/key-hierarchy/
secure-boot/device-ID/TRNG work. Recorded as DOCUMENTED_ONLY, with the
recommendation preserved by name (Objective C / Provenance) rather than
re-derived if a future pass picks this up.

### Overall FREK V3 hardware maturity (the roadmap's own honest self-assessment)

`FREK_V3_Architecture_Review_Final.md` names three maturity levels —
**Concept** (dépassé/superseded), **Architecture** (current — "hardware +
crypto + DSP + Core fonctionnent ensemble" on paper), **Engineering**
(next — "bits exacts, timings, RTL, consommation, résultats
expérimentaux") — and states plainly: *"La faisabilité technique n'est
PAS encore prouvée. Elle est suffisamment définie pour être testée."*
Its own explicit "what NOT to do now" list (contact a fab, price an NRE,
commit to a final certification profile, freeze the fingerprint algorithm,
promise a tape-out) rules out exactly the kind of premature hardware
commitment this reconciliation pass has also avoided. `FREK_V3_Roadmap_
Next_Lock_v0.2.md` names the concrete next deliverable as **Golden
Vectors + Rust Verifier** (a second, Rust reference implementation that
must byte-for-byte match the existing Python one's outputs) — not yet
started; `frek_v3/reference_verifier/`'s 16 golden test vectors are the
Python half of that pair, already real and passing.

### Documents given lighter treatment, and why

`BILAN_DISCUSSION_FREK_V3.md` is a session recap that itself summarizes
the other six documents (its own §3 "Livrables produits" lists them) —
reconciling it item-by-item would double-count content already reconciled
above from its primary sources. `INSTRUCTIONS_EMERGENT.md` is developer
onboarding instructions for the Emergent.sh coding-assistance platform
("Instructions pour l'équipe" — how to set up and validate the reference
verifier in that tool), not a FREK product/requirements document at all —
no requirement to extract. Both read in full to confirm this triage was
correct, not skipped on assumption.

### Net effect on this reconciliation's conclusions

No change to the headline finding (FAP and the Proof Engine are
orthogonal, not competing) or to the "not implemented, correctly deferred"
verdict — every one of these seven documents is hardware-attestation
material with zero backend code implementing it. The one substantive
correction (key derivation) sharpens this document's own accuracy without
changing what it recommends or what remains deferred.
