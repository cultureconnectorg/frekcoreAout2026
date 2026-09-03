"""STATE_7 — API/SDK Contract Stabilization: the canonical error
vocabulary (`docs/architecture/FREKCORE_ERROR_CONTRACT_V1.md`).

Pure module — no FastAPI import, no route dependency, importable from
any future canonical route without a circular-import risk. Existing
D1–D5 routes are NOT retrofitted to use this this state
(`REWRITE_D1_D6_ARCHITECTURE=FALSE` — retrofitting ~40 raise sites across
5 modules mid-contract-stabilization is exactly the invasive change that
rule exists to prevent). This is the vocabulary new canonical endpoints
should adopt going forward, and the exact vocabulary the SDK error
models (`sdk/python/frekcore_sdk/errors.py`,
`sdk/typescript/src/errors.ts`) mirror.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """The founder's own named STATE_7 error taxonomy, verbatim — no
    additional code invented."""

    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    STALE_AUTHORITY = "STALE_AUTHORITY"
    REVOKED = "REVOKED"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# The one canonical HTTP status each code maps to by default — an
# endpoint MAY choose a different status for a real, documented reason
# (e.g. STALE_AUTHORITY is often reported inline in a 200 response body,
# never raised as this exception at all), this is the default a new
# endpoint should reach for absent such a reason.
_DEFAULT_HTTP_STATUS: Dict[ErrorCode, int] = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.AUTHENTICATION_REQUIRED: 401,
    ErrorCode.AUTHORITY_DENIED: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.IDEMPOTENCY_CONFLICT: 409,
    ErrorCode.VERIFICATION_FAILED: 422,
    ErrorCode.STALE_AUTHORITY: 409,
    ErrorCode.REVOKED: 403,
    ErrorCode.UNSUPPORTED_VERSION: 400,
    ErrorCode.INTERNAL_ERROR: 500,
}


class CanonicalError(Exception):
    """A canonical, structured FREKCORE API error. `details` must only
    ever carry disclosure-safe fields (no credential/key material, no
    raw Mongo `_id`, no internal exception text) — the caller building
    one is responsible for that, matching every existing D1-D5 route's
    own manual discipline of never leaking internals into a `detail`
    string (see FREKCORE_ERROR_CONTRACT_V1.md's own audit)."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status or _DEFAULT_HTTP_STATUS[code]
        self.details = details or {}

    def to_detail(self) -> Dict[str, Any]:
        """The structured `detail` body — strictly additive over the
        plain-string convention existing routes use (a caller reading
        `.detail` as a string on an old route is unaffected; only a
        route that adopts this returns this shape instead)."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }

    def to_http_exception(self):
        """Builds the FastAPI `HTTPException` a route actually raises.
        Imports FastAPI lazily so this module stays importable (and
        unit-testable) with zero FastAPI/route dependency at module
        load time."""
        from fastapi import HTTPException

        return HTTPException(status_code=self.http_status, detail=self.to_detail())
