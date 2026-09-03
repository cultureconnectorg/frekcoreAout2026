"""FrekcoreRelationshipGraphClient — D3's assert + bounded-read surface
(`/api/v1/relationships/*`).

| Method            | Endpoint                                          |
|--------------------|------------------------------------------------------|
| create_relationship  | POST /api/v1/relationships                              |
| get_neighbors          | GET  /api/v1/relationships/entity/{entity_id}/neighbors   |

See `backend/relationship_graph/routes.py`. `verify`/`revoke` and the
`/traverse/path`/`/{id}/history` reads are intentionally not wrapped this
state — see `FREKCORE_SDK_CONTRACT_V1.md`'s own scope note.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .errors import raise_for_frek_status


class FrekcoreRelationshipGraphClient:
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

    def __enter__(self) -> "FrekcoreRelationshipGraphClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def create_relationship(
        self,
        *,
        subject_id: str,
        predicate: str,
        object_id: str,
        origin: str,
        statement: str,
        subject_type: Optional[str] = None,
        object_type: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        session_token: Optional[str] = None,
        admin_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/relationships. `origin` is one of the D6
        `ClaimOrigin` values ("declared", "observed", "attested",
        "computed", "inferred") -- a holder session may only
        self-assert "declared"; other origins require an admin key,
        matching the server route's own authority split."""
        headers: Dict[str, str] = {}
        if session_token:
            headers["X-FREK-Session"] = session_token
        if admin_key:
            headers["X-Admin-Key"] = admin_key
        resp = self._client.post(
            "/api/v1/relationships",
            json={
                "subject_id": subject_id,
                "subject_type": subject_type,
                "predicate": predicate,
                "object_id": object_id,
                "object_type": object_type,
                "origin": origin,
                "statement": statement,
                "data": data or {},
            },
            headers=headers,
        )
        raise_for_frek_status(resp)
        return resp.json()

    def get_neighbors(
        self, entity_id: str, *, direction: str = "both", limit: int = 200
    ) -> Dict[str, Any]:
        """GET /api/v1/relationships/entity/{entity_id}/neighbors.
        Optionally authenticated -- an unauthenticated call sees only
        GLOBAL-visibility relationships, matching the server route's own
        per-section `Scope` redaction."""
        resp = self._client.get(
            f"/api/v1/relationships/entity/{entity_id}/neighbors",
            params={"direction": direction, "limit": limit},
        )
        raise_for_frek_status(resp)
        return resp.json()
