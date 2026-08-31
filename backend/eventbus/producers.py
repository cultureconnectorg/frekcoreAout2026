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
