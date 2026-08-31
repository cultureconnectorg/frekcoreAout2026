# 0003 — Founder Decisions: `identity_engine` merge / renew / recovery (APPROVED)

Status: **DECIDED, IMPLEMENTATION IN PROGRESS**. Supersedes the open
questions in `docs/decisions/0002-identity-lifecycle-founder-decisions-needed.md`
(that document's evidence and options remain valid background; this one
records the founder's actual choice and scopes it against
`docs/architecture/FREK_ID_ENTITY_TAXONOMY.md`).

**Entity scope** (per the taxonomy audit that preceded this ADR, done at
the founder's explicit instruction rather than assumed): these three
decisions apply to **Person / Institution identities in
`backend/identity_engine`'s `frek_persons` collection** — the only FREK-ID
entity type in this codebase that has its own WebAuthn credentials, its
own holder-session authority model, and no built-in expiry. Registry
objects owned *by* an identity (`.fk`, `frek.organization`,
`frek.wallet`, `frek.certificate`) are not credentialed actors — "merge,"
"renew," and "recovery" as decided here do not apply to them and are not
implemented for them by this ADR. `frek_v1`'s own identities are a
separate authority model (OAuth2-client-scoped, no holder session) and
participate here only as the admin-gated cross-system side of MERGE (§1).

---

## 1. MERGE — APPROVED, NON-DESTRUCTIVE

**Founder decision, verbatim:**
- Never delete or overwrite a FREK-ID.
- Reconciliation establishes a canonical identity relationship.
- Preserve every source identifier, provenance, lineage and historical proof.
- Require strong authorization, audit and proof.
- Prevent cross-holder takeover.
- Existing references to reconciled IDs must remain resolvable.

**Implementation shape** (closest to `0002`'s Option B, generalized beyond
same-system-only, and made explicit rather than left as an unformalized
convention): no identity document is ever combined, overwritten, or
retired. `POST /identity/{frek_id}/reconcile` creates one new, append-only
record in a dedicated `frek_reconciliations` collection asserting that
`frek_id` and a `target_frek_id` represent a canonical relationship (the
same underlying person/entity, or an explicitly reconciled cross-system
counterpart). Both original identities keep resolving exactly as they did
before — `GET /{frek_id}` is untouched by this feature, satisfying
"existing references must remain resolvable" literally, not just in
spirit. `GET /identity/{frek_id}/reconciliations` surfaces every
reconciliation record naming that `frek_id` on either side.

**Authorization** (prevents cross-holder takeover): the caller must prove
holder-session authority over the *source* `frek_id` (or supply the
admin key). Reconciling with another `identity_engine` identity
additionally requires a session token proving control of the *target*
identity too — a holder can only reconcile identities they can prove they
control on both sides. Reconciling with a `frek_v1` identity (a different
authority model with no holder-session concept, see
`docs/architecture/FREK_ID_RECONCILIATION.md`) requires the admin-key path,
since there is no way for a holder to self-serve prove control of a
`frek_v1`-issued identifier under the current architecture — an honest,
documented constraint, not a shortcut introduced here.

**Proof**: notarized (`notary.notarize_event`, `payload_type="identity_reconciliation"`),
same pattern as `revoke_identity`. **Audit**: a new `identity.reconciled`
event, subscribed into the Audit Trail alongside the four existing event
types.

## 2. RENEW — FREK-ID ITSELF DOES NOT RENEW

**Founder decision, verbatim:**
- FREK-ID is persistent.
- Credentials, authenticators, keys, devices, attestations and authority grants may expire, rotate or renew.
- Never regenerate an identity because authentication material expires.
- Inspect the historical `frek_v1` renew semantics and preserve them under the correct lifecycle concept if they represent something distinct from identity renewal.

**Finding on `frek_v1`'s existing renew** (`frek_v1/identity.py:256-315`,
inspected for this ADR): it **already conforms exactly**. `POST
/{frek_id}/renew` only ever mutates `expires_at` and `renewed_at`,
notarizes a `"renewal"` block, and never touches, regenerates, or
re-issues `frek_id` itself. This is credential/session-lifetime renewal,
not identity renewal — it was correctly built this way from the start;
this ADR records that finding rather than changing working code. No code
change to `frek_v1` is needed or made by this ADR.

