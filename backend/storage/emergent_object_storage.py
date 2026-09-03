"""EmergentObjectStorageProvider — wraps the storage FREKCORE actually uses.

Phase 3 correction (reports/16_INTEGRATION_TEST_BASELINE.md Priority 9):
Phase 2's `backend/storage/__init__.py` claimed local disk was "the only
storage backend this session has first-hand evidence FREKCORE actually
needs today." That was wrong. Reading `backend/moment/storage.py` (the
module that actually uploads media, called from
`backend/moment/routes.py:POST /sign-media`) shows FREKCORE's real,
currently-used storage is Emergent's remote, platform-hosted Object
Storage service (`https://integrations.emergentagent.com/objstore/api/v1/storage`),
authenticated with the `EMERGENT_LLM_KEY` environment variable
(`backend/moment/storage.py:23,36`) — not local disk at all. There is no
local-filesystem fallback in the existing code: when the key is absent,
`is_available()` returns False and `put_object`/`get_object` raise
`RuntimeError` (backend/moment/storage.py:60-61,84-85,97-98).

This adapter wraps the *exact same* HTTP calls
`backend/moment/storage.py` already makes, behind the `StorageProvider`
interface — it does not invent a new integration, it exposes the real one
through the typed interface. `LocalFilesystemStorageProvider` (added in
Phase 2) remains useful for local dev/tests, where `moment/storage.py`
itself has no equivalent (its only degraded mode is "disabled", not
"local").
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional, Tuple

import requests  # type: ignore[import-untyped]  # stubs unreachable from mypy's isolated tool venv here

from .provider import StoredObject

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"


class ObjectStorageUnavailable(RuntimeError):
    """Mirrors backend/moment/storage.py's own RuntimeError("Object Storage indisponible")."""


class EmergentObjectStorageProvider:
    """Same wire protocol as backend/moment/storage.py:init_storage/put_object/get_object.

    Kept independent of that module (no import of it) so this class has no
    side effect on the existing, already-working `moment` feature — this is
    a parallel, typed accessor to the same remote service, not a
    replacement wired into any route this phase.
    """

    def __init__(
        self, emergent_key: Optional[str] = None, app_prefix: str = "frekcore"
    ) -> None:
        self._key = emergent_key or os.environ.get("EMERGENT_LLM_KEY")
        self._app_prefix = app_prefix
        self._session_key: Optional[str] = None

    def _ensure_session(self) -> str:
        if self._session_key:
            return self._session_key
        if not self._key:
            raise ObjectStorageUnavailable(
                "EMERGENT_LLM_KEY absent — Object Storage disabled"
            )
        resp = requests.post(
            f"{STORAGE_URL}/init", json={"emergent_key": self._key}, timeout=30
        )
        resp.raise_for_status()
        self._session_key = resp.json()["storage_key"]
        return self._session_key

    def is_available(self) -> bool:
        try:
            self._ensure_session()
            return True
        except Exception:
            return False

    def put(self, path: str, data: bytes, content_type: str) -> StoredObject:
        key = self._ensure_session()
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120,
        )
        resp.raise_for_status()
        return StoredObject(
            path=path,
            size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            content_type=content_type,
        )

    def get(self, path: str) -> Tuple[bytes, str]:
        key = self._ensure_session()
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60
        )
        resp.raise_for_status()
        return resp.content, resp.headers.get(
            "Content-Type", "application/octet-stream"
        )

    def exists(self, path: str) -> bool:
        # backend/moment/storage.py has no HEAD/exists call against the
        # remote API either — mirrored here rather than invented.
        raise NotImplementedError(
            "The Emergent Object Storage API used by backend/moment/storage.py has no "
            "existence-check endpoint; this mirrors that real limitation rather than "
            "inventing one."
        )
