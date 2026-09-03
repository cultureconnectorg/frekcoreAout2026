"""FrekcoreIdentityClient — every method maps to a real, tested,
*public-read-only* endpoint of `identity_engine` (`/api/v1/identity/*`).

| Method               | Endpoint                                  | Auth                        |
|----------------------|--------------------------------------------|------------------------------|
| get_identity          | GET /api/v1/identity/{frek_id}              | none (public view)            |
| get_me                 | GET /api/v1/identity/me                      | X-FREK-Session (required)      |
| get_linked_objects      | GET /api/v1/identity/{frek_id}/objects        | X-FREK-Session (required)       |
| search_identities        | GET /api/v1/identity/search                    | X-Admin-Key (required)           |

See `backend/identity_engine/routes.py` for the server-side implementation
of each of these calls. No method here corresponds to an endpoint that
does not exist.

Scope, deliberately narrow (mirrors `client.py`'s own rationale): this
covers only identity_engine's READ surface. The write/lifecycle surface
(`init`, `register/*`, `authenticate/*`, `revocation`, update, archive,
`link-object`) is intentionally not wrapped yet — those either involve a
multi-step WebAuthn ceremony this SDK has no browser/authenticator
context to perform, or (merge/renew/recovery) have semantics still
pending a founder decision (`docs/decisions/0002-identity-lifecycle-
founder-decisions-needed.md`) — wrapping them now would mean committing
this SDK to a contract that may still change. `get_identity` never
returns credentials or other sensitive fields — see `_to_public()` in
the server route module.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .errors import raise_for_frek_status


class FrekcoreIdentityClient:
    """Thin, typed wrapper over `identity_engine`'s public-read endpoints
    (`/api/v1/identity/*`).

    Accepts either a `base_url` (constructs its own `httpx.Client`) or an
    already-configured `httpx.Client`-compatible transport — the latter is
    how `sdk/python/tests` exercises this class against the real FastAPI
    app in-process, with no live server needed (same pattern as
    `FrekcoreRegistryClient`).
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

    def __enter__(self) -> "FrekcoreIdentityClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def get_identity(self, frek_id: str) -> Dict[str, Any]:
        """GET /api/v1/identity/{frek_id}. Public, no auth — the server's
        own `_to_public()` strips credentials before this response is
        built, so this is safe to call with no session/admin context."""
        resp = self._client.get(f"/api/v1/identity/{frek_id}")
        raise_for_frek_status(resp)
        return resp.json()

    def get_me(self, session_token: str) -> Dict[str, Any]:
        """GET /api/v1/identity/me. Requires a valid holder session token
        (`X-FREK-Session`) — raises for a missing/expired/invalid one, same
        as the server route."""
        resp = self._client.get(
            "/api/v1/identity/me", headers={"X-FREK-Session": session_token}
        )
        raise_for_frek_status(resp)
        return resp.json()

    def get_linked_objects(self, frek_id: str, session_token: str) -> Dict[str, Any]:
        """GET /api/v1/identity/{frek_id}/objects. Requires a holder
        session valid for THIS `frek_id` specifically — the server route
        rejects a session that verifies to a different identity."""
        resp = self._client.get(
            f"/api/v1/identity/{frek_id}/objects",
            headers={"X-FREK-Session": session_token},
        )
        raise_for_frek_status(resp)
        return resp.json()

    def search_identities(
        self,
        *,
        admin_key: str,
        display_name: Optional[str] = None,
        status: Optional[str] = None,
        identity_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """GET /api/v1/identity/search. Admin-key only, no holder path —
        matches the server route's own design (a bulk-listing/enumeration
        surface has no per-holder analog, see `search_identities()`'s
        docstring in `backend/identity_engine/routes.py`)."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if display_name is not None:
            params["display_name"] = display_name
        if status is not None:
            params["status"] = status
        if identity_type is not None:
            params["identity_type"] = identity_type
        resp = self._client.get(
            "/api/v1/identity/search",
            params=params,
            headers={"X-Admin-Key": admin_key},
        )
        raise_for_frek_status(resp)
        return resp.json()
