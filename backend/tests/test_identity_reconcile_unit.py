"""MERGE (docs/decisions/0003-identity-lifecycle-founder-decisions-
implemented.md §1) — unit tests for POST /{frek_id}/reconcile and
GET /{frek_id}/reconciliations.

Isolated FastAPI app + TestClient + mongomock_motor (same technique as
test_identity_recovery_unit.py). Proves: non-destructive (both identities
still resolve after reconciling), dual-consent authorization (prevents
cross-holder takeover), admin-only for cross-system (frek_v1) targets,
idempotency, and the frek_reconciliations record's own shape.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-reconcile-test")

import mongomock_motor  # noqa: E402

import identity_engine.routes as identity_routes  # noqa: E402
import identity_engine.service as identity_service  # noqa: E402
from identity_engine.routes import identity_router  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_reconcile_test"]
    identity_routes.set_db(db)
    test_bus = InProcessEventBus()
    monkeypatch.setattr(identity_routes, "_event_bus", test_bus)

    app = FastAPI()
    app.include_router(identity_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db, test_bus


def _seed_identity(db, frek_id, display_name="Someone"):
    async def _seed():
        await db.frek_persons.insert_one(
            {
                "frek_id": frek_id,
                "identity_type": "individual",
                "display_name": display_name,
                "status": "protected",
                "credentials": [],
                "linked_objects": [],
                "linked_sessions": [],
                "created_at": "2026-08-31T00:00:00+00:00",
            }
        )

    asyncio.run(_seed())


def _session(frek_id):
    return identity_service.issue_session_token(frek_id)


def test_cannot_reconcile_identity_with_itself(app_and_db):
    client, db, _bus = app_and_db
    _seed_identity(db, "id-a")
    resp = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-a"},
        headers={"X-FREK-Session": _session("id-a")},
    )
    assert resp.status_code == 400


def test_holder_without_source_session_or_admin_key_is_rejected(app_and_db):
    client, db, _bus = app_and_db
    _seed_identity(db, "id-a")
    _seed_identity(db, "id-b")
    resp = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-b", "target_session_token": _session("id-b")},
    )
    assert resp.status_code == 403


def test_holder_without_target_consent_is_rejected_prevents_cross_holder_takeover(
    app_and_db,
):
    client, db, _bus = app_and_db
    _seed_identity(db, "id-a")
    _seed_identity(db, "id-b")
    resp = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-b"},  # no target_session_token
        headers={"X-FREK-Session": _session("id-a")},
    )
    assert resp.status_code == 403


def test_holder_with_dual_consent_succeeds_and_is_non_destructive(app_and_db):
    client, db, bus = app_and_db
    events = []
    bus.subscribe("identity.reconciled", lambda e: events.append(e))

    _seed_identity(db, "id-a")
    _seed_identity(db, "id-b")

    resp = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={
            "target_frek_id": "id-b",
            "target_session_token": _session("id-b"),
            "reason": "same person, two devices",
        },
        headers={"X-FREK-Session": _session("id-a")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["canonical_frek_id"] == "id-a"
    assert body["reconciled_frek_id"] == "id-b"
    assert body["authorized_by"] == "holder"

    # Non-destructive: both identities still resolve exactly as before.
    a = client.get("/api/v1/identity/id-a")
    b = client.get("/api/v1/identity/id-b")
    assert a.status_code == 200
    assert b.status_code == 200
    assert a.json()["frek_id"] == "id-a"
    assert b.json()["frek_id"] == "id-b"

    assert len(events) == 1
    assert events[0].event_type == "identity.reconciled"


def test_admin_can_reconcile_without_dual_consent(app_and_db):
    client, db, _bus = app_and_db
    _seed_identity(db, "id-a")
    _seed_identity(db, "id-b")
    resp = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-b"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["authorized_by"] == "admin"


def test_cross_system_reconciliation_requires_admin(app_and_db):
    client, db, _bus = app_and_db
    _seed_identity(db, "id-a")

    holder_attempt = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "frekv1-uuid-1", "target_system": "frek_v1"},
        headers={"X-FREK-Session": _session("id-a")},
    )
    assert holder_attempt.status_code == 403

    admin_attempt = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "frekv1-uuid-1", "target_system": "frek_v1"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert admin_attempt.status_code == 200, admin_attempt.text
    assert admin_attempt.json()["reconciled_system"] == "frek_v1"


def test_reconciling_unknown_identity_engine_target_404s(app_and_db):
    client, db, _bus = app_and_db
    _seed_identity(db, "id-a")
    resp = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-does-not-exist"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert resp.status_code == 404


def test_duplicate_reconciliation_is_idempotent(app_and_db):
    client, db, bus = app_and_db
    events = []
    bus.subscribe("identity.reconciled", lambda e: events.append(e))

    _seed_identity(db, "id-a")
    _seed_identity(db, "id-b")

    first = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-b"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    second = client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-b"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert "idempotent" in second.json()["message"]
    # Only the first call actually published an event.
    assert len(events) == 1


def test_reconciliations_are_visible_from_either_side(app_and_db):
    client, db, _bus = app_and_db
    _seed_identity(db, "id-a")
    _seed_identity(db, "id-b")

    client.post(
        "/api/v1/identity/id-a/reconcile",
        json={"target_frek_id": "id-b"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )

    from_a = client.get("/api/v1/identity/id-a/reconciliations")
    from_b = client.get("/api/v1/identity/id-b/reconciliations")
    assert from_a.status_code == 200
    assert from_b.status_code == 200
    assert from_a.json()["count"] == 1
    assert from_b.json()["count"] == 1
    assert from_a.json()["reconciliations"][0]["reconciled_frek_id"] == "id-b"
    assert from_b.json()["reconciliations"][0]["canonical_frek_id"] == "id-a"
