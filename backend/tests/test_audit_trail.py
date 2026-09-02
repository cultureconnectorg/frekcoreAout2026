"""Unit tests for the Audit Trail (Phase 2, Priorite 4). Pure Python, no MongoDB."""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from audit_trail import AuditEvent, InMemoryAuditRecorder  # noqa: E402

pytestmark = pytest.mark.unit


def test_record_appends_and_all_events_reflects_order():
    recorder = InMemoryAuditRecorder()
    e1 = recorder.record(
        AuditEvent(action="read", resource_type="frek.artist", result="success")
    )
    e2 = recorder.record(
        AuditEvent(action="issue", resource_type="frek.certificate", result="deny")
    )

    assert recorder.all_events() == (e1, e2)


def test_all_events_returns_immutable_tuple_not_the_backing_list():
    recorder = InMemoryAuditRecorder()
    recorder.record(
        AuditEvent(action="read", resource_type="frek.artist", result="success")
    )

    events = recorder.all_events()
    assert isinstance(events, tuple)
    with pytest.raises(AttributeError):
        events.append(None)  # tuples have no append — proves it's not the live list


def test_recorder_exposes_no_mutation_or_deletion_method():
    """Append-only is enforced by the class shape: no update/delete/clear method exists."""
    public_methods = {
        name for name in dir(InMemoryAuditRecorder) if not name.startswith("_")
    }
    assert public_methods == {"record", "all_events"}


def test_audit_event_defaults():
    event = AuditEvent(action="verify", resource_type="frek.track", result="success")
    assert event.event_id
    assert event.timestamp
    assert event.actor_frek_id is None
    assert event.reason is None


def test_audit_event_result_is_constrained_to_known_values():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AuditEvent(action="read", resource_type="frek.artist", result="maybe")  # type: ignore[arg-type]


# ---------------- Event Bus -> Audit Trail wiring (P2, 2026-08-31) ----------------
# server.py's _AUDIT_TRAIL_EVENT_TYPES now subscribes identity.updated,
# identity.revoked, and object.created in addition to identity.created (they
# were all real producers, per reports/FREKCORE_COMPLETION_BACKLOG.md P1 #8,
# but none was ever wired into the audit trail until this pass). These tests
# prove event_envelope_to_audit_event() + MongoAuditRecorder correctly
# round-trip each of the three new event shapes — the actual server.py
# subscription list itself is not re-imported here (that would mean booting
# the whole app; a static reading of server.py's own source, done once
# while wiring this, is the simpler check for "is this event_type in that
# list", not duplicated as a live test per event type).

import asyncio  # noqa: E402

from audit_trail.mongo_recorder import MongoAuditRecorder  # noqa: E402
from audit_trail.subscribers import (  # noqa: E402
    event_envelope_to_audit_event,
    make_audit_trail_subscriber,
)
from eventbus.producers import (  # noqa: E402
    build_identity_revoked_event,
    build_identity_updated_event,
    build_identity_recovered_event,
    build_identity_reconciled_event,
    build_object_created_event,
    build_content_binding_created_event,
    build_creative_lifecycle_event,
)


class _FakeMongoCollection:
    """Minimal stand-in — just enough for MongoAuditRecorder.record()'s
    insert_one call, no real MongoDB or mongomock needed for this pure
    mapping-correctness check."""

    def __init__(self):
        self.inserted = []

    async def insert_one(self, doc):
        self.inserted.append(doc)


class _FakeMongoDb:
    def __init__(self):
        self.audit_trail_events = _FakeMongoCollection()

    def __getitem__(self, name):
        assert name == "audit_trail_events"
        return self.audit_trail_events


def test_identity_updated_event_maps_to_a_correct_audit_event():
    envelope = build_identity_updated_event(
        frek_id="id-abcdef012345-ab12",
        updated_at="2026-08-31T00:00:00+00:00",
        changed_fields=["display_name"],
    )
    audit_event = event_envelope_to_audit_event(envelope)
    assert audit_event.action == "identity.updated"
    assert audit_event.resource_type == "identity_engine"
    assert audit_event.actor_frek_id == "id-abcdef012345-ab12"
    assert audit_event.metadata["payload"]["changed_fields"] == ["display_name"]


def test_identity_revoked_event_maps_to_a_correct_audit_event():
    envelope = build_identity_revoked_event(
        frek_id="id-abcdef012345-ab12", revoked_at="t", revoked_by="holder"
    )
    audit_event = event_envelope_to_audit_event(envelope)
    assert audit_event.action == "identity.revoked"
    assert audit_event.metadata["payload"]["revoked_by"] == "holder"


def test_identity_recovered_event_maps_to_a_correct_audit_event():
    envelope = build_identity_recovered_event(
        frek_id="id-abcdef012345-ab12",
        recovered_at="t",
        new_credential_label="recovery-device",
    )
    audit_event = event_envelope_to_audit_event(envelope)
    assert audit_event.action == "identity.recovered"
    assert audit_event.actor_frek_id == "id-abcdef012345-ab12"
    assert audit_event.metadata["payload"]["new_credential_label"] == "recovery-device"


