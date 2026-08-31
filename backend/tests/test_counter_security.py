"""FREK Counter — P0 security regression (docs/decisions/0001-founder-decisions-2026-08-31.md).

Before this fix, POST /api/count (batch ingest) was reachable with no
credential at all — anyone could submit counts falsely attributed to any of
the 9 CVLN_SOURCES, polluting the cultural-impact scoring this feeds. No
test file previously covered this route.
"""

import os
import secrets

import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
# Real mount path (server.py: app.include_router(counter_router,
# prefix="/api/core"), counter_router itself prefix="/count") — NOT
# /api/count, which is what earlier reports said; corrected here and in
# the matrix (docs/decisions/0001-founder-decisions-2026-08-31.md).
API = f"{BASE_URL}/api/core/count"

ADMIN_KEY = os.environ.get("SECRET_KEY", "")


def H_admin():
    return {"X-Admin-Key": ADMIN_KEY}


def _entry():
    return {
        "external_ref": f"TEST-{secrets.token_hex(6)}",
        "action": "test_action",
        "source": "kiltikonet",
    }


class TestCountBatchAuth:
    def test_without_admin_key_is_rejected(self):
        r = requests.post(API, json={"entries": [_entry()]}, timeout=5)
        assert r.status_code == 403

    def test_with_wrong_admin_key_is_rejected(self):
        r = requests.post(
            API,
            json={"entries": [_entry()]},
            headers={"X-Admin-Key": "definitely-not-the-real-key"},
            timeout=5,
        )
        assert r.status_code == 403

    def test_with_admin_key_still_works(self):
        r = requests.post(
            API, json={"entries": [_entry()]}, headers=H_admin(), timeout=5
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("processed") == 1


class TestReadRoutesRemainPublic:
    """/sources, /rules, /stats are read-only reference data — the P0 fix
    must not have accidentally locked these down too."""

    def test_sources_remains_public(self):
        r = requests.get(f"{API}/sources", timeout=5)
        assert r.status_code == 200

    def test_stats_remains_public(self):
        r = requests.get(f"{API}/stats", timeout=5)
        assert r.status_code == 200
