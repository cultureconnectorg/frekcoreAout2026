"""StorageProvider — vendor-neutral interface.

Method shape mirrors backend/moment/storage.py's real functions
(`put_object(path, data, content_type)` / `get_object(path) -> (bytes, content_type)`,
backend/moment/storage.py:78,96) so that module could migrate to this
interface later without a caller-visible behavior change.
"""

from __future__ import annotations

from typing import Protocol, Tuple

from pydantic import BaseModel


class StoredObject(BaseModel):
    path: str
    size: int
    sha256: str
    content_type: str


class StorageProvider(Protocol):
    def put(self, path: str, data: bytes, content_type: str) -> StoredObject: ...

    def get(self, path: str) -> Tuple[bytes, str]:
        """Returns (data, content_type). Raises FileNotFoundError if absent."""
        ...

    def exists(self, path: str) -> bool: ...
