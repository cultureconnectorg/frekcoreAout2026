"""LocalFilesystemStorageProvider — real local-disk implementation.

The only StorageProvider implementation in this phase, backed by genuine
file I/O under a configurable root directory (defaults to a temp-style path,
never a hardcoded `/app/...` — see reports/10_TEST_INFRASTRUCTURE.md for why
that pattern was flagged elsewhere in this codebase).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple

from .provider import StoredObject


class LocalFilesystemStorageProvider:
    def __init__(self, root: str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        # Reject absolute paths / parent traversal — `path` is caller-controlled.
        candidate = (self._root / path).resolve()
        if (
            self._root.resolve() not in candidate.parents
            and candidate != self._root.resolve()
        ):
            raise ValueError(f"path escapes storage root: {path}")
        return candidate

    def put(self, path: str, data: bytes, content_type: str) -> StoredObject:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        (target.parent / f"{target.name}.content-type").write_text(content_type)
        return StoredObject(
            path=path,
            size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            content_type=content_type,
        )

    def get(self, path: str) -> Tuple[bytes, str]:
        target = self._resolve(path)
        if not target.exists():
            raise FileNotFoundError(path)
        content_type_file = target.parent / f"{target.name}.content-type"
        content_type = (
            content_type_file.read_text()
            if content_type_file.exists()
            else "application/octet-stream"
        )
        return target.read_bytes(), content_type

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()
