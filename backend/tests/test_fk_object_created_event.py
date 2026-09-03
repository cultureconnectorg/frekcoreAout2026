"""object.created event wiring — TestClient, in-process.

Same pattern as tests/test_registry.py: an isolated FastAPI app mounting
just fk_router, mongomock_motor substituting real MongoDB — no live
external server needed. Proves the actual wiring (fk/routes.py really
calls eventbus.publish() during POST /fk/create), which
tests/test_eventbus.py's unit tests for build_object_created_event() alone
cannot: those only prove the producer function's *output* is correct, not
that anything in fk/routes.py ever calls it.

The shared eventbus.bus.default_bus singleton has no unsubscribe (by
design, see its own docstring: "Tests should construct their own
InProcessEventBus() to stay isolated") — so this file monkeypatches
fk.routes's own `_event_bus` module attribute to a fresh, test-local bus
instead of touching the process-wide default.
"""

import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault(
    "FREK_PASSPORT_KEY_PATH", "/tmp/frekcore_test_fk_event_passport_key.pem"
)

import mongomock_motor  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import fk.routes as fk_routes  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture()
def client():
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_test_fk_event"]
    fk_routes.set_db(db)
    app = FastAPI()
    app.include_router(fk_routes.fk_router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture()
def test_bus(monkeypatch):
    bus = InProcessEventBus()
    monkeypatch.setattr(fk_routes, "_event_bus", bus)
    return bus


def test_creating_an_fk_publishes_object_created(client, test_bus):
    received = []
    test_bus.subscribe("object.created", received.append)

    resp = client.post(
        "/api/v1/fk/create",
        data={
            "title": "Test Song",
            "object_type": "song",
            "primary_creator_name": "Test Artist",
            "return_json": "true",
        },
    )
    assert resp.status_code == 200, resp.text
    real_frek_id = resp.json()["info"]["frek_id"]

    assert len(received) == 1
    env = received[0]
    assert env.event_type == "object.created"
    assert env.producer == "fk"
    assert env.subject == real_frek_id
    assert env.payload["frek_id"] == real_frek_id
    assert env.payload["title"] == "Test Song"
    assert env.payload["object_type"] == "song"
    assert env.payload["creator_name"] == "Test Artist"
    assert "storage_path" not in env.payload


def test_a_broken_bus_does_not_break_fk_creation(client, monkeypatch):
    """The try/except guard in fk/routes.py must actually be reachable:
    a publish() that raises must not turn into a 500 on POST /fk/create."""

    class ExplodingBus:
        def publish(self, _envelope):
            raise RuntimeError("bus down")

    monkeypatch.setattr(fk_routes, "_event_bus", ExplodingBus())

    resp = client.post(
        "/api/v1/fk/create",
        data={
            "title": "Resilience Check",
            "object_type": "other",
            "primary_creator_name": "Test Artist",
        },
    )
    assert resp.status_code == 200, resp.text
