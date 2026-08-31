"""POST /notary/anchor/force-upgrade — unit tests.

Historical P1 finding (memory/RESILIENCE_REPORT_v1.0.md, Sprint G,
section 4.1 point 2 + section 7 P1#3): the OTS upgrade queue had no
admin-gated on-demand drain distinct from the pre-existing `emit`-scoped
`/anchor/upgrade`. This file verifies the new endpoint's authorization
gate specifically (X-Admin-Key required, constant-time compare, wrong/
missing key rejected) and that it invokes the same `OTSAnchor.
upgrade_pending` capability `/anchor/upgrade` already uses — without
touching real OpenTimestamps calendars (`upgrade_pending` is
monkeypatched, same isolation technique as test_identity_recovery_unit.py
monkeypatching WebAuthn verification).
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

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-force-upgrade-test")

import mongomock_motor  # noqa: E402

import notary.routes as notary_routes  # noqa: E402
from notary.routes import notary_router  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def app_and_calls(monkeypatch):
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_force_upgrade_test"]
    notary_routes.set_db(db)

    calls = []

    async def _fake_upgrade_pending(self, max_blocks: int = 100):
        calls.append(max_blocks)
        return {"checked": 0, "upgraded": 0, "results": []}

    monkeypatch.setattr(
        notary_routes.OTSAnchor, "upgrade_pending", _fake_upgrade_pending
    )

    app = FastAPI()
    app.include_router(notary_router, prefix="/api/v1")
    client = TestClient(app)
    return client, calls, db


class TestForceUpgradeAuth:
    def test_missing_admin_key_rejected(self, app_and_calls):
        client, calls, _db = app_and_calls
        r = client.post("/api/v1/notary/anchor/force-upgrade")
        assert r.status_code == 401
        assert calls == []

    def test_wrong_admin_key_rejected(self, app_and_calls):
        client, calls, _db = app_and_calls
        r = client.post(
            "/api/v1/notary/anchor/force-upgrade",
            headers={"X-Admin-Key": "not-the-real-key"},
        )
        assert r.status_code == 401
        assert calls == []

    def test_correct_admin_key_accepted(self, app_and_calls):
        client, calls, _db = app_and_calls
        r = client.post(
            "/api/v1/notary/anchor/force-upgrade",
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert r.status_code == 200
        assert calls == [100]  # default max_blocks
        body = r.json()
        assert body == {"checked": 0, "upgraded": 0, "results": []}

    def test_max_blocks_param_forwarded(self, app_and_calls):
        client, calls, _db = app_and_calls
        r = client.post(
            "/api/v1/notary/anchor/force-upgrade?max_blocks=7",
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert r.status_code == 200
        assert calls == [7]

    def test_uses_same_upgrade_pending_capability_as_anchor_upgrade(
        self, app_and_calls
    ):
        """Not a new proof/upgrade mechanism -- the same
        OTSAnchor.upgrade_pending as the pre-existing, emit-scoped
        /anchor/upgrade endpoint. This endpoint only changes who may call
        it and under what header, never what it does."""
        client, calls, _db = app_and_calls
        client.post(
            "/api/v1/notary/anchor/force-upgrade",
            headers={"X-Admin-Key": ADMIN_KEY},
        )
        assert len(calls) == 1
