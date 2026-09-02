"""Pure event-construction helpers, kept separate from route handlers.

Splitting "build the envelope" (pure, unit-testable, no I/O) from "publish
it" (a side effect) lets Phase 2's one real producer (identity.created, see
backend/identity_engine/routes.py) be verified by a unit test without a
live server or MongoDB — see backend/tests/test_eventbus.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .envelope import EventEnvelope


def build_identity_created_event(
    identity: Dict[str, Any], correlation_id: Optional[str] = None
) -> EventEnvelope:
    """Build the `identity.created` event for a freshly created FREKIdentity.

    `identity` is the same dict inserted into `db.frek_persons` by
    backend/identity_engine/routes.py:init_identity — this function does not
    touch the database itself, so it can be unit-tested with a plain dict.
    """
    return EventEnvelope(
        event_type="identity.created",
        producer="identity_engine",
        subject=identity["frek_id"],
        correlation_id=correlation_id,
        payload={
            "frek_id": identity["frek_id"],
            "identity_type": identity.get("identity_type"),
            "status": identity.get("status"),
            "created_at": identity.get("created_at"),
        },
        schema_version="1.0.0",
    )


def build_identity_revoked_event(
    frek_id: str,
    revoked_at: str,
    revoked_by: str,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> EventEnvelope:
    """Build the `identity.revoked` event (P1 backlog item, closes the
    `implemented: false` entry in backend/registry/events/event_registry.json
    — see docs/architecture/FREK_ID_RECONCILIATION.md for why this was built
    holder-initiated-by-default rather than copied from frek_v1's
    client-initiated revoke).

    `revoked_by` is `"holder"` (the FREK-ID's own session revoked itself) or
    `"admin"` (the X-Admin-Key override path) — never a client_id, since
    identity_engine has no OAuth2-client concept the way frek_v1 does.
    """
    return EventEnvelope(
        event_type="identity.revoked",
        producer="identity_engine",
        subject=frek_id,
        correlation_id=correlation_id,
        payload={
            "frek_id": frek_id,
            "revoked_at": revoked_at,
            "revoked_by": revoked_by,
            "reason": reason,
        },
        schema_version="1.0.0",
    )


def build_object_created_event(
    fk_doc: Dict[str, Any], correlation_id: Optional[str] = None
) -> EventEnvelope:
    """Build the `object.created` event for a freshly created `.fk` Cultural
    Object Container (P1 backlog: closes the `implemented: false` entry in
    backend/registry/events/event_registry.json, which already assigns this
    event `producer: "fk"` — this is that producer, not a new one).

    `fk_doc` is the same dict `backend/fk/routes.py:create_fk_endpoint`
    inserts into `db.fk_objects` — this function does not touch the
    database itself, matching `build_identity_created_event`'s pattern
    (unit-testable with a plain dict, no live server/Mongo needed). The
    payload echoes exactly the fields `GET /api/v1/fk/detail/{frek_id}`
    already returns publicly (everything but `storage_path`, which that
    route itself excludes) — publishing this event exposes nothing that
    wasn't already public via the existing detail route.
    """
    return EventEnvelope(
        event_type="object.created",
        producer="fk",
        subject=fk_doc["frek_id"],
        correlation_id=correlation_id,
        payload={
            "frek_id": fk_doc["frek_id"],
            "object_type": fk_doc.get("object_type"),
            "title": fk_doc.get("title"),
            "creator_name": fk_doc.get("creator_name"),
            "created_at": fk_doc.get("created_at"),
            "block_hash": fk_doc.get("block_hash"),
            "root_hash": fk_doc.get("root_hash"),
            "media_count": fk_doc.get("media_count"),
        },
        schema_version="1.0.0",
    )


def build_identity_updated_event(
    frek_id: str,
    updated_at: str,
    changed_fields: list,
    correlation_id: Optional[str] = None,
) -> EventEnvelope:
    """Build the `identity.updated` event. `changed_fields` names which
    top-level identity fields changed (e.g. `["display_name"]`) — never the
    values themselves, so this event can never leak PII a subscriber (like
    the Audit Trail) shouldn't see just by existing."""
    return EventEnvelope(
        event_type="identity.updated",
        producer="identity_engine",
        subject=frek_id,
        correlation_id=correlation_id,
        payload={
            "frek_id": frek_id,
            "updated_at": updated_at,
            "changed_fields": changed_fields,
        },
        schema_version="1.0.0",
    )


def build_identity_recovered_event(
    frek_id: str,
    recovered_at: str,
    new_credential_label: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> EventEnvelope:
    """Build the `identity.recovered` event (RECOVERY, `docs/decisions/
    0003-identity-lifecycle-founder-decisions-implemented.md` §3) — a
    holder who could not produce a valid session (every registered Passkey
    lost) regained control of their EXISTING frek_id via the admin-key
    override on register_begin/register_complete. Deliberately a distinct
    event type from `identity.updated`: this is a sensitive, security-
    relevant action ("Sensitive recovery requires strengthened
    authorization and complete auditability" per the ADR) and deserves its
    own unambiguous audit signal rather than being folded into the generic
    field-changed event. `frek_id` is never regenerated by this path — the
    payload deliberately has no "new_frek_id" field, because there isn't
    one."""
    return EventEnvelope(
        event_type="identity.recovered",
        producer="identity_engine",
        subject=frek_id,
        correlation_id=correlation_id,
        payload={
            "frek_id": frek_id,
            "recovered_at": recovered_at,
            "new_credential_label": new_credential_label,
        },
        schema_version="1.0.0",
    )


def build_identity_reconciled_event(
    canonical_frek_id: str,
    reconciled_frek_id: str,
    reconciled_system: str,
    reconciled_at: str,
    authorized_by: str,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> EventEnvelope:
    """Build the `identity.reconciled` event (MERGE, `docs/decisions/
    0003-...md` §1). Deliberately named `reconciled`, not `merged` — the
    approved semantics are strictly non-destructive (see the ADR): neither
    `canonical_frek_id` nor `reconciled_frek_id` is deleted, overwritten,
    or stops resolving; this event records that a new relationship record
    was appended to `frek_reconciliations`, nothing more. `subject` is the
    initiating (source) frek_id — `reconciled_frek_id` and
    `reconciled_system` carry the other side, so a subscriber can tell
    same-system from cross-system (`frek_v1`) reconciliation without a
    second lookup."""
    return EventEnvelope(
        event_type="identity.reconciled",
        producer="identity_engine",
        subject=canonical_frek_id,
        correlation_id=correlation_id,
        payload={
            "canonical_frek_id": canonical_frek_id,
            "reconciled_frek_id": reconciled_frek_id,
            "reconciled_system": reconciled_system,
            "reconciled_at": reconciled_at,
            "authorized_by": authorized_by,
            "reason": reason,
        },
        schema_version="1.0.0",
    )


def build_content_binding_created_event(
    binding_doc: Dict[str, Any], correlation_id: Optional[str] = None
) -> EventEnvelope:
    """Build the `content_binding.created` event (founder decision D1,
    docs/decisions/0004-... -- see
    reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md section D).

    `binding_doc` is the same dict `backend/content_binding/routes.py:
    create_content_binding` inserts into `db.content_bindings` -- this
    function does not touch the database itself, matching every other
    producer in this file (unit-testable with a plain dict). The payload
    deliberately omits the full 528-float `signal_fingerprint.vector` --
    it echoes the algorithm/version/dimensions metadata plus both hash
    values, which is what a subscriber needs to know a binding exists and
    what produced it, not the raw vector itself (available via
    `GET /api/v1/content-binding/binding/{binding_id}` for anyone who
    needs it)."""
    fingerprint = binding_doc.get("signal_fingerprint") or {}
    return EventEnvelope(
        event_type="content_binding.created",
        producer="content_binding",
        subject=binding_doc["frek_id"],
        correlation_id=correlation_id,
        payload={
            "binding_id": binding_doc["binding_id"],
            "frek_id": binding_doc["frek_id"],
            "exact_hash": binding_doc.get("exact_hash"),
            "exact_hash_algorithm": binding_doc.get("exact_hash_algorithm"),
            "signal_algorithm": fingerprint.get("algorithm"),
            "signal_algorithm_version": fingerprint.get("algorithm_version"),
            "signal_dimensions": fingerprint.get("dimensions"),
            "produced_by": binding_doc.get("produced_by"),
            "proof_state": binding_doc.get("proof_state"),
            "computed_at": binding_doc.get("computed_at"),
        },
        schema_version="1.0.0",
    )


def build_creative_lifecycle_event(
    event_doc: Dict[str, Any], correlation_id: Optional[str] = None
) -> EventEnvelope:
    """Build the `creative_lifecycle.recorded` event (founder decision D2,
    2026-09-02 -- see reports/FREKCORE_HISTORICAL_CAPABILITY_
    RECONCILIATION.md section D "D2 -- Creative Lifecycle").

    `event_doc` is the same dict `backend/creative_lifecycle/routes.py`'s
    `_notarize_and_store` inserts into `db.creative_lifecycle_events` --
    this function does not touch the database itself, matching every
    other producer in this file. One unified event type covers all five
    stages (GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY, carried in
    `payload["stage"]`) rather than five near-identical producer
    functions -- the stage is itself just a value of the same underlying
    "a lifecycle event was recorded" fact, and every consumer (Audit
    Trail included) needs the same shape regardless of which stage.
    `subject` is `pre_id` -- a provisional creative-lifecycle identity,
    NEVER a FREK-ID (see creative_lifecycle/models.py's module
    docstring). The full `claim`/`evidence`/`signal_vector` payloads are
    NOT echoed here (same reasoning as `build_content_binding_created_
    event`'s omission of the raw fingerprint vector) -- a subscriber
    that needs the full record reads it back via
    `GET /api/v1/creative-lifecycle/{pre_id}`.
    """
    return EventEnvelope(
        event_type="creative_lifecycle.recorded",
        producer="creative_lifecycle",
        subject=event_doc["pre_id"],
        correlation_id=correlation_id,
        payload={
            "event_id": event_doc["event_id"],
            "pre_id": event_doc["pre_id"],
            "stage": event_doc.get("stage"),
            "sequence": event_doc.get("sequence"),
            "actor_id": event_doc.get("actor_id"),
            "authority": event_doc.get("authority"),
            "fk_frek_id": event_doc.get("fk_frek_id"),
            "proof_state": event_doc.get("proof_state"),
            "created_at": event_doc.get("created_at"),
        },
        schema_version="1.0.0",
    )
