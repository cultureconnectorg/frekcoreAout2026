"""Storage abstraction (Phase 2, Priority 13).

The mission brief: create a `StorageProvider` interface able to support
Local / S3-compatible / Cloudinary / other providers later, but "ne pas
ajouter des providers inutilises juste pour remplir une checklist" — only
what is justified by a real need.

Real need found by audit: `backend/moment/storage.py` already implements a
single, concrete Object Storage backend (`put_object`/`get_object`,
`init_storage()` at backend/moment/storage.py:29,78,96) with no abstraction
layer above it — every caller talks to that module directly. This package
defines the `StorageProvider` interface that module's shape maps onto,
plus ONE reference implementation (`LocalFilesystemStorageProvider`) backed
by real local disk I/O — the only storage backend this session has
first-hand evidence FREKCORE actually needs today (local dev/tests).
S3/Cloudinary adapters are deliberately NOT stubbed out here: doing so
without a real integration would be exactly the "provider inutilise" the
brief warns against. See reports/13_PHASE2_GAP_ANALYSIS.md.

Not wired into backend/moment/storage.py or any route in this phase.
"""

from .provider import StorageProvider, StoredObject
from .local import LocalFilesystemStorageProvider

__all__ = ["StorageProvider", "StoredObject", "LocalFilesystemStorageProvider"]
