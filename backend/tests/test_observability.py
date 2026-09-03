"""Unit tests for observability primitives (Phase 2, Priority 9).

No MongoDB, no live server — an isolated FastAPI app for the middleware
test, and direct assertions against a dedicated CollectorRegistry for
metrics.
"""

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from observability.request_id import (  # noqa: E402
    RequestIdMiddleware,
    current_correlation_id,
    current_request_id,
)
from observability import metrics  # noqa: E402

pytestmark = pytest.mark.unit


@pytest.fixture()
def client():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/probe")
    async def probe():
        return {
            "request_id": current_request_id(),
            "correlation_id": current_correlation_id(),
        }

    return TestClient(app)


def test_generates_a_fresh_request_id_when_none_supplied(client):
    resp = client.get("/probe")
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"]
    assert resp.headers["X-Correlation-ID"] == resp.headers["X-Request-ID"]
    body = resp.json()
    assert body["request_id"] == resp.headers["X-Request-ID"]


def test_echoes_a_caller_supplied_request_id(client):
    resp = client.get("/probe", headers={"X-Request-ID": "caller-supplied-123"})
    assert resp.headers["X-Request-ID"] == "caller-supplied-123"


def test_propagates_a_caller_supplied_correlation_id_independently(client):
    resp = client.get(
        "/probe",
        headers={
            "X-Request-ID": "req-1",
            "X-Correlation-ID": "corr-shared-across-many-requests",
        },
    )
    assert resp.headers["X-Request-ID"] == "req-1"
    assert resp.headers["X-Correlation-ID"] == "corr-shared-across-many-requests"


def test_two_requests_get_different_request_ids(client):
    r1 = client.get("/probe")
    r2 = client.get("/probe")
    assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]


def test_metrics_registry_exposes_the_brief_minimum_set():
    metrics.http_requests_total.labels(
        method="GET", path="/api/v1/registry/namespaces", status="200"
    ).inc()
    metrics.registry_operations_total.labels(
        operation="validate", namespace="frek.artist"
    ).inc()

    output = generate_latest(metrics.registry).decode()
    assert "frekcore_http_requests_total" in output
    assert "frekcore_http_request_duration_seconds" in output
    assert "frekcore_http_errors_total" in output
    assert "frekcore_registry_operations_total" in output
    assert "frekcore_identity_operations_total" in output
    assert "frekcore_proof_operations_total" in output
    assert "frekcore_event_operations_total" in output
