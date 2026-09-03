"""End-to-end test for FrekcoreTechnicalEvidenceReportClient — real
request/response cycles against the actual
`technical_evidence_report_router` FastAPI app, no live server or network
needed.

Run from repo root:
    PYTHONPATH=backend:sdk/python python3 -m pytest sdk/python/tests -v
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "backend"
SDK_DIR = REPO_ROOT / "sdk" / "python"
for p in (BACKEND_DIR, SDK_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-sdk-test")
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"

import technical_evidence_report.routes as ter_routes  # noqa: E402
from technical_evidence_report.routes import (  # noqa: E402
    technical_evidence_report_router,
)
from frekcore_sdk import FrekcoreTechnicalEvidenceReportClient, NotFoundError  # noqa: E402

pytestmark = pytest.mark.unit

ADMIN_KEY = os.environ["SECRET_KEY"]


@pytest.fixture()
def sdk_client_with_db():
    import mongomock_motor

    db = mongomock_motor.AsyncMongoMockClient()["frekcore_sdk_test_ter"]
    ter_routes.set_db(db)

    app = FastAPI()
    app.include_router(technical_evidence_report_router, prefix="/api/v1")
    test_client = TestClient(app)
    with FrekcoreTechnicalEvidenceReportClient(client=test_client) as client:
        yield client, db


def test_generate_report_then_verify_it_publicly(sdk_client_with_db):
    client, db = sdk_client_with_db

    async def _seed():
        await db.fk_objects.insert_one(
            {"frek_id": "fk-1", "object_type": "song", "created_at": "2026-09-03T00:00:00Z"}
        )

    asyncio.run(_seed())
    report = client.generate_report(
        subject_type="frek_object", subject_id="fk-1", admin_key=ADMIN_KEY
    )
    assert report["subject_id"] == "fk-1"
    report_id = report["report_id"]

    verification = client.verify_report(report_id)
    assert verification["integrity_verified"] is True
    assert "sections_summary" in verification
    # Public verification is shape-only -- never raw section content.
    assert "statements" not in str(verification["sections_summary"])


def test_verify_report_unknown_id_raises_not_found_error(sdk_client_with_db):
    client, _db = sdk_client_with_db
    with pytest.raises(NotFoundError):
        client.verify_report("does-not-exist")
