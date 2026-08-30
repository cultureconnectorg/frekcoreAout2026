"""FrekcoreRegistryClient — every method maps to a real, tested endpoint.

| Method              | Endpoint                                        |
|----------------------|--------------------------------------------------|
| list_versions         | GET  /api/v1/registry/versions                  |
| list_namespaces        | GET  /api/v1/registry/namespaces                 |
| get_namespace_schema     | GET  /api/v1/registry/namespaces/{namespace}      |
| validate                | POST /api/v1/registry/validate                    |
| list_events              | GET  /api/v1/registry/events                     |

See backend/registry/routes.py for the server-side implementation each of
these calls. No method here corresponds to an endpoint that does not exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class RegistryNamespace:
    namespace: str
    version: str
    title: str
    description: str
    schema_url: str


@dataclass
class ValidationResult:
    valid: bool
    namespace: str
    schema_version: str
    errors: List[str]


class FrekcoreRegistryClient:
    """Thin, typed wrapper over `/api/v1/registry/*`.

    Accepts either a `base_url` (constructs its own `httpx.Client`) or an
    already-configured `httpx.Client`/`httpx.AsyncClient`-compatible
    transport — the latter is how sdk/python/tests exercise this class
    against the real FastAPI app in-process, with no live server needed.
    """

    def __init__(
        self, base_url: Optional[str] = None, *, client: Optional[httpx.Client] = None
    ) -> None:
        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            if not base_url:
                raise ValueError("base_url is required when no client is provided")
            self._client = httpx.Client(base_url=base_url.rstrip("/"))
            self._owns_client = True

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "FrekcoreRegistryClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def list_versions(self) -> Dict[str, Any]:
        resp = self._client.get("/api/v1/registry/versions")
        resp.raise_for_status()
        return resp.json()

    def list_namespaces(self, schema_version: str = "v1") -> List[RegistryNamespace]:
        resp = self._client.get(
            "/api/v1/registry/namespaces", params={"schema_version": schema_version}
        )
        resp.raise_for_status()
        return [RegistryNamespace(**row) for row in resp.json()]

    def get_namespace_schema(
        self, namespace: str, schema_version: str = "v1"
    ) -> Dict[str, Any]:
        resp = self._client.get(
            f"/api/v1/registry/namespaces/{namespace}",
            params={"schema_version": schema_version},
        )
        resp.raise_for_status()
        return resp.json()

    def validate(
        self, namespace: str, payload: Dict[str, Any], schema_version: str = "v1"
    ) -> ValidationResult:
        resp = self._client.post(
            "/api/v1/registry/validate",
            json={
                "namespace": namespace,
                "payload": payload,
                "schema_version": schema_version,
            },
        )
        resp.raise_for_status()
        body = resp.json()
        return ValidationResult(**body)

    def list_events(self) -> Dict[str, Any]:
        resp = self._client.get("/api/v1/registry/events")
        resp.raise_for_status()
        return resp.json()
