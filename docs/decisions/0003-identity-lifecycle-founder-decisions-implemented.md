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

Unit tests for all three (`backend/tests/test_identity_lifecycle.py`,
`backend/tests/test_eventbus.py`, `backend/tests/test_audit_trail.py`):
reconciliation authorization (holder+holder, holder+missing-target-consent
rejected, admin cross-system, duplicate-pair idempotency, both original
identities still independently resolvable after reconciling), the
`frek_id`-never-regenerates invariant for renew, and the recovery
admin-override path (including that a non-admin, non-holder caller is
still rejected exactly as before this change). Full evidence and counts
in the commits implementing each piece and in this session's final
report.

## What this ADR does not do

Per the entity-scope note above and `docs/architecture/FREK_ID_ENTITY_TAXONOMY.md`
§3: does not add merge/renew/recovery to `.fk` objects, `frek.organization`,
`frek.wallet`, or `frek.certificate` records — none of them holds
credentials, so none of these three concepts applies to them as decided
here. Does not implement typed device/org/app DIDs (`did:frek:device-*`
etc.) or FAP — out of scope for this ADR, tracked separately (Contradiction
C6, `docs/architecture/FREK_ID_CANONICAL_MODEL.md` §4).
