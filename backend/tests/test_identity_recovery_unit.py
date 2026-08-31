"""RECOVERY (docs/decisions/0003-identity-lifecycle-founder-decisions-
implemented.md §3) — unit tests for the admin-key override on
register_begin/register_complete.

Isolated FastAPI app + TestClient + mongomock_motor, no live server needed
(same technique as backend/tests/test_registry_objects_unit.py). WebAuthn's
own cryptographic verification is monkeypatched out — `service.
verify_registration` is replaced with a fixed stub — because what this
file tests is the AUTHORIZATION logic around it (holder session vs.
admin-key vs. neither), not the WebAuthn protocol itself, which
test_identity_lifecycle.py already documents as needing a real virtual
authenticator this sandbox doesn't have.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-recovery-test")

import mongomock_motor  # noqa: E402

import identity_engine.routes as identity_routes  # noqa: E402
import identity_engine.service as identity_service  # noqa: E402
from identity_engine.routes import identity_router  # noqa: E402
from eventbus.bus import InProcessEventBus  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]
FAKE_CRED_INFO = {
    "credential_id": "fake-credential-id",
    "public_key": "fake-public-key",
    "sign_count": 0,
    "aaguid": None,
    "transports": ["internal"],
}


@pytest.fixture()
def app_and_db(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_recovery_test"]
    identity_routes.set_db(db)

    # Swap the real eventbus for a fresh in-process one so tests can assert
    # on exactly what this test run published, isolated from any other
    # test module's subscriptions.
    test_bus = InProcessEventBus()
    monkeypatch.setattr(identity_routes, "_event_bus", test_bus)

    # WebAuthn verification itself is out of scope here (see module
    # docstring) — always "succeeds" with a fixed credential.
    monkeypatch.setattr(
        identity_service,
        "verify_registration",
        lambda cred, challenge: dict(FAKE_CRED_INFO),
    )

    app = FastAPI()
    app.include_router(identity_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db, test_bus


def _init_identity(client):
    resp = client.post("/api/v1/identity/init", json={"identity_type": "individual"})
    assert resp.status_code == 200, resp.text
    return resp.json()["frek_id"]


def _register_first_credential(client, frek_id):
    """Bootstraps one real credential onto a fresh identity — no session or
    admin key needed for the FIRST credential, matching the existing,
    unchanged bootstrap behavior."""
    begin = client.post(
        f"/api/v1/identity/{frek_id}/register/begin", json={"label": "first"}
    )
    assert begin.status_code == 200, begin.text
    complete = client.post(
        f"/api/v1/identity/{frek_id}/register/complete",
        json={"credential": {"response": {}}, "label": "first"},
    )
    assert complete.status_code == 200, complete.text
    return complete.json()["session_token"]


def test_bootstrap_first_credential_needs_no_auth(app_and_db):
    client, _db, bus = app_and_db
    events = []
    bus.subscribe("identity.recovered", lambda e: events.append(e))
    frek_id = _init_identity(client)
    _register_first_credential(client, frek_id)
    # Not a recovery — this identity had zero credentials before.
    assert events == []


def test_second_credential_without_session_or_admin_key_is_rejected(app_and_db):
    client, _db, _bus = app_and_db
    frek_id = _init_identity(client)
    _register_first_credential(client, frek_id)

    begin = client.post(
        f"/api/v1/identity/{frek_id}/register/begin", json={"label": "second"}
    )
    assert begin.status_code == 403, begin.text


def test_second_credential_with_admin_key_but_no_session_succeeds_at_begin(app_and_db):
    client, _db, _bus = app_and_db
    frek_id = _init_identity(client)
    _register_first_credential(client, frek_id)

    begin = client.post(
        f"/api/v1/identity/{frek_id}/register/begin",
        json={"label": "recovery"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert begin.status_code == 200, begin.text


def test_ordinary_holder_initiated_rotation_does_not_emit_recovered(app_and_db):
    client, _db, bus = app_and_db
    events = []
    bus.subscribe("identity.recovered", lambda e: events.append(e))

    frek_id = _init_identity(client)
    session_token = _register_first_credential(client, frek_id)

    begin = client.post(
        f"/api/v1/identity/{frek_id}/register/begin",
        json={"label": "second-device"},
        headers={"X-FREK-Session": session_token},
    )
    assert begin.status_code == 200, begin.text
    complete = client.post(
        f"/api/v1/identity/{frek_id}/register/complete",
        json={"credential": {"response": {}}, "label": "second-device"},
        headers={"X-FREK-Session": session_token},
    )
    assert complete.status_code == 200, complete.text
    # A holder rotating their own credential is not a recovery event.
    assert events == []


def test_admin_key_recovery_emits_identity_recovered_and_preserves_frek_id(app_and_db):
    client, db, bus = app_and_db
    events = []
    bus.subscribe("identity.recovered", lambda e: events.append(e))

    frek_id = _init_identity(client)
    _register_first_credential(client, frek_id)  # holder then loses this device

    begin = client.post(
        f"/api/v1/identity/{frek_id}/register/begin",
        json={"label": "recovery-device"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert begin.status_code == 200, begin.text
    complete = client.post(
        f"/api/v1/identity/{frek_id}/register/complete",
        json={"credential": {"response": {}}, "label": "recovery-device"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["identity"]["frek_id"] == frek_id  # never regenerated

    assert len(events) == 1
    assert events[0].event_type == "identity.recovered"
    assert events[0].payload["frek_id"] == frek_id
    assert events[0].payload["new_credential_label"] == "recovery-device"


def test_recovery_never_deletes_the_prior_credential(app_and_db):
    """The founder text permits, but does not require, revoking a
    compromised credential during recovery — this asserts the actual
    default behavior: the lost device's credential is left in place, not
    silently dropped."""
    client, db, _bus = app_and_db
    frek_id = _init_identity(client)
    _register_first_credential(client, frek_id)

    client.post(
        f"/api/v1/identity/{frek_id}/register/begin",
        json={"label": "recovery-device"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    complete = client.post(
        f"/api/v1/identity/{frek_id}/register/complete",
        json={"credential": {"response": {}}, "label": "recovery-device"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert complete.status_code == 200, complete.text
    # IdentityPublicResponse doesn't echo raw credentials (never leaks them,
    # by design — see _to_public) so verify directly against the DB instead.
    import asyncio

    async def _fetch():
        return await db.frek_persons.find_one({"frek_id": frek_id})

    doc = asyncio.run(_fetch())
    assert len(doc["credentials"]) == 2
    assert {c["label"] for c in doc["credentials"]} == {"first", "recovery-device"}


def test_revoked_identity_cannot_be_recovered(app_and_db):
    """Recovery must never bypass a legitimate revocation — the existing
    revoked/archived guard in register_complete is unchanged and still
    applies on the admin-key path."""
    client, db, _bus = app_and_db
    frek_id = _init_identity(client)
    _register_first_credential(client, frek_id)

    import asyncio

    async def _revoke():
        await db.frek_persons.update_one(
            {"frek_id": frek_id}, {"$set": {"status": "revoked"}}
        )

    asyncio.run(_revoke())

    complete = client.post(
        f"/api/v1/identity/{frek_id}/register/complete",
        json={"credential": {"response": {}}, "label": "recovery-device"},
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert complete.status_code == 403, complete.text
