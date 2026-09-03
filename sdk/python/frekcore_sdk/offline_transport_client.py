"""FrekcoreOfflineTransportClient — D4's protocol-catalog + envelope-read
surface (`/api/v1/offline/*`).

| Method        | Endpoint                                       |
|----------------|----------------------------------------------------|
| get_protocols   | GET /api/v1/offline/protocols                        |
| get_envelope     | GET /api/v1/offline/envelopes/{envelope_id}            |

See `backend/offline_transport/routes.py`. Envelope create/receive/sync
(signature-bearing writes) and device registration are intentionally not
wrapped this state — see `FREKCORE_SDK_CONTRACT_V1.md`'s own scope note.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .errors import raise_for_frek_status


class FrekcoreOfflineTransportClient:
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

    def __enter__(self) -> "FrekcoreOfflineTransportClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def get_protocols(self) -> Dict[str, Any]:
        """GET /api/v1/offline/protocols. Public, no auth."""
        resp = self._client.get("/api/v1/offline/protocols")
        raise_for_frek_status(resp)
        return resp.json()

    def get_envelope(
        self, envelope_id: str, *, session_token: Optional[str] = None, admin_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """GET /api/v1/offline/envelopes/{envelope_id}. Requires the
        issuing holder's own session or an admin key, matching the
        server route."""
        headers: Dict[str, str] = {}
        if session_token:
            headers["X-FREK-Session"] = session_token
        if admin_key:
            headers["X-Admin-Key"] = admin_key
        resp = self._client.get(
            f"/api/v1/offline/envelopes/{envelope_id}", headers=headers
        )
        raise_for_frek_status(resp)
        return resp.json()
