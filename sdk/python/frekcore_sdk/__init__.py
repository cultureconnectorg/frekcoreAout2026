"""FREKCORE Python SDK (Phase 2, Priorite 7).

Scope, deliberately narrow: this SDK wraps ONLY the FREK Registry API
(`/api/v1/registry/*`), because that is the one API family this phase has
strong, reproducible evidence is stable — it shipped in Phase 1
(reports/01_FORENSIC_AUDIT.md, reports/02_GAP_ANALYSIS.md Bloc 1), has a
dedicated versioned contract (backend/registry/schemas/v1/), and 10/21
passing unit tests plus this SDK's own end-to-end tests (see
sdk/python/tests/) exercise it directly against the real FastAPI router.

Every other FREKCORE API family (Identity, Proof/Notary, FK, Certificates,
...) is explicitly NOT wrapped here. Not because they don't exist — they do,
see reports/03_ARCHITECTURE_MAP.md — but because this phase has no evidence
(a passing integration run, see reports/10_TEST_INFRASTRUCTURE.md) that
their current shape is what should be committed to as a client contract.
Adding methods for them now would mean "inventer des capacites", which the
mission brief explicitly forbids for Priority 7. See
reports/12_PHASE2_IMPLEMENTATION.md for the full reasoning and the
recommended order to extend this SDK once each family's contract is
verified stable.
"""

from .client import FrekcoreRegistryClient, RegistryNamespace, ValidationResult

__all__ = ["FrekcoreRegistryClient", "RegistryNamespace", "ValidationResult"]

__version__ = "0.1.0"