**Finding on `identity_engine`**: `FREKIdentity` has no expiry field at
all (`identity_engine/models.py`) — there is nothing to renew, and this
ADR does not add one (inventing an expiry concept an identity never had
would itself violate "FREK-ID is persistent"). What `identity_engine`
*does* have, already, is credential rotation: adding a new Passkey to an
identity that already holds one requires the holder's own session
(`register_begin`/`register_complete`'s existing ownership check) — this
already is "an authenticator may expire, rotate or renew" in the
approved sense, simply not previously named as such. This ADR's only
`identity_engine` change for RENEW is documentation: the module docstring
and `docs/architecture/FREK_ID_CANONICAL_MODEL.md` are updated to name
this existing mechanism as the credential-rotation lifecycle concept, and
a regression test locks in the invariant that no code path regenerates a
`frek_id`.

## 3. RECOVERY — APPROVED

**Founder decision, verbatim:**
- Recovery restores control of the existing FREK-ID.
- Compromised credentials/authenticators may be revoked or rotated.
- Identity continuity, provenance and proof history must remain intact.
- Sensitive recovery requires strengthened authorization and complete auditability.
- Recovery must never silently mint a replacement FREK-ID.

**The gap this closes** (found while preparing `0002`, confirmed again
here): `register_begin`/`register_complete`'s ownership check
(`identity_engine/routes.py`) had **no admin-key override**, unlike every
other gated route in the module (revoke/update/archive/search/export all
have one via `_holder_or_admin`/`_admin_or_403`). A holder who lost every
registered Passkey had no path back into their own identity — not even
via support.

**Not to be confused with** (found during the entity-taxonomy audit,
`docs/architecture/FREK_ID_ENTITY_TAXONOMY.md` §2.1): `backend/heritage/`
is a real, separate, already-implemented mechanism that transfers control
of a `frek_v1` identity to a **different** person (death, donation,
retirement) — succession, not recovery. It exists only for `frek_v1`
identities, has no `identity_engine` equivalent, and this ADR does not
touch or duplicate it. RECOVERY here is exclusively "the same holder
regains their own access."

**Implementation**: both routes now accept an `X-Admin-Key` header and
use `_holder_or_admin` in place of the session-only check. When the
admin-key path is the one that succeeds on an identity that already has
credentials (the actual recovery case — a holder-session success on that
same branch is ordinary credential rotation, already covered by §2), the
new credential is added exactly as `register_complete` already does
(`$push` to `credentials`, never a delete of the prior ones — the founder
text permits revoking/rotating compromised credentials, but does not
require it, so existing credentials are left in place unless a holder or
admin separately revokes them via the existing identity-level `revoke`
route), `frek_id` is never touched, and a dedicated `identity.recovered`
event is published and notarized — distinct from `identity.updated`, so
this sensitive path has its own, unambiguous audit signal rather than
being folded into a generic "identity changed" event.

## Verification performed

- **RECOVERY**: `backend/tests/test_identity_recovery_unit.py` (7 tests)
  — bootstrap needs no auth, second credential rejected with neither
  session nor admin key, admin-key succeeds without a session, ordinary
  holder rotation does NOT emit `identity.recovered`, admin-key recovery
  DOES emit it and never regenerates `frek_id`, the prior credential is
  never deleted by default, a revoked identity still cannot be
  "recovered."
- **RENEW**: `backend/tests/test_frek_v1_renew_unit.py` (4 tests) —
  `frek_id` never changes, only `expires_at`/`renewed_at` mutate (every
  other field asserted unchanged, document count asserted unchanged), a
  past expiry is rejected, a revoked identity cannot be renewed.
- **MERGE**: `backend/tests/test_identity_reconcile_unit.py` (9 tests) —
  self-reconciliation rejected, unauthorized caller rejected, missing
  target consent rejected (prevents cross-holder takeover), dual-consent
  holder path succeeds and both identities remain independently
  resolvable afterward, admin bypasses dual consent, cross-system
  (`frek_v1`) targets are admin-only, an unknown target 404s, duplicate
  reconciliation is idempotent (and does not re-publish the event), and
  reconciliation records are visible from either `frek_id`.
- New producer-level tests in `backend/tests/test_eventbus.py`
  (`build_identity_recovered_event`, `build_identity_reconciled_event`)
  and mapping/subscriber tests in `backend/tests/test_audit_trail.py`
  (both new event types round-trip through the Audit Trail correctly;
  the static `server.py` source check now covers all 6 event types).
- Full local unit suite: 156 passed / 0 failed. Exact CI coverage
  command reproduced locally and in a fresh venv
  (`pip install -r requirements-ci.txt`): 96.34% overall, 100% on
  `eventbus/producers.py` — above the 90% gate. `backend/registry/events/
  event_registry.json` updated: `identity.merged` marked `REJECTED` (true
  fusion was explicitly rejected by this ADR) with a pointer to the new
  `identity.reconciled` entry; `identity.recovered` and
  `identity.reconciled` both catalogued as `EXISTS`.

## What this ADR does not do

Per the entity-scope note above and `docs/architecture/FREK_ID_ENTITY_TAXONOMY.md`
§3: does not add merge/renew/recovery to `.fk` objects, `frek.organization`,
`frek.wallet`, or `frek.certificate` records — none of them holds
credentials, so none of these three concepts applies to them as decided
here. Does not implement typed device/org/app DIDs (`did:frek:device-*`
etc.) or FAP — out of scope for this ADR, tracked separately (Contradiction
C6, `docs/architecture/FREK_ID_CANONICAL_MODEL.md` §4).