def test_identity_reconciled_event_maps_to_a_correct_audit_event():
    envelope = build_identity_reconciled_event(
        canonical_frek_id="id-abcdef012345-ab12",
        reconciled_frek_id="id-987654321fed-cd34",
        reconciled_system="identity_engine",
        reconciled_at="t",
        authorized_by="holder",
    )
    audit_event = event_envelope_to_audit_event(envelope)
    assert audit_event.action == "identity.reconciled"
    assert audit_event.actor_frek_id == "id-abcdef012345-ab12"
    assert (
        audit_event.metadata["payload"]["reconciled_frek_id"] == "id-987654321fed-cd34"
    )


def test_object_created_event_maps_to_a_correct_audit_event():
    envelope = build_object_created_event(
        {"frek_id": "id-fk-1", "object_type": "song", "title": "T", "created_at": "t"}
    )
    audit_event = event_envelope_to_audit_event(envelope)
    assert audit_event.action == "object.created"
    assert audit_event.resource_type == "fk"


def test_content_binding_created_event_maps_to_a_correct_audit_event():
    envelope = build_content_binding_created_event(
        {
            "binding_id": "CB-1",
            "frek_id": "id-fk-1",
            "exact_hash": "a" * 64,
            "signal_fingerprint": {
                "algorithm": "frek_signal_v1",
                "algorithm_version": "1.0.0",
            },
            "produced_by": "admin",
            "proof_state": "fingerprint",
        }
    )
    audit_event = event_envelope_to_audit_event(envelope)
    assert audit_event.action == "content_binding.created"
    assert audit_event.resource_type == "content_binding"


def test_creative_lifecycle_recorded_event_maps_to_a_correct_audit_event():
    envelope = build_creative_lifecycle_event(
        {
            "event_id": "evt-1",
            "pre_id": "PRE-1",
            "stage": "GENESIS",
            "sequence": 1,
            "actor_id": "ARTIST-1",
            "authority": "holder",
            "fk_frek_id": None,
            "proof_state": "fingerprint",
        }
    )
    audit_event = event_envelope_to_audit_event(envelope)
    assert audit_event.action == "creative_lifecycle.recorded"
    assert audit_event.resource_type == "creative_lifecycle"
    assert audit_event.actor_frek_id == "PRE-1"


def test_subscriber_actually_writes_each_new_event_type_to_the_recorder():
    """End-to-end through the real subscriber function (not just the pure
    mapping) — proves make_audit_trail_subscriber's async-write path works
    for every non-identity.created event shape, matching how server.py
    actually wires them (same subscriber instance for every event_type,
    per _AUDIT_TRAIL_EVENT_TYPES's own design)."""
    fake_db = _FakeMongoDb()
    recorder = MongoAuditRecorder(fake_db)
    subscriber = make_audit_trail_subscriber(recorder)

    events = [
        build_identity_updated_event(
            frek_id="id-x", updated_at="t", changed_fields=["display_name"]
        ),
        build_identity_revoked_event(
            frek_id="id-x", revoked_at="t", revoked_by="admin"
        ),
        build_object_created_event(
            {
                "frek_id": "id-fk-1",
                "object_type": "other",
                "title": "T",
                "created_at": "t",
            }
        ),
        build_identity_recovered_event(frek_id="id-x", recovered_at="t"),
        build_identity_reconciled_event(
            canonical_frek_id="id-x",
            reconciled_frek_id="id-y",
            reconciled_system="identity_engine",
            reconciled_at="t",
            authorized_by="admin",
        ),
        build_content_binding_created_event(
            {
                "binding_id": "CB-1",
                "frek_id": "id-fk-1",
                "exact_hash": "a" * 64,
                "signal_fingerprint": {
                    "algorithm": "frek_signal_v1",
                    "algorithm_version": "1.0.0",
                },
                "produced_by": "admin",
                "proof_state": "fingerprint",
            }
        ),
        build_creative_lifecycle_event(
            {
                "event_id": "evt-1",
                "pre_id": "PRE-1",
                "stage": "GENESIS",
                "sequence": 1,
                "actor_id": "ARTIST-1",
                "authority": "holder",
                "fk_frek_id": None,
                "proof_state": "fingerprint",
            }
        ),
    ]

    async def _run():
        for envelope in events:
            subscriber(envelope)
        # subscriber schedules the write via create_task — yield control so
        # those tasks actually run before asserting.
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    asyncio.run(_run())

    recorded_actions = {doc["action"] for doc in fake_db.audit_trail_events.inserted}
    assert recorded_actions == {
        "identity.updated",
        "identity.revoked",
        "object.created",
        "identity.recovered",
        "identity.reconciled",
        "content_binding.created",
        "creative_lifecycle.recorded",
    }


def test_server_py_subscribes_all_eight_real_producers_to_audit_trail():
    """Static check on server.py's own source — the actual regression this
    guards against is a future new producer (or this list) drifting without
    the other being updated, without needing to boot the full app to catch
    it."""
    server_py = (BACKEND_DIR / "server.py").read_text(encoding="utf-8")
    assert "_AUDIT_TRAIL_EVENT_TYPES" in server_py
    for event_type in (
        "identity.created",
        "identity.updated",
        "identity.revoked",
        "object.created",
        "identity.recovered",
        "identity.reconciled",
        "content_binding.created",
        "creative_lifecycle.recorded",
    ):
        assert f'"{event_type}"' in server_py, f"{event_type} not found in server.py"
