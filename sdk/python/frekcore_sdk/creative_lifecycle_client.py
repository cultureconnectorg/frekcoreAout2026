"""FrekcoreCreativeLifecycleClient — D2's genesis-start + history-read
surface (`/api/v1/creative-lifecycle/*`).

| Method        | Endpoint                                   |
|----------------|----------------------------------------------|
| start_genesis   | POST /api/v1/creative-lifecycle/genesis         |
| get_history      | GET  /api/v1/creative-lifecycle/{pre_id}         |

See `backend/creative_lifecycle/routes.py`. WORKSHOP/METAMORPHOSE/
EMISSION/LEGACY (all multipart or reference-only writes) are
intentionally not wrapped this state — see
`FREKCORE_SDK_CONTRACT_V1.md`'s own scope note.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .errors import raise_for_frek_status


class FrekcoreCreativeLifecycleClient:
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

    def __enter__(self) -> "FrekcoreCreativeLifecycleClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    @staticmethod
    def _auth_headers(
        session_token: Optional[str], admin_key: Optional[str]
    ) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if session_token:
            headers["X-FREK-Session"] = session_token
        if admin_key:
            headers["X-Admin-Key"] = admin_key
        return headers

    def start_genesis(
        self,
        *,
        concept: Optional[str] = None,
        lieu: Optional[str] = None,
        description: Optional[str] = None,
        session_token: Optional[str] = None,
        admin_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/creative-lifecycle/genesis. Requires a holder
        session or an admin key, same as the server route."""
        resp = self._client.post(
            "/api/v1/creative-lifecycle/genesis",
            json={"concept": concept, "lieu": lieu, "description": description},
            headers=self._auth_headers(session_token, admin_key),
        )
        raise_for_frek_status(resp)
        return resp.json()

    def get_history(self, pre_id: str) -> Dict[str, Any]:
        """GET /api/v1/creative-lifecycle/{pre_id}. Public, no auth --
        lifecycle history is public-readable, matching D1's own
        disclosure stance."""
        resp = self._client.get(f"/api/v1/creative-lifecycle/{pre_id}")
        raise_for_frek_status(resp)
        return resp.json()
