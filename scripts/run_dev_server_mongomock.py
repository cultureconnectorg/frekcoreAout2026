"""Run the real FREKCORE backend against an in-memory MongoDB-compatible mock.

*** THIS IS NOT A REPLACEMENT FOR A REAL MONGODB / REAL INTEGRATION TEST RUN. ***

Context (reports/16_INTEGRATION_TEST_BASELINE.md): this sandbox's Docker
daemon cannot pull any image (registry CDN blocks with 403 Forbidden — a
network policy boundary, not a technical failure to route around), so
`docker-compose.yml`'s `mongo` service cannot be brought up here. This
script exists as a documented, clearly-labeled substitute to get *some*
real-code-path evidence out of the actual `server.py` application (all 30+
modules, the real routes, the real Pydantic validation) when no real
MongoDB is reachable — not to claim real MongoDB behavior was verified.

It patches `motor.motor_asyncio.AsyncIOMotorClient` to
`mongomock_motor.AsyncMongoMockClient` *before* importing `server`, then
serves the real `app` with uvicorn. Known gaps vs. a real MongoDB:
  - No real network/auth/TLS behavior.
  - Aggregation pipeline operator coverage is a mongomock subset, not 1:1.
  - No replication, no real write concerns, no real index enforcement
    identical to MongoDB's on-disk behavior (mongomock enforces some
    constraints in-memory but this is not audited here).
  - Startup index creation code in server.py runs against the mock and may
    behave differently for edge cases (e.g. exact duplicate-key error
    shapes) — treat any FAILED test surfaced through this script as a
    *lead to investigate*, not proof of an application bug, until
    corroborated against a real MongoDB.

Usage:
    pip install mongomock mongomock_motor  # not in backend/requirements.txt —
                                            # a test-only tool, see reports/16
    MONGO_URL=mongodb://mock/ DB_NAME=frekcore_mongomock SECRET_KEY=dev-only \
    CORS_ORIGINS=http://localhost:3000 FREK_ENV=development \
    FREK_CLIENT_KILTIKONET_SECRET=dev-only FREK_CLIENT_CVLBRAIN_SECRET=dev-only \
    python3 scripts/run_dev_server_mongomock.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def _patch_motor_with_mongomock() -> None:
    import mongomock_motor
    import motor.motor_asyncio

    motor.motor_asyncio.AsyncIOMotorClient = mongomock_motor.AsyncMongoMockClient  # type: ignore[assignment]


def main() -> None:
    _patch_motor_with_mongomock()

    import uvicorn

    from server import app  # noqa: E402  (must import after the patch above)

    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
