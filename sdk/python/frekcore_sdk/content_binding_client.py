"""FrekcoreContentBindingClient — the D1 read surface
(`/api/v1/content-binding/*`), plus its own create() supported for
`FREKCORE_SDK_CONTRACT_V1.md`'s lean two-method-per-capability contract.

| Method       | Endpoint                                              |
|--------------|--------------------------------------------------------|
| get_binding   | GET  /api/v1/content-binding/binding/{binding_id}        |
| list_bindings  | GET  /api/v1/content-binding/{frek_id}                    |

See `backend/content_binding/routes.py` for the server-side
implementation. No method here corresponds to an endpoint that does not
exist. The multipart create endpoint (`POST /{frek_id}`) is intentionally
not wrapped this state — see `FREKCORE_SDK_CONTRACT_V1.md`'s own scope
note.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .errors import raise_for_frek_status


class FrekcoreContentBindingClient:
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

    def __enter__(self) -> "FrekcoreContentBindingClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def get_binding(self, binding_id: str) -> Dict[str, Any]:
        """GET /api/v1/content-binding/binding/{binding_id}. Public, no
        auth — evidence data is public-readable by design."""
        resp = self._client.get(f"/api/v1/content-binding/binding/{binding_id}")
        raise_for_frek_status(resp)
        return resp.json()

    def list_bindings(self, frek_id: str) -> Dict[str, Any]:
        """GET /api/v1/content-binding/{frek_id}. Public, no auth."""
        resp = self._client.get(f"/api/v1/content-binding/{frek_id}")
        raise_for_frek_status(resp)
        return resp.json()
