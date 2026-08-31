"""Storage abstraction (Phase 2 Priority 13, corrected Phase 3 Priority 9).

The mission brief: create a `StorageProvider` interface able to support
Local / S3-compatible / Cloudinary / other providers later, but "ne pas
ajouter des providers inutilises juste pour remplir une checklist" — only
what is justified by a real need.

**Phase 3 correction**: Phase 2's docstring here claimed local disk was
"the only storage backend this session has first-hand evidence FREKCORE
actually needs today." That was wrong — see `emergent_object_storage.py`'s
docstring for the evidence. FREKCORE's real storage today is Emergent's
remote Object Storage API, used by `backend/moment/storage.py`, wrapped
here (parallel, not wired in) as `EmergentObjectStorageProvider`.
`LocalFilesystemStorageProvider` is kept — it is genuinely useful for local
dev/tests, where the real `moment/storage.py` has no local fallback at all
(only "disabled") — but it is not what production FREKCORE uses.

Neither implementation is wired into `backend/moment/storage.py` or any
route in this phase.
"""

from .provider import StorageProvider, StoredObject
from .local import LocalFilesystemStorageProvider
from .emergent_object_storage import (
    EmergentObjectStorageProvider,
    ObjectStorageUnavailable,
)

__all__ = [
    "StorageProvider",
    "StoredObject",
    "LocalFilesystemStorageProvider",
    "EmergentObjectStorageProvider",
    "ObjectStorageUnavailable",
]
