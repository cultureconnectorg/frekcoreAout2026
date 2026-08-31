# FREK-ID Reconciliation Architecture

Per founder directive §5–6 (`docs/decisions/0001-founder-decisions-2026-08-31.md`): Contradiction C1 is resolved as **reconcile, do not replace** — one coherent FREK-ID trust model, multiple technical subsystems underneath it. This document maps the capability chain the directive specifies and names which module currently owns each capability, as the prerequisite to any resolver work (§6) — not the resolver itself, which is out of scope until this mapping is agreed and the missing cells are filled or explicitly deferred.

```
FREK-ID CONCEPT
  ↓
IDENTITY DATA        → who currently stores "this is a FREK-ID and what it is"
  ↓
AUTHENTICATION        → how a caller proves it acts as/for a FREK-ID
  ↓
CREDENTIALS            → what verifiable claims can be issued about it
  ↓
LIFECYCLE               → what state transitions exist
  ↓
PROVENANCE               → what history/chain-of-custody is tracked
  ↓
AUTHORITY                 → who can mutate it and under what permission
  ↓
PROOF                      → what cryptographic/timestamped evidence exists
  ↓
REVOCATION                  → how it is invalidated
  ↓
RECOVERY                     → how access is restored if lost
  ↓
VERIFICATION                  → how a third party checks all of the above
```

## Capability ownership map

