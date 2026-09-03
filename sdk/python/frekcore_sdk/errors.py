"""FREKCORE Python SDK — canonical error hierarchy.

STATE_7 (`docs/architecture/FREKCORE_SDK_CONTRACT_V1.md`,
`FREKCORE_ERROR_CONTRACT_V1.md`). Maps HTTP status codes to a typed
exception hierarchy — every SDK client method (this file's own base
`_raise_for_frek_status` used by each) raises the matching subclass
instead of a raw `httpx.HTTPStatusError`.

`FrekError` subclasses `httpx.HTTPStatusError` — an existing caller of
`FrekcoreRegistryClient`/`FrekcoreIdentityClient` that already catches
`httpx.HTTPStatusError` keeps working unchanged; this is a strictly
additive typing refinement, not a breaking change (see the SDK contract
doc's own "strictly additive" note).
"""

from __future__ import annotations

from typing import Optional

import httpx


class FrekError(httpx.HTTPStatusError):
    """Base class for every canonical FREKCORE API error."""

    code: str = "INTERNAL_ERROR"


class InvalidRequestError(FrekError):
    code = "INVALID_REQUEST"


class AuthenticationError(FrekError):
    code = "AUTHENTICATION_REQUIRED"


class AuthorityError(FrekError):
    code = "AUTHORITY_DENIED"


class NotFoundError(FrekError):
    code = "NOT_FOUND"


class ConflictError(FrekError):
    code = "CONFLICT"


class RateLimitError(FrekError):
    code = "RATE_LIMITED"


class VerificationError(FrekError):
    code = "VERIFICATION_FAILED"


class UnsupportedVersionError(FrekError):
    code = "UNSUPPORTED_VERSION"


class InternalError(FrekError):
    code = "INTERNAL_ERROR"


_STATUS_TO_ERROR = {
    400: InvalidRequestError,
    401: AuthenticationError,
    403: AuthorityError,
    404: NotFoundError,
    409: ConflictError,
    422: InvalidRequestError,  # FastAPI/Pydantic validation default; see SDK contract doc §"SDK error model"
    429: RateLimitError,
}


def raise_for_frek_status(response: httpx.Response) -> None:
    """Drop-in replacement for `response.raise_for_status()` that raises
    a canonical `FrekError` subclass instead of a bare
    `httpx.HTTPStatusError` — every 2xx/3xx response is a silent no-op,
    matching `raise_for_status()`'s own contract exactly."""
    if response.is_success or response.is_redirect:
        return
    error_cls = _STATUS_TO_ERROR.get(response.status_code)
    if error_cls is None:
        error_cls = InternalError if response.status_code >= 500 else FrekError
    message = _error_message(response)
    raise error_cls(message, request=response.request, response=response)


def _error_message(response: httpx.Response) -> Optional[str]:
    try:
        body = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"
    if isinstance(body, dict):
        detail = body.get("detail", body)
        if isinstance(detail, dict):
            return detail.get("message") or str(detail)
        return str(detail)
    return str(body)
