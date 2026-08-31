"""RENEW (docs/decisions/0003-identity-lifecycle-founder-decisions-
implemented.md §2) — regression test locking in the finding that
`frek_v1`'s existing `POST /{frek_id}/renew` already conforms to the
approved semantics: it only ever mutates `expires_at`/`renewed_at`, never
`frek_id` itself, and never mints a replacement identity.

No code in `frek_v1/identity.py` was changed by the RENEW decision — this
test exists so that invariant is enforced going forward, not just
asserted once in the ADR's prose. Isolated FastAPI app + TestClient +
mongomock_motor (same technique as sdk/python/tests/test_registry_client.py's
`sdk_client_with_db` fixture), no live server needed.
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

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-renew-test")

import mongomock_motor  # noqa: E402

import frek_v1.auth as frek_v1_auth  # noqa: E402
import frek_v1.identity as frek_v1_identity  # noqa: E402
from frek_v1.identity import identity_router  # noqa: E402
from frek_v1.utils import create_access_token, hash_secret  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture()
def app_and_db():
    db = mongomock_motor.AsyncMongoMockClient()["frekcore_renew_test"]
    frek_v1_auth.set_db(db)
    frek_v1_identity.set_db(db)

    app = FastAPI()
    app.include_router(identity_router, prefix="/api/v1")
    client = TestClient(app)
    return client, db


@pytest.fixture()
def issuer_token(app_and_db):
    import asyncio

    _client, db = app_and_db
    client_id = "renew-test-issuer"

    async def _seed():
        await db.frek_clients.insert_one(
            {
                "client_id": client_id,
                "secret_hash": hash_secret("unused"),
                "permissions": ["emit"],
                "active": True,
            }
        )

    asyncio.run(_seed())
    return create_access_token(client_id)


@pytest.fixture()
def seeded_identity(app_and_db, issuer_token):
    import asyncio

    _client, db = app_and_db
    frek_id = "id-renewtest001-ab12"

    async def _seed():
        await db.frek_identities.insert_one(
            {
                "frek_id": frek_id,
                "client_id": "renew-test-issuer",
                "created_at": "2026-08-30T00:00:00+00:00",
                "current_stage": "GENESIS",
                "stages_completed": [],
                "active": False,
                "revoked": False,
                "expires_at": None,
            }
        )

    asyncio.run(_seed())
    return frek_id


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_renew_never_changes_frek_id(app_and_db, issuer_token, seeded_identity):
    client, _db = app_and_db
    frek_id = seeded_identity
    resp = client.post(
        f"/api/v1/identity/{frek_id}/renew",
        json={"expires_at": "2099-01-01T00:00:00+00:00"},
        headers=_auth_header(issuer_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["frek_id"] == frek_id  # the one invariant this test exists for


def test_renew_only_mutates_expires_at_and_renewed_at(
    app_and_db, issuer_token, seeded_identity
):
    """Confirms the ADR's finding by direct DB inspection: no other field on
    the identity document changes, and no new document is created."""
    client, db = app_and_db
    frek_id = seeded_identity

    import asyncio

    async def _before():
        return await db.frek_identities.find_one({}, {"_id": 0})

    before = asyncio.run(_before())

    resp = client.post(
        f"/api/v1/identity/{frek_id}/renew",
        json={"expires_at": "2099-01-01T00:00:00+00:00"},
        headers=_auth_header(issuer_token),
    )
    assert resp.status_code == 200, resp.text

    async def _after():
        count = await db.frek_identities.count_documents({})
        doc = await db.frek_identities.find_one({}, {"_id": 0})
        return count, doc

    count, after = asyncio.run(_after())

    assert count == 1  # never mints a second/replacement identity
    for key in before:
        if key in ("expires_at", "renewed_at"):
            continue
        assert after[key] == before[key], f"renew changed unrelated field {key!r}"
    assert after["expires_at"] == "2099-01-01T00:00:00+00:00"
    assert after.get("renewed_at") is not None


def test_renew_rejects_a_past_expiry(app_and_db, issuer_token, seeded_identity):
    client, _db = app_and_db
    frek_id = seeded_identity
    resp = client.post(
        f"/api/v1/identity/{frek_id}/renew",
        json={"expires_at": "2020-01-01T00:00:00+00:00"},
        headers=_auth_header(issuer_token),
    )
    assert resp.status_code == 400


def test_renew_refuses_a_revoked_identity(app_and_db, issuer_token, seeded_identity):
    client, db = app_and_db
    frek_id = seeded_identity

    import asyncio

    async def _revoke():
        await db.frek_identities.update_one(
            {"frek_id": frek_id}, {"$set": {"revoked": True}}
        )

    asyncio.run(_revoke())

    resp = client.post(
        f"/api/v1/identity/{frek_id}/renew",
        json={"expires_at": "2099-01-01T00:00:00+00:00"},
        headers=_auth_header(issuer_token),
    )
    assert resp.status_code == 400
