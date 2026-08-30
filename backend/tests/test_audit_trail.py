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
