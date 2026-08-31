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
| **Provenance** | FAP's `DEVICE_TIME`, `FIRMWARE_HASH`, and the counter-bound signing key (§5.4: the signing key is derived from `COUNTER \|\| FIRMWARE_HASH`, so a firmware change or a replayed counter changes the effective key) are exactly the provenance guarantees `.fk`'s `provenance.creation` (timestamp, lieu, device) layer already has a named slot for, per the Object Model spec. No code change needed to the `.fk` provenance *concept* — only to populate that layer with FAP data once hardware exists. |
| **Signatures** | FAP uses **NIST P-256 / ECDSA**, raw `r\|\|s` (no ASN.1/DER), deliberately different from every other signature in this codebase (Ed25519 — `passport/keys.py`, `did/vc.py`, notary blocks). This is a **real, documented cryptographic divergence, not a contradiction to fix**: the spec's own rationale (§5.4) is that hardware key derivation from a PUF response needs a curve/scheme suited to constrained-device HKDF derivation and per-counter key rotation; there is no requirement anywhere that every signature in the system use the same curve, and Ed25519 remains exactly what FREKCORE's own platform-level signing already correctly uses. "Do not silently replace historical cryptographic semantics" — this reconciliation does not touch FAP's P-256 choice, nor propose migrating the platform's Ed25519 to match it. |
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
