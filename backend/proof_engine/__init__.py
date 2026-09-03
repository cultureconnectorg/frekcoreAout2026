"""Proof Engine readiness — explicit proof states + a ProofProvider interface
(Phase 2, Priority 12).

The mission brief's exact instruction: "Ne pas prétendre avoir une preuve
blockchain simplement parce qu'un hash existe. Séparer explicitement:
fingerprint/hash, local proof, signed proof, timestamp proof,
OpenTimestamps, external anchoring."

This package does exactly that, as a typed enum + Pydantic models, mapped
onto what backend/notary/ and backend/passport/ *actually* do today (see
`from_notary_block()` below) — it does not invent new cryptographic
capability, it makes the existing capability's maturity level explicit and
machine-checkable. No new blockchain integration is added; Bitcoin/OpenTimestamps
anchoring already exists in backend/notary/anchor.py and is left untouched.

D6 (founder execution protocol, 2026-09-01): `evidence_semantics.py` adds
Claim/Evidence/VerificationResult -- the two genuinely-missing primitives
identified in `reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md`
SS E's audit of the founder's evolved trust model. Purely additive: no
existing symbol in this package changes shape or behavior.
"""

from .models import ProofReceipt, ProofState
from .provider import ProofProvider
from .notary_adapter import proof_state_from_notary_block
from .evidence_semantics import (
    Claim,
    ClaimOrigin,
    Evidence,
    EvidenceKind,
    AuthorityStatus,
    VerificationResult,
)

__all__ = [
    "ProofReceipt",
    "ProofState",
    "ProofProvider",
    "proof_state_from_notary_block",
    "Claim",
    "ClaimOrigin",
    "Evidence",
    "EvidenceKind",
    "AuthorityStatus",
    "VerificationResult",
]
