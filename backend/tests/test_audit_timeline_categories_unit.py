"""Audit-event separation (P2, 2026-08-31 — reports/FREKCORE_COMPLETION_
BACKLOG.md P2 #4): unit tests for backend/audit/routes.py's `category`
field and the notary_blocks filter fix.

Isolated FastAPI app + TestClient + mongomock_motor (no live server
needed). `GET /audit/{frek_id}` has no auth dependency, so this can be
tested directly without mocking frek_v1's OAuth2 chain.
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

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-audit-test")

import mongomock_motor  # noqa: E402

import audit.routes as audit_routes  # noqa: E402
from audit.routes import audit_router, _category, CATEGORIES  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture()
def app_and_db():
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_audit_test"]
    audit_routes.set_db(db)
    app = FastAPI()
    app.include_router(audit_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db


def _seed(db, frek_id):
    async def _run():
        await db.frek_identities.insert_one(
            {
                "frek_id": frek_id,
                "client_id": "issuer-1",
                "created_at": "2026-08-31T00:00:00+00:00",
                "source": "test",
                "event": "test-event",
                "expires_at": None,
            }
        )
        await db.notary_blocks.insert_one(
            {
                "payload_id": frek_id,
                "payload_type": "identity_recovery",
                "timestamp": "2026-08-31T01:00:00+00:00",
                "height": 1,
                "block_hash": "abc123",
                "btc_anchored": False,
                "payload_data": {"new_credential_label": "recovery-device"},
                "metadata": {},
            }
        )
        await db.notary_blocks.insert_one(
            {
                "payload_id": frek_id,
                "payload_type": "identity_reconciliation",
                "timestamp": "2026-08-31T02:00:00+00:00",
                "height": 2,
                "block_hash": "def456",
                "btc_anchored": False,
                "payload_data": {"reconciled_frek_id": "id-other"},
                "metadata": {},
            }
        )
        await db.frek_stages.insert_one(
            {
                "frek_id": frek_id,
                "stage": "WORKSHOP",
                "sequence": 1,
                "timestamp": "2026-08-31T00:30:00+00:00",
                "client_id": "issuer-1",
            }
        )
        await db.scans.insert_one(
            {
                "frek_id": frek_id,
                "zone": "backstage",
                "timestamp": "2026-08-31T00:45:00+00:00",
                "scan_id": "scan-1",
                "agent_id": "agent-1",
            }
        )
        await db.transactions.insert_one(
            {
                "frek_id": frek_id,
                "type": "PAIEMENT",
                "montant_jetons": 5,
                "timestamp": "2026-08-31T00:50:00+00:00",
                "tx_id": "tx-1",
                "agent_id": "agent-1",
            }
        )

    asyncio.run(_run())


def test_every_category_value_is_one_of_the_four_named_categories():
    named = {"identity_security", "work_lifecycle", "operational_access", "financial"}
    for kind, category in CATEGORIES.items():
        assert category in named, f"{kind!r} maps to an unnamed category {category!r}"


def test_unknown_kind_defaults_to_operational_access():
    assert _category("some-future-kind-nobody-mapped-yet") == "operational_access"


def test_timeline_includes_recovery_and_reconciliation_events(app_and_db):
    """Regression guard for the exact gap this pass found: the notary_blocks
    filter previously silently omitted identity_recovery/
    identity_reconciliation from a holder's own timeline."""
    client, db = app_and_db
    frek_id = "id-audittest01-ab12"
    _seed(db, frek_id)

    resp = client.get(f"/api/v1/audit/{frek_id}")
    assert resp.status_code == 200, resp.text
    events = resp.json()
    kinds = {e["kind"] for e in events}
    assert "identity_recovery" in kinds
    assert "identity_reconciliation" in kinds


def test_timeline_events_carry_the_correct_category_per_kind(app_and_db):
    client, db = app_and_db
    frek_id = "id-audittest02-cd34"
    _seed(db, frek_id)

    resp = client.get(f"/api/v1/audit/{frek_id}")
    assert resp.status_code == 200, resp.text
    by_kind = {e["kind"]: e["category"] for e in resp.json()}

    assert by_kind["identity_emit"] == "identity_security"
    assert by_kind["identity_recovery"] == "identity_security"
    assert by_kind["identity_reconciliation"] == "identity_security"
    assert by_kind["stage"] == "work_lifecycle"
    assert by_kind["scan"] == "operational_access"
    assert by_kind["transaction"] == "financial"


def test_timeline_can_be_filtered_by_category_client_side(app_and_db):
    """Proves the actual point of adding the field: a consumer that wants
    only security-relevant events can now do so without re-deriving the
    kind->category mapping itself."""
    client, db = app_and_db
    frek_id = "id-audittest03-ef56"
    _seed(db, frek_id)

    resp = client.get(f"/api/v1/audit/{frek_id}")
    events = resp.json()
    security_only = [e for e in events if e["category"] == "identity_security"]
    assert len(security_only) == 3  # identity_emit, recovery, reconciliation
    assert all(e["category"] != "financial" for e in security_only)
