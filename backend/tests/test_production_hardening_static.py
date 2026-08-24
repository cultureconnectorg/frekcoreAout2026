"""Static regression checks for P0 production-hardening guardrails.

These checks deliberately require neither MongoDB nor an external deployment. They keep
security defaults reviewable even when the integration suite is not configured locally.
"""
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_server_requires_explicit_credentialed_cors_allowlist_and_nonblank_seed_secrets():
    source = (REPO_ROOT / "backend/server.py").read_text()

    assert "CORS_ORIGINS must be configured in production" in source
    assert '"*" in origins' in source
    assert "configured_client_secret" in source
    assert "Client API non initialise" in source
    assert 'hash_secret(os.environ.get("FREK_CLIENT_KILTIKONET_SECRET", ""))' not in source


def test_scanner_idempotency_keys_use_web_crypto_not_math_random():
    for relative_path in ("frontend/src/scan/lib.js", "frontend/src/pages/Scanner.jsx"):
        source = (REPO_ROOT / relative_path).read_text()
        function_source = source[source.index("function uuid()"):] if relative_path.endswith("lib.js") else source[source.index("function newUuid() "):]
        function_source = function_source.split("}\n", 1)[0]
        assert "crypto.getRandomValues" in function_source
        assert "Math.random" not in function_source


def test_staff_seed_requires_explicit_pin_outside_opt_in_development_mode():
    source = (REPO_ROOT / "backend/staff/routes.py").read_text()

    assert 'FREK_ALLOW_INSECURE_DEV_STAFF_PINS' in source
    assert 'os.environ.get(d["pin_env"], d["default_pin"])' not in source
    assert '"Staff account %s not seeded: configure %s"' in source


def test_unique_index_startup_never_drops_existing_indexes_without_preflight():
    source = (REPO_ROOT / "backend/server.py").read_text()
    migration = (REPO_ROOT / "backend/migrations/20260824_unique_index_preflight.py").read_text()

    helper = source[source.index("async def _ensure_unique_sparse_index"):source.index('@app.on_event("startup")', source.index("async def _ensure_unique_sparse_index"))]
    assert "drop_index" not in helper
    assert "duplicate values detected" in helper
    assert "TARGETS" in migration
