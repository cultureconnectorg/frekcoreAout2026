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
| **REVOCATION** | **Owns this**: `POST /{frek_id}/revoke` (`frek_v1/identity.py:201`), live-tested (`test_governance_phase1.py`) | **MISSING** (confirmed every phase — this is the "missing lifecycle capability" founder directive §7 names) | N/A (no revoke concept — a certified work isn't "revoked" the way a person's identity is; a legal-retraction concept, if wanted, would be new, not copied) | N/A | N/A |
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

## Explicit non-goals of this document

- Does not decide whether `frek_v1` and `identity_engine` should ever merge into one collection (§5: still open, deferred to whoever makes that call with this map in hand).
- Does not implement any missing capability (revoke/update/archive/renew/recovery for `identity_engine`, notarization wiring, the resolver itself).
- Does not touch `backend/frek/`'s (work-certification) lifecycle beyond citing it — its fate is `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md`'s to decide.
