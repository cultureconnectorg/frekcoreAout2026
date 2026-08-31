# Audit-Event Separation

Per the founder's instruction: investigate whether operational, domain,
security, immutable-audit-evidence, and proof/notarial events currently
have sufficiently clear boundaries in this codebase, and implement
separation only where it is actually required to preserve integrity,
provenance, authority, or forensic guarantees — not for architectural
aesthetics. This closes `reports/FREKCORE_COMPLETION_BACKLOG.md` P2 #4.

## Inventory: five candidate event categories, five real mechanisms

| Category | Mechanism | What it actually is |
|---|---|---|
| Domain events | `backend/eventbus/` (Phase 2) | The pure "what happened" signal (`identity.created`, `identity.updated`, `identity.revoked`, `identity.recovered`, `identity.reconciled`, `object.created`) — no storage of its own, just an in-process publish/subscribe bus |
| Security-audit evidence | `backend/audit_trail/` (Phase 2/3) | The **authoritative, append-only** write path: subscribes to Event Bus domain events, writes immutable `AuditEvent` records to `audit_trail_events`. Already correctly, narrowly scoped — its own `__init__.py` and this session's own work never described it as anything else |
| Proof/notarial events | `backend/notary/` | The cryptographic write path: `FrekChain.append_block(payload_type, payload_id, payload_data, ...)` hash-chains every block (`height`, `prev_hash`, `payload_hash`), independently anchorable to Bitcoin via OTS. Fully generic — already the extensibility point this session used for `identity_recovery`, `identity_reconciliation`, `renewal`, and (pre-existing) `heritage_transfer`/`heritage_declare` |
| Operational timeline (read) | `backend/audit/` (Phase 1) | **Not a write path at all** — a read-only aggregation over `frek_stages`, `scans`, `transactions`, and `notary_blocks`, presented as one human-readable, French-labeled chronology. Its own docstring already distinguishes itself from notary ("Different de /api/v1/notary/\* qui est cryptographique") |
| Permission decisions | `backend/permissions/audit_integration.py` | `decision_to_audit_event()` — maps a `Decision` from the (not-yet-wired-to-any-route) Permission Engine into the same `AuditEvent` shape `audit_trail` uses, so a future route that adopts the Permission Engine gets audit coverage for free |

## The actual finding

**The guarantees that matter — cryptographic integrity, provenance, and
forensic reliability — were already correctly separated at the write/
storage level**, and remain so:

- Cryptographic integrity lives in `notary_blocks` (hash-chained,
  independently Bitcoin-anchorable) — nothing in this investigation
  touches or weakens that.
- Forensic/compliance audit reliability lives in `audit_trail_events`
  (append-only, `backend/audit_trail/`'s own model) — a completely
  separate collection and write path from `backend/audit/`'s read
  aggregation, unaffected by anything the latter does.
- `backend/audit/` **writes nothing** — it is a query/presentation
  convenience over data that is exactly as trustworthy with or without
  this endpoint existing.

The gap `reports/FREKCORE_COMPLETION_BACKLOG.md` P2 #4 named ("business/
provenance/security-audit events... currently conflated in
`backend/audit/`... the older module wasn't refactored to match") was
real, but narrower than "conflated" implied on first read: it was a
**read-side categorization gap**, not a write-side integrity risk.
`backend/audit/`'s `TimelineEvent` model mixed identity-security events
(`identity_emit`, `revocation`, `renewal`, `transfer`), a cultural work's
lifecycle stages (`stage`, business/domain — not security-sensitive),
physical-access events (`scan`), and financial transactions
(`transaction`) into one undifferentiated stream with no field a
consumer could filter on to ask for just one category.

**A second, concrete gap found while investigating, not hypothetical**:
the same module's notary-block query was scoped to a hardcoded
`payload_type` list (`revocation`, `renewal`, `transfer`, `walkin_emit`)
that predated this session's own `identity_recovery` and
`identity_reconciliation` payload types (added earlier in this pass) —
so a holder's own timeline was silently omitting their own
recovery/reconciliation history. This is exactly the kind of drift the
founder's "implement it with backward compatibility and tests" applies
to.

## What was implemented (additive, backward-compatible)

`backend/audit/routes.py`:

1. **A `category` field** added to `TimelineEvent` (`identity_security` /
   `work_lifecycle` / `operational_access` / `financial`), computed by a
   new `_category(kind)` helper from an explicit `CATEGORIES` mapping —
   populated at every one of the module's 10 event-construction sites.
   Every existing field is unchanged; this is a pure addition to the
   response shape, not a redesign.
2. **The notary-block filter fixed** to include `identity_recovery` and
   `identity_reconciliation`, closing the concrete omission found above.
3. Module docstring updated to state explicitly that `backend/audit_trail/`
   is the authoritative security-audit mechanism and this module is a
   non-authoritative convenience view — closing the "wasn't refactored to
   match" backlog line honestly, in prose, rather than by restructuring a
   read-only endpoint that was never the integrity boundary in the first
   place.

## What was deliberately NOT done

No new abstraction, no new collection, no new event bus, no migration of
`backend/audit/`'s existing data model. The founder's own rule —
"do not create abstractions merely for architectural aesthetics" —
applies directly here: the write-side separation the mission cares about
(integrity, provenance, authority, forensic reliability) was already
correct; building a fifth event-storage mechanism to formally unify five
things that already have five appropriately-scoped, independently-correct
mechanisms would have been exactly that kind of unnecessary abstraction.

## Verification

`backend/tests/test_audit_timeline_categories_unit.py` (5 tests, isolated
FastAPI app + mongomock_motor): every `CATEGORIES` value is one of the
four named categories, an unmapped `kind` defaults safely rather than
raising, the timeline now includes `identity_recovery`/
`identity_reconciliation` (the concrete regression this closes), every
event carries the correct category for its kind, and a consumer can
filter the response to "security events only" client-side using the new
field — proving the field actually serves its stated purpose, not just
that it exists.