| Capability | `frek_v1` | `identity_engine` | `backend/frek/` (legacy, work-scoped) | `did`/`vc` | `notary`/`passport` |
|---|---|---|---|---|---|
| **IDENTITY DATA** | `frek_identities` collection — email-hash-attributed, OAuth2-client-scoped, event-context (`EmitRequest.event`) | `frek_persons` collection — WebAuthn-credential-attributed, no client scoping | In-memory only (no persistent collection — `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`'s central finding), subject = a creative work, not a person | Resolves *either* system's `frek_id` as `did:frek:{frek_id}` — does not store identity data itself, reads through | Passport's Ed25519 key is shared platform-wide, not per-identity |
| **AUTHENTICATION** | OAuth2 client-credentials grant (the *client* authenticates, not the identity's own holder) | WebAuthn/Passkey ceremony (the holder authenticates directly — this is the one system where the *subject itself* proves possession) | None | N/A (resolution is public, per spec) | N/A |
| **CREDENTIALS** | None issued (no VC/VP integration) | None issued | None | **Owns this**: `did/vc.py` issues/verifies VCs against either system's `frek_id`, `core/` issues SD-JWT | Passport issues a signed Merkle-root claim set (`.fk`/passport "credential", pre-dates the W3C VC integration, not the same artifact) |
| **LIFECYCLE** | **Owns this** for person/event identities: `GENESIS→WORKSHOP→METAMORPHOSE→EMISSION→LEGACY`, `STAGE_ORDER`, explicit stage-recording endpoints | None (confirmed MISSING every phase) | **Owns this** for work-certification identities: `GENESIS→WORKSHOP` wired (only 2 of 5 stages have routes), non-persistent | N/A | N/A |
| **PROVENANCE** | Stage history is itself a provenance record (append-only per `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s Identity section) | None | `backend/frek/`'s NODE06 (Réseau) graph models creator/place/work relations, but is non-persistent (same finding) | N/A | `heritage/` (chain-of-custody transfers), `.fk`'s provenance/lineage fields |
| **AUTHORITY** | `require_permission(...)` (OAuth2 client scope) gates mutation | Session-token gates mutation (no fine-grained scope beyond "is this session") | **None found** — no `Depends(...)` anywhere in the module | N/A | `notary`'s routes: `Depends(require_permission("emit"))` (confirmed real this phase, see `docs/PERMISSION_MATRIX.md`'s correction note) |
| **PROOF** | Notary block created on emission (`identity/emit` triggers `notarize_event`, confirmed Phase 3) | None wired to notary (a real gap — `identity_engine`'s own lifecycle events are not notarized) | None (no `notary`/`proof_engine` usage found) | N/A | **Owns this**: hash-chain blocks, OTS submission, Bitcoin anchoring attempt (`reports/18_RUNTIME_VALIDATION.md`'s 6-level classification) |
| **REVOCATION** | **Owns this**: `POST /{frek_id}/revoke` (`frek_v1/identity.py:201`), live-tested (`test_governance_phase1.py`) | **Now owns this too** (P1, implemented 2026-08-31): `POST /{frek_id}/revocation` (`identity_engine/routes.py`) — see the implementation update below for why the path is `/revocation`, not `/revoke` | N/A (no revoke concept — a certified work isn't "revoked" the way a person's identity is; a legal-retraction concept, if wanted, would be new, not copied) | N/A | N/A |
| **RECOVERY** | **MISSING** (no recovery flow found in either identity system) | **MISSING** | N/A | N/A | N/A |
| **VERIFICATION** | `GET /{frek_id}` (status, public, no-auth by design) | `GET /me`, `/{frek_id}/objects` (session-scoped) | `GET /verify/{frek_id}` (reads the in-memory/non-persistent store) | **Owns cross-system verification**: `did/routes.py:resolve_did`, offline verifier (`verifier/python/verify_passport.py`) | `notary/routes.py:GET /chain/verify`, `passport`'s own offline verification |

## What this map makes explicit

1. **No single module owns the full chain for any one FREK-ID today.** A `frek_v1`-minted identity has lifecycle + revocation + proof but no VC/credential issuance of its own (it can be *resolved* as a DID and have a VC issued *about* it via `did/vc.py`, which is a different thing than the identity system itself issuing one). An `identity_engine`-minted identity has real per-subject authentication (WebAuthn) but no lifecycle, no revocation, no proof integration at all.
2. **§7's "missing lifecycle capabilities" are now precisely scoped**, not a vague TODO: `identity_engine` needs revoke, update, archive, and (per this map) has never had renew or recovery either — but per §7's explicit instruction, these should not be *copied* from `frek_v1`'s implementation without checking semantic equivalence first:
   - `frek_v1`'s `revoke` operates on an OAuth2-client-scoped identity where the *client* revokes on the holder's behalf (no holder-initiated revoke exists). `identity_engine`'s WebAuthn model has a real per-subject session — a holder-initiated revoke is semantically *possible* there in a way it structurally is not for `frek_v1`. **These are not the same operation wearing different names — building `identity_engine`'s revoke as a literal port of `frek_v1`'s would under-use the very capability (subject-initiated action) that makes `identity_engine` the more modern system.** Recommendation: design `identity_engine`'s revoke as holder-initiated-by-default (with an admin/client override path modeled on, not copied from, `frek_v1`'s), not implemented in this pass — new capability work, out of scope for a reconciliation-mapping document.
   - `renew`/`recovery` have no existing implementation in *either* system to model from — these are genuinely new capability designs, not adaptations.
3. **`identity_engine`'s lifecycle events are never notarized.** `frek_v1`'s `identity/emit` triggers `notarize_event`; `identity_engine`'s `/init` does not. This is a real, previously-unnoted gap: the newer, WebAuthn-based system — which `docs/interfaces/*.md` exposes as the trust root external CVLN systems should rely on — has weaker cryptographic-proof backing than the older one it's meant to supersede. Recorded here, not fixed in this pass (wiring notarization into `identity_engine` is real capability work with its own regression-testing needs, consistent with how `identity.created`'s Audit Trail wiring was done carefully in Phase 3 rather than blindly).

## Toward the canonical resolver (§6) — contract sketch, not implementation

A future canonical resolver should answer, for any `frek_id` string, without the caller needing to know which system minted it:
- Which system owns it (`frek_v1` | `identity_engine` | neither — could be a `backend/frek/`-minted work-certification ID, a structurally different namespace per `docs/architecture/FREK_ID_CANONICAL_MODEL.md` §2)
- Its current lifecycle stage, if the owning system has one
- Whether it is active, revoked, or expired
- Where to find its DID Document, credentials, and proof chain

This is deliberately **not implemented in this pass**. Per founder directive §6: "Do NOT implement this blindly. First document the contract. Preserve backward compatibility." The map above is that documentation step; the resolver itself is `reports/FREKCORE_COMPLETION_BACKLOG.md`'s own item (P1, already listed as depending on this document).

## P1 implementation update (2026-08-31)

`identity_engine` now implements `revoke`, `update`, and `archive` as
holder-initiated-by-default (with an `X-Admin-Key` override), exactly as
recommended above — see `backend/identity_engine/routes.py`'s LIFECYCLE
section and `backend/tests/test_identity_lifecycle.py`. Notes:

- **A path collision was found and fixed while building this.**
  `frek_v1` already owns `POST /{frek_id}/revoke` at the identical mounted
  path `/api/v1/identity/{frek_id}/revoke` (both routers share that
  prefix). FastAPI resolves overlapping path+verb registrations across
  routers by registration order, silently — no error, no warning — and
  `frek_v1`'s router registers first in `server.py`, so a same-named
  `identity_engine` route would have been permanently dead code, shadowed
  on every call. This is a concrete, load-bearing instance of Contradiction
  C1 (`reports/FREKCORE_CONTRADICTIONS.md`): two systems sharing a URL
  namespace they don't share an identity model for. Reordering registration
  would not fix it — it would just make whichever system moved second the
  shadowed one, since the router dispatch has no way to know which identity
  system a given `frek_id` string belongs to (that's exactly the resolver
  gap §6 above describes). The fix taken: `identity_engine`'s new endpoint
  is `POST /{frek_id}/revocation` (a noun, distinct from `frek_v1`'s verb
  path) — `frek_v1`'s route is untouched (no breaking change, per founder
  directive §28), and `identity_engine`'s is now a live, reachable route.
  `PATCH /{frek_id}` and `POST /{frek_id}/archive` do not collide with any
  `frek_v1` route (checked against every `frek_id`-scoped route in
  `frek_v1/identity.py`: `/activate`, `/status`, `/revoke`, `/renew`,
  `/detail`, `/qr.png`).
- Revoke is immutable and idempotent, notarized (`payload_type:
  identity_revocation`), and blocks future authentication/registration for
  that `frek_id`. Archive is a distinct, softer, non-notarized state (not a
  security event) and does not (yet) have an unarchive flow — a new
  capability, not modeled on an existing one.
- Building this surfaced a genuine, separate, pre-existing security gap:
  `register_begin`/`register_complete` let anyone who knew a `frek_id`
  (never meant to be secret — it's what `GET /{frek_id}` and QR codes
  resolve) register a *second*, competing Passkey and take over an
  already-credentialed identity, which would have made `/revocation`
  trivially bypassable (revoke, then just re-register). Fixed alongside
  this work: adding a credential to an identity that already has one now
  requires the holder's own session; claiming a fresh, zero-credential
  identity (the real bootstrap case) stays open.
- `renew` and `recovery` are still not implemented for `identity_engine` —
  as noted above, neither system has an existing implementation to model
  them from, so they remain open P1 backlog items, not done in this pass.

## A second consumer of this map: fingerprint/geo per-holder authorization (2026-08-31)

`reports/22_P0_SECURITY_CLOSURE.md` gated `fingerprint`/`geo`'s consent and
sensitive-read routes behind a shared ADMIN key as an interim fix, flagging
"true per-holder authorization" as blocked on this very document landing.
It has, so this closes that gap
(`reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #3):
`backend/fingerprint/routes.py` and `backend/geo/routes.py` both now
accept `identity_engine`'s `X-FREK-Session` as primary authority (admin
key kept only as override), using the exact split this document already
describes — `frek_v1` has no holder-session concept to check against at
all, so the only live per-holder proof mechanism is `identity_engine`'s.

The realistic wrinkle this map's abstract split becomes concrete for:
fingerprint/geo data is keyed by whatever `frek_id` an external caller
supplies, commonly a `frek_v1`-minted UUID4 (a plain `uuid.uuid4()`
string, `frek_v1/utils.py:generate_frek_id`) — a different, structurally
distinguishable ID space from `identity_engine`'s own `id-{hex}-{hex}`
FREK-IDs. A holder session can never *directly* match such a `frek_id`.
The fix reuses `identity_engine`'s pre-existing `linked_objects` field
(populated by the already-existing `POST /identity/link-object`, meant
for exactly "this object is mine") as the second, indirect proof path —
no new mechanism invented, an existing one applied to a new consumer.

## Explicit non-goals of this document

- Does not decide whether `frek_v1` and `identity_engine` should ever merge into one collection (§5: still open, deferred to whoever makes that call with this map in hand).
- Does not implement `renew`/`recovery` for `identity_engine`, notarization wiring for `identity.created`, or the canonical resolver itself — `revoke`/`update`/`archive` are now implemented (see the P1 update above).
- Does not touch `backend/frek/`'s (work-certification) lifecycle beyond citing it — its fate is `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`'s to decide.
