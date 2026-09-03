"""Request ID / Correlation ID — contextvar-backed, ASGI middleware.

Pure-Starlette implementation (no new dependency): `BaseHTTPMiddleware` is
already transitively available via `starlette`, already pinned in
backend/requirements.txt.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_request_id_var: ContextVar[Optional[str]] = ContextVar("frek_request_id", default=None)
_correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "frek_correlation_id", default=None
)

REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"


def current_request_id() -> Optional[str]:
    return _request_id_var.get()


def current_correlation_id() -> Optional[str]:
    return _correlation_id_var.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns/propagates a request ID and correlation ID per request.

    - `X-Request-ID`: always fresh per request unless the caller supplied
      one (some clients want to correlate their own retries).
    - `X-Correlation-ID`: propagated from the caller if present, else set
      equal to the request ID (this request is then the start of its own
      correlation chain).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or request_id

        request_id_token = _request_id_var.set(request_id)
        correlation_id_token = _correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            _request_id_var.reset(request_id_token)
            _correlation_id_var.reset(correlation_id_token)

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
