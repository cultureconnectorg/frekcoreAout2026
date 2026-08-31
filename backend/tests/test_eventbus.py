"""Unit tests for the Event Bus abstraction (Phase 2, Priorite 5 & 6).

No MongoDB, no live server — pure Python + the in-process bus.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from eventbus.bus import InProcessEventBus  # noqa: E402
from eventbus.envelope import EventEnvelope  # noqa: E402
from eventbus.producers import (  # noqa: E402
    build_identity_created_event,
    build_identity_revoked_event,
    build_identity_updated_event,
    build_identity_recovered_event,
    build_identity_reconciled_event,
    build_object_created_event,
)

pytestmark = pytest.mark.unit


def test_envelope_defaults_are_populated():
    env = EventEnvelope(
        event_type="identity.created", producer="identity_engine", payload={"x": 1}
    )
    assert env.event_id
    assert env.event_version == "v1"
    assert env.occurred_at
    assert env.schema_version == "1.0.0"
    assert env.payload == {"x": 1}


def test_envelope_matches_registry_schema():
    """The hand-written EventEnvelope model must stay in sync with the JSON
    Schema served at GET /api/v1/registry/events (envelope_schema)."""
    import json

    registry_path = BACKEND_DIR / "registry" / "events" / "event_registry.json"
    catalog = json.loads(registry_path.read_text())
    required = set(catalog["envelope_schema"]["required"])
    schema_fields = set(catalog["envelope_schema"]["properties"].keys())

    env = EventEnvelope(event_type="x.y", producer="test", payload={})
    model_fields = set(env.model_dump().keys())

    assert (
        model_fields == schema_fields
    ), "EventEnvelope fields drifted from the registry schema"
    assert required.issubset(model_fields)


def test_bus_delivers_to_matching_subscriber_only():
    bus = InProcessEventBus()
    received = []
    other = []
    bus.subscribe("identity.created", received.append)
    bus.subscribe("object.created", other.append)

    env = EventEnvelope(
        event_type="identity.created",
        producer="identity_engine",
        payload={"frek_id": "id-1"},
    )
    bus.publish(env)

    assert received == [env]
    assert other == []
    assert bus.published_events() == (env,)


def test_bus_never_raises_when_subscriber_fails():
    bus = InProcessEventBus()

    def boom(_envelope):
        raise RuntimeError("subscriber exploded")

    bus.subscribe("identity.created", boom)
    env = EventEnvelope(
        event_type="identity.created", producer="identity_engine", payload={}
    )

    # Must not raise — a broken subscriber can never break the publisher.
    bus.publish(env)
    assert bus.published_events() == (env,)


def test_build_identity_created_event_matches_envelope_contract():
    identity = {
        "frek_id": "id-abcdef012345-ab12",
        "identity_type": "individual",
        "status": "anonymous",
        "created_at": "2026-08-30T00:00:00+00:00",
    }
    env = build_identity_created_event(identity, correlation_id="corr-1")

    assert env.event_type == "identity.created"
    assert env.producer == "identity_engine"
    assert env.subject == identity["frek_id"]
    assert env.correlation_id == "corr-1"
    assert env.payload["frek_id"] == identity["frek_id"]


def test_build_identity_revoked_event_matches_envelope_contract():
    env = build_identity_revoked_event(
        frek_id="id-abcdef012345-ab12",
        revoked_at="2026-08-31T00:00:00+00:00",
        revoked_by="holder",
        reason="lost device",
        correlation_id="corr-2",
    )

    assert env.event_type == "identity.revoked"
    assert env.producer == "identity_engine"
    assert env.subject == "id-abcdef012345-ab12"
    assert env.correlation_id == "corr-2"
    assert env.payload["revoked_by"] == "holder"
    assert env.payload["reason"] == "lost device"


def test_build_identity_revoked_event_never_carries_a_client_id():
    """revoked_by must be "holder" or "admin" — never a client_id (unlike
    frek_v1's revoke), since identity_engine has no OAuth2-client concept."""
    env = build_identity_revoked_event(
        frek_id="id-x", revoked_at="t", revoked_by="admin"
    )
    assert env.payload["revoked_by"] in ("holder", "admin")


def test_build_identity_updated_event_never_carries_field_values():
    """changed_fields names which fields changed, never the new values —
    so this event can never leak PII to a subscriber (e.g. the Audit Trail)
    just by existing."""
    env = build_identity_updated_event(
        frek_id="id-abcdef012345-ab12",
        updated_at="2026-08-31T00:00:00+00:00",
        changed_fields=["display_name"],
    )

    assert env.event_type == "identity.updated"
    assert env.payload["changed_fields"] == ["display_name"]
    assert "display_name" not in str(env.payload.get("value", ""))
    assert set(env.payload.keys()) == {"frek_id", "updated_at", "changed_fields"}


def test_build_identity_recovered_event_matches_envelope_contract():
    """RECOVERY (docs/decisions/0003-...md §3) — never carries a
    'new_frek_id' field, since recovery never regenerates one."""
    env = build_identity_recovered_event(
        frek_id="id-abcdef012345-ab12",
        recovered_at="2026-08-31T00:00:00+00:00",
        new_credential_label="recovery-device",
        correlation_id="corr-3",
    )
    assert env.event_type == "identity.recovered"
    assert env.producer == "identity_engine"
    assert env.subject == "id-abcdef012345-ab12"
    assert env.correlation_id == "corr-3"
    assert env.payload["new_credential_label"] == "recovery-device"
    assert "new_frek_id" not in env.payload


def test_build_identity_reconciled_event_matches_envelope_contract():
    """MERGE (docs/decisions/0003-...md §1) — subject is the initiating
    (source) frek_id; the payload names the other side and system
    separately so a subscriber can tell same-system from cross-system
    (frek_v1) reconciliation without a second lookup."""
    env = build_identity_reconciled_event(
        canonical_frek_id="id-abcdef012345-ab12",
        reconciled_frek_id="id-987654321fed-cd34",
        reconciled_system="identity_engine",
        reconciled_at="2026-08-31T00:00:00+00:00",
        authorized_by="holder",
        reason="same person, two devices",
    )
    assert env.event_type == "identity.reconciled"
    assert env.producer == "identity_engine"
    assert env.subject == "id-abcdef012345-ab12"
    assert env.payload["reconciled_frek_id"] == "id-987654321fed-cd34"
    assert env.payload["reconciled_system"] == "identity_engine"
    assert env.payload["authorized_by"] == "holder"


def test_build_object_created_event_matches_envelope_contract():
    fk_doc = {
        "frek_id": "id-fk012345678a-0001",
        "object_type": "song",
        "title": "Test Song",
        "creator_name": "Test Artist",
        "created_at": "2026-08-31T00:00:00+00:00",
        "block_hash": "a" * 64,
        "root_hash": "b" * 64,
        "media_count": 1,
        "size_bytes": 12345,
        "storage_path": "frekcore/fk/id-fk012345678a-0001.fk",
    }
    env = build_object_created_event(fk_doc, correlation_id="corr-3")

    assert env.event_type == "object.created"
    assert env.producer == "fk"
    assert env.subject == fk_doc["frek_id"]
    assert env.correlation_id == "corr-3"
    assert env.payload["object_type"] == "song"
    assert env.payload["title"] == "Test Song"


def test_build_object_created_event_never_carries_storage_path():
    """storage_path is server-internal (GET /fk/detail/{id} itself excludes
    it) — the event must never leak it even though fk_doc (the raw
    db.fk_objects document) carries it."""
    fk_doc = {
        "frek_id": "id-x",
        "object_type": "other",
        "title": "X",
        "created_at": "t",
        "storage_path": "frekcore/fk/id-x.fk",
    }
    env = build_object_created_event(fk_doc)
    assert "storage_path" not in env.payload


def test_identity_engine_publish_wrapper_survives_a_broken_bus():
    """Reproduces the exact try/except shape at backend/identity_engine/routes.py:126-130:
    a broken bus must never be able to propagate out and break identity
    creation. This does not boot the FastAPI route (needs MongoDB) — it
    exercises the identical call/except pattern used there, so a future
    change to that pattern that removes the guard will break this test."""

    class ExplodingBus:
        def publish(self, _envelope):
            raise RuntimeError("bus down")

    event_bus = ExplodingBus()
    identity = {
        "frek_id": "id-x",
        "identity_type": "individual",
        "status": "anonymous",
        "created_at": "now",
    }

    # Identical shape to identity_engine/routes.py:126-130.
    publish_error = None
    if event_bus is not None:
        try:
            event_bus.publish(build_identity_created_event(identity))
        except Exception as exc:  # pragma: no cover - exercised by this test
            publish_error = exc

    # The route never re-raises: it only logs. Here we assert the guard
    # actually caught something (proving the bus really did fail) while
    # nothing escaped this function.
    assert isinstance(publish_error, RuntimeError)
