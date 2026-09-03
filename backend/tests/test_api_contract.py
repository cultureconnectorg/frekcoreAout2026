"""STATE_7 — API/SDK Contract Stabilization: contract regression tests.

Builds an isolated FastAPI app from the real canonical D1-D6 routers plus
the real legacy `frek_router`, and checks:

1. OpenAPI generation succeeds for the combined canonical surface
   (acceptance #25).
2. No duplicate (method, path) operation exists across the canonical
   `/api/v1/...` routers (`FREKCORE_API_CONTRACT_V1.md`'s own "no
   duplicate canonical routes" section).
3. Every one of the 19 historical `backend/frek/` routes is still present
   in the generated OpenAPI surface (a stronger, schema-level companion
   to `test_legacy_compatibility.py::TestRouteCountGuard`).
4. A golden snapshot of the canonical (method, path) surface
   (`tests/fixtures/api_contract_snapshot.json`) — this test fails loudly
   if the canonical surface changes shape, which is exactly the point:
   a real snapshot-diff test proves it *can* detect a breaking change
   (acceptance #26), not merely that it exists.

No database is touched — constructing a FastAPI app from real routers and
calling `.openapi()` never executes a route handler, so no `set_db` call
is needed for this file's purposes.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
from fastapi import FastAPI

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "dev-only-not-a-real-secret-api-contract-test")
os.environ["FREK_DISABLE_RATE_LIMIT"] = "1"
os.environ.setdefault(
    "FREK_PASSPORT_KEY_PATH", "/tmp/frekcore_test_api_contract_passport_key.pem"
)

from frek.routes import frek_router  # noqa: E402
from content_binding.routes import content_binding_router  # noqa: E402
from creative_lifecycle.routes import creative_lifecycle_router  # noqa: E402
from relationship_graph.routes import relationship_graph_router  # noqa: E402
from offline_transport.routes import offline_transport_router  # noqa: E402
from technical_evidence_report.routes import (  # noqa: E402
    technical_evidence_report_router,
)
from identity_engine.routes import identity_router  # noqa: E402

pytestmark = pytest.mark.unit

SNAPSHOT_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "api_contract_snapshot.json"
)

# The 19 historical routes, method + full path, re-verified from code in
# STATE_6/STATE_7 (see docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md
# and FREKCORE_API_CONTRACT_V1.md) -- not re-derived here, imported as the
# fixed expectation this test locks in.
LEGACY_19_ROUTES: Set[Tuple[str, str]] = {
    ("POST", "/api/frek/certify"),
    ("POST", "/api/frek/certify/upload"),
    ("GET", "/api/frek/verify/{frek_id}"),
    ("POST", "/api/frek/genesis"),
    ("POST", "/api/frek/workshop"),
    ("GET", "/api/frek/advanced/reseau"),
    ("GET", "/api/frek/advanced/reseau/stats"),
    ("GET", "/api/frek/advanced/reseau/node/{node_id}"),
    ("GET", "/api/frek/advanced/reseau/neighbors/{node_id}"),
    ("GET", "/api/frek/advanced/reseau/artiste/{artiste_id}"),
    ("GET", "/api/frek/advanced/reseau/lieu/{lieu_id}"),
    ("GET", "/api/frek/advanced/reseau/path"),
    ("GET", "/api/frek/advanced/transmission"),
    ("GET", "/api/frek/advanced/transmission/protocols"),
    ("GET", "/api/frek/advanced/transmission/protocol/{protocol}"),
    ("POST", "/api/frek/advanced/transmission/packet"),
    ("POST", "/api/frek/advanced/transmission/watermark"),
    ("POST", "/api/frek/advanced/transmission/sync"),
    ("POST", "/api/frek/advanced/juridique/attestation"),
}


def _build_app() -> FastAPI:
    app = FastAPI(title="FREKCORE contract-test app")
    app.include_router(frek_router, prefix="/api")
    app.include_router(content_binding_router, prefix="/api/v1")
    app.include_router(creative_lifecycle_router, prefix="/api/v1")
    app.include_router(relationship_graph_router, prefix="/api/v1")
    app.include_router(offline_transport_router, prefix="/api/v1")
    app.include_router(technical_evidence_report_router, prefix="/api/v1")
    app.include_router(identity_router, prefix="/api/v1")
    return app


def _canonical_routes(app: FastAPI) -> List[Tuple[str, str]]:
    """(method, path) pairs for every route mounted under /api/v1 --
    "canonical" per FREKCORE_API_CONTRACT_V1.md's own definition."""
    out = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if not methods or not path or not path.startswith("/api/v1/"):
            continue
        for method in methods:
            if method == "HEAD":
                continue
            out.append((method, path))
    return out


def test_openapi_schema_generates_successfully():
    app = _build_app()
    schema = app.openapi()
    assert schema["openapi"]
    assert schema["paths"]
    # A meaningful sample of canonical paths must be present, not just
    # "some schema came back".
    assert "/api/v1/content-binding/{frek_id}" in schema["paths"]
    assert "/api/v1/reports/technical-evidence" in schema["paths"]


def test_no_duplicate_canonical_method_path_pairs():
    app = _build_app()
    routes = _canonical_routes(app)
    seen: Dict[Tuple[str, str], int] = {}
    for pair in routes:
        seen[pair] = seen.get(pair, 0) + 1
    duplicates = {pair: count for pair, count in seen.items() if count > 1}
    assert (
        not duplicates
    ), f"duplicate canonical (method, path) pairs found: {duplicates}"


def test_all_19_legacy_routes_present_in_openapi_surface():
    app = _build_app()
    schema = app.openapi()
    present: Set[Tuple[str, str]] = set()
    for path, methods in schema["paths"].items():
        for method in methods:
            if method.upper() == "HEAD":
                continue
            present.add((method.upper(), path))
    missing = LEGACY_19_ROUTES - present
    assert not missing, f"legacy routes missing from OpenAPI surface: {missing}"


def test_canonical_surface_matches_golden_snapshot():
    """A real snapshot-diff test: if this fails, the canonical `/api/v1/...`
    surface genuinely changed shape since the snapshot was captured --
    exactly the "detect a real breaking contract change" acceptance
    criterion. To intentionally evolve the contract, regenerate the
    snapshot file deliberately (never silently) and note the change in
    docs/architecture/FREKCORE_API_CONTRACT_V1.md."""
    app = _build_app()
    actual = sorted(f"{method} {path}" for method, path in _canonical_routes(app))

    if not SNAPSHOT_PATH.exists():
        pytest.fail(f"missing golden snapshot at {SNAPSHOT_PATH}")

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert actual == expected, (
        "canonical /api/v1/... surface no longer matches the golden "
        "snapshot -- if this is an intentional, reviewed contract "
        "change, regenerate tests/fixtures/api_contract_snapshot.json "
        "deliberately."
    )
