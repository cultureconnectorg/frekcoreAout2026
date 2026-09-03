"""FREKCORE Python SDK (Phase 2, Priorite 7 + STATE_7 API/SDK Contract
Stabilization, 2026-09-03).

Scope, deliberately narrow: this SDK wraps only API families with strong,
reproducible evidence they're stable enough to commit to as a client
contract (a passing integration/unit run exercising the real FastAPI
router directly, see `sdk/python/tests/`). Adding a method for anything
less would mean "inventer des capacites", which the mission brief
explicitly forbids for Priority 7 and STATE_7 both.

- `FrekcoreRegistryClient` — the full FREK Registry API
  (`/api/v1/registry/*`), including the Phase 1 schema-catalog surface and
  the P1 (2026-08-31) instance-store endpoints (`create_object`/
  `list_objects`/`get_object`). See `client.py`'s own header comment.
- `FrekcoreIdentityClient` — `identity_engine`'s public-READ surface only
  (`/api/v1/identity/*`: `get_identity`, `get_me`, `get_linked_objects`,
  `search_identities`), added P2 (2026-08-31). The write/lifecycle surface
  is intentionally not wrapped — see `identity_client.py`'s own header
  comment for why.
- `FrekcoreContentBindingClient`, `FrekcoreCreativeLifecycleClient`,
  `FrekcoreRelationshipGraphClient`, `FrekcoreOfflineTransportClient`,
  `FrekcoreTechnicalEvidenceReportClient` — added STATE_7, one canonical
  create/generate + one canonical read operation per D1–D5 capability,
  see each client's own module docstring and
  `docs/architecture/FREKCORE_SDK_CONTRACT_V1.md` for the full scope
  rationale.
- `errors` — the canonical error hierarchy (`FrekError` and its
  subclasses) every method above raises instead of a bare
  `httpx.HTTPStatusError`, per `docs/architecture/
  FREKCORE_ERROR_CONTRACT_V1.md`.

Every other FREKCORE API family (Proof/Notary, FK, Certificates, ...) is
explicitly NOT wrapped here yet — see reports/03_ARCHITECTURE_MAP.md for
what exists, and `docs/architecture/FREKCORE_SDK_CONTRACT_V1.md` for the
recommended order to extend this SDK once each family's contract is
verified stable.
"""

from .client import FrekcoreRegistryClient, RegistryNamespace, ValidationResult
from .identity_client import FrekcoreIdentityClient
from .content_binding_client import FrekcoreContentBindingClient
from .creative_lifecycle_client import FrekcoreCreativeLifecycleClient
from .relationship_graph_client import FrekcoreRelationshipGraphClient
from .offline_transport_client import FrekcoreOfflineTransportClient
from .technical_evidence_report_client import FrekcoreTechnicalEvidenceReportClient
from .errors import (
    AuthenticationError,
    AuthorityError,
    ConflictError,
    FrekError,
    InternalError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    UnsupportedVersionError,
    VerificationError,
    raise_for_frek_status,
)

__all__ = [
    "FrekcoreRegistryClient",
    "RegistryNamespace",
    "ValidationResult",
    "FrekcoreIdentityClient",
    "FrekcoreContentBindingClient",
    "FrekcoreCreativeLifecycleClient",
    "FrekcoreRelationshipGraphClient",
    "FrekcoreOfflineTransportClient",
    "FrekcoreTechnicalEvidenceReportClient",
    "FrekError",
    "InvalidRequestError",
    "AuthenticationError",
    "AuthorityError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "VerificationError",
    "UnsupportedVersionError",
    "InternalError",
    "raise_for_frek_status",
]

__version__ = "0.3.0"
