"""Unit tests for the Event Bus -> Audit Trail bridge (Phase 3, Priority 5).

Pure Python + a fake in-memory recorder (not MongoDB) for the pure mapping
function; an asyncio event loop for the subscriber scheduling behavior.
No MongoDB, no live server.
"""

import asyncio
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from audit_trail.subscribers import (  # noqa: E402
    event_envelope_to_audit_event,
    make_audit_trail_subscriber,
)
from eventbus.envelope import EventEnvelope  # noqa: E402

pytestmark = pytest.mark.unit


def test_event_envelope_to_audit_event_maps_fields():
    envelope = EventEnvelope(
        event_type="identity.created",
        producer="identity_engine",
        subject="id-abc123",
        correlation_id="corr-1",
        payload={"frek_id": "id-abc123", "identity_type": "individual"},
    )
    audit_event = event_envelope_to_audit_event(envelope)

    assert audit_event.actor_frek_id == "id-abc123"
    assert audit_event.action == "identity.created"
    assert audit_event.resource_type == "identity_engine"
    assert audit_event.resource_id == "id-abc123"
    assert audit_event.result == "success"
    assert audit_event.correlation_id == "corr-1"
    assert audit_event.metadata["event_id"] == envelope.event_id
    assert audit_event.metadata["payload"]["frek_id"] == "id-abc123"


class _FakeRecorder:
    def __init__(self):
        self.recorded = []

    async def record(self, event):
        self.recorded.append(event)
        return event


def test_subscriber_schedules_a_write_inside_a_running_loop():
    async def scenario():
        recorder = _FakeRecorder()
        subscriber = make_audit_trail_subscriber(recorder)
        envelope = EventEnvelope(
            event_type="identity.created", producer="identity_engine", payload={}
        )

        subscriber(envelope)
        # The write is scheduled via create_task — yield control so it runs.
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert len(recorder.recorded) == 1
        assert recorder.recorded[0].action == "identity.created"

    asyncio.run(scenario())


def test_subscriber_never_raises_when_recorder_fails():
    class _ExplodingRecorder:
        async def record(self, event):
            raise RuntimeError("mongo down")

    async def scenario():
        subscriber = make_audit_trail_subscriber(_ExplodingRecorder())
        envelope = EventEnvelope(
            event_type="identity.created", producer="identity_engine", payload={}
        )

        # Must not raise synchronously — the write failure happens inside
        # the scheduled task, caught there (see subscribers.py:_write).
        subscriber(envelope)
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    asyncio.run(scenario())  # no exception propagates out


def test_subscriber_without_running_loop_does_not_raise():
    recorder = _FakeRecorder()
    subscriber = make_audit_trail_subscriber(recorder)
    envelope = EventEnvelope(
        event_type="identity.created", producer="identity_engine", payload={}
    )

    # No asyncio.run() wrapping this call — no running loop.
    subscriber(envelope)  # must not raise
    assert recorder.recorded == []
