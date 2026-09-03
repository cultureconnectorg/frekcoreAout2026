"""Prometheus metrics — the mission brief's exact minimum list, no more.

`registry` is a dedicated `CollectorRegistry` (not the global default) so
importing this module in tests never pollutes/duplicate-registers against
any other module's metrics — a real problem with prometheus_client's
process-global default registry when multiple test files import the same
counters. A future `GET /metrics` route (not added in this phase) would
call `generate_latest(registry)`.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Histogram

registry = CollectorRegistry()

http_requests_total = Counter(
    "frekcore_http_requests_total",
    "Total HTTP requests handled",
    labelnames=("method", "path", "status"),
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "frekcore_http_request_duration_seconds",
    "HTTP request latency",
    labelnames=("method", "path"),
    registry=registry,
)

http_errors_total = Counter(
    "frekcore_http_errors_total",
    "Total HTTP 5xx responses",
    labelnames=("method", "path"),
    registry=registry,
)

registry_operations_total = Counter(
    "frekcore_registry_operations_total",
    "FREK Registry operations (Bloc 1)",
    labelnames=("operation", "namespace"),
    registry=registry,
)

identity_operations_total = Counter(
    "frekcore_identity_operations_total",
    "Identity Engine operations",
    labelnames=("operation",),
    registry=registry,
)

proof_operations_total = Counter(
    "frekcore_proof_operations_total",
    "Proof Engine operations",
    labelnames=("operation", "state"),
    registry=registry,
)

event_operations_total = Counter(
    "frekcore_event_operations_total",
    "Event Bus publish/subscribe operations",
    labelnames=("event_type", "operation"),
    registry=registry,
)
