"""FREKCORE Python SDK (Phase 2, Priorite 7).

Scope, deliberately narrow: this SDK wraps only API families with strong,
reproducible evidence they're stable enough to commit to as a client
contract (a passing integration/unit run exercising the real FastAPI
router directly, see `sdk/python/tests/`). Adding a method for anything
less would mean "inventer des capacites", which the mission brief
explicitly forbids for Priority 7.

- `FrekcoreRegistryClient` — the full FREK Registry API
  (`/api/v1/registry/*`), including the Phase 1 schema-catalog surface and
  the P1 (2026-08-31) instance-store endpoints (`create_object`/
  `list_objects`/`get_object`). See `client.py`'s own header comment.
- `FrekcoreIdentityClient` — `identity_engine`'s public-READ surface only
  (`/api/v1/identity/*`: `get_identity`, `get_me`, `get_linked_objects`,
  `search_identities`), added P2 (2026-08-31) once that module's read
  endpoints had the same live-tested evidence the Registry API has
  (`reports/21_FREEZE_ASSESSMENT.md`'s SDK-contracts line named this as
  the next candidate). The write/lifecycle surface is intentionally not
  wrapped — see `identity_client.py`'s own header comment for why.

Every other FREKCORE API family (Proof/Notary, FK, Certificates, ...) is
explicitly NOT wrapped here yet — see reports/03_ARCHITECTURE_MAP.md for
what exists, and reports/12_PHASE2_IMPLEMENTATION.md for the recommended
order to extend this SDK once each family's contract is verified stable.
"""

from .client import FrekcoreRegistryClient, RegistryNamespace, ValidationResult
from .identity_client import FrekcoreIdentityClient

__all__ = [
    "FrekcoreRegistryClient",
    "RegistryNamespace",
    "ValidationResult",
    "FrekcoreIdentityClient",
]

__version__ = "0.2.0"
