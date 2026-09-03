"""STATE_7 — canonical error vocabulary (backend/errors.py) unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from errors import CanonicalError, ErrorCode  # noqa: E402

pytestmark = pytest.mark.unit


def test_error_code_matches_founder_named_taxonomy_exactly():
    assert {c.value for c in ErrorCode} == {
        "INVALID_REQUEST",
        "AUTHENTICATION_REQUIRED",
        "AUTHORITY_DENIED",
        "NOT_FOUND",
        "CONFLICT",
        "RATE_LIMITED",
        "IDEMPOTENCY_CONFLICT",
        "VERIFICATION_FAILED",
        "STALE_AUTHORITY",
        "REVOKED",
        "UNSUPPORTED_VERSION",
        "INTERNAL_ERROR",
    }


@pytest.mark.parametrize(
    "code,expected_status",
    [
        (ErrorCode.INVALID_REQUEST, 400),
        (ErrorCode.AUTHENTICATION_REQUIRED, 401),
        (ErrorCode.AUTHORITY_DENIED, 403),
        (ErrorCode.NOT_FOUND, 404),
        (ErrorCode.CONFLICT, 409),
        (ErrorCode.RATE_LIMITED, 429),
        (ErrorCode.IDEMPOTENCY_CONFLICT, 409),
        (ErrorCode.VERIFICATION_FAILED, 422),
        (ErrorCode.REVOKED, 403),
        (ErrorCode.UNSUPPORTED_VERSION, 400),
        (ErrorCode.INTERNAL_ERROR, 500),
    ],
)
def test_default_http_status_mapping(code, expected_status):
    err = CanonicalError(code, "message")
    assert err.http_status == expected_status


def test_explicit_http_status_overrides_default():
    err = CanonicalError(ErrorCode.NOT_FOUND, "gone", http_status=410)
    assert err.http_status == 410


def test_to_detail_is_structured_and_safe():
    err = CanonicalError(
        ErrorCode.NOT_FOUND,
        "Binding X introuvable",
        details={"binding_id": "X"},
    )
    detail = err.to_detail()
    assert detail == {
        "code": "NOT_FOUND",
        "message": "Binding X introuvable",
        "details": {"binding_id": "X"},
    }


def test_details_defaults_to_empty_dict_never_none():
    err = CanonicalError(ErrorCode.INTERNAL_ERROR, "oops")
    assert err.to_detail()["details"] == {}


def test_to_http_exception_builds_a_real_fastapi_exception():
    from fastapi import HTTPException

    err = CanonicalError(ErrorCode.AUTHORITY_DENIED, "invalid_admin_key")
    http_exc = err.to_http_exception()
    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == 403
    assert http_exc.detail["code"] == "AUTHORITY_DENIED"


def test_module_has_zero_fastapi_dependency_at_import_time():
    """Confirms `errors.py` is importable standalone -- no route/FastAPI
    coupling at module load, only inside to_http_exception()."""
    src = (BACKEND_DIR / "errors.py").read_text()
    top_of_file = src.split("class CanonicalError")[0]
    assert "from fastapi" not in top_of_file
    assert "import fastapi" not in top_of_file
