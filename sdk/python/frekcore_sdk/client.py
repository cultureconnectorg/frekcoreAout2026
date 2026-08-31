"""FrekcoreRegistryClient — every method maps to a real, tested endpoint.

| Method              | Endpoint                                        |
|----------------------|--------------------------------------------------|
| list_versions         | GET  /api/v1/registry/versions                  |
| list_namespaces        | GET  /api/v1/registry/namespaces                 |
| get_namespace_schema     | GET  /api/v1/registry/namespaces/{namespace}      |
| validate                | POST /api/v1/registry/validate                    |
| list_events              | GET  /api/v1/registry/events                     |
| create_object            | POST /api/v1/registry/objects/{namespace}          |
| list_objects             | GET  /api/v1/registry/objects/{namespace}          |
| get_object               | GET  /api/v1/registry/objects/{namespace}/{frek_id} |

See backend/registry/routes.py for the server-side implementation each of
these calls. No method here corresponds to an endpoint that does not exist.

`create_object` requires the same authority the server itself requires
(`backend/registry/routes.py::_authorize_write`): either a `bearer_token`
(an OAuth2 client holding the `registry:write` permission) or a
`session_token` (an `identity_engine` holder session, `X-FREK-Session`) —
see that function's own docstring for the full ISSUER/OWNER rationale.
This client does not choose one for you; a call with neither raises the
same 403 the server would.
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

    @staticmethod
    def _write_auth_headers(
        bearer_token: Optional[str], session_token: Optional[str]
    ) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        if session_token:
            headers["X-FREK-Session"] = session_token
        return headers

    def create_object(
        self,
        namespace: str,
        payload: Dict[str, Any],
        *,
        schema_version: str = "v1",
        bearer_token: Optional[str] = None,
        session_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/registry/objects/{namespace}.

        `payload` is the namespace-specific fields only (e.g. `frek.artist`'s
        `display_name`) — envelope fields (`frek_id`, `entity_type`, `status`,
        `created_at`, `version`) are filled in server-side, matching
        `RegistryObjectCreateRequest`'s own contract.
        """
        resp = self._client.post(
            f"/api/v1/registry/objects/{namespace}",
            json={"payload": payload, "schema_version": schema_version},
            headers=self._write_auth_headers(bearer_token, session_token),
        )
        resp.raise_for_status()
        return resp.json()

    def list_objects(
        self,
        namespace: str,
        *,
        schema_version: str = "v1",
        owner_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/v1/registry/objects/{namespace}. Public, no auth required —
        matches the server route's own public-read design."""
        params: Dict[str, Any] = {
            "schema_version": schema_version,
            "limit": limit,
            "offset": offset,
        }
        if owner_id is not None:
            params["owner_id"] = owner_id
        if status is not None:
            params["status"] = status
        resp = self._client.get(f"/api/v1/registry/objects/{namespace}", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_object(
        self, namespace: str, frek_id: str, *, schema_version: str = "v1"
    ) -> Dict[str, Any]:
        """GET /api/v1/registry/objects/{namespace}/{frek_id}. Public, no auth."""
        resp = self._client.get(
            f"/api/v1/registry/objects/{namespace}/{frek_id}",
            params={"schema_version": schema_version},
        )
        resp.raise_for_status()
        return resp.json()
