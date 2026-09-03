"""Observability primitives (Phase 2, Priority 9).

- `RequestIdMiddleware`: a small Starlette/ASGI middleware that assigns a
  request ID (from `X-Request-ID` if the caller supplied one, else a fresh
  uuid4) and a correlation ID, exposes them via a contextvar
  (`current_request_id()`/`current_correlation_id()`) for logging, and
  echoes them back as response headers.
- `metrics`: a small, fixed set of Prometheus counters/histograms named
  exactly after the mission brief's minimum list (HTTP requests, latency,
  errors, Registry operations, identity operations, proof operations, event
  operations) — no metrics for capabilities that do not exist yet.

Neither is wired into backend/server.py in this phase. Wiring
`RequestIdMiddleware` is a one-line `app.add_middleware(...)` change to a
file this phase deliberately kept to a minimal, reviewed diff (see
reports/12_PHASE2_IMPLEMENTATION.md) — left for the next session once this
module has been reviewed.
"""

from .request_id import RequestIdMiddleware, current_correlation_id, current_request_id
from .metrics import registry as metrics_registry
from . import metrics

__all__ = [
    "RequestIdMiddleware",
    "current_request_id",
    "current_correlation_id",
    "metrics",
    "metrics_registry",
]
