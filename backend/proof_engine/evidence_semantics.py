"""D6 -- Evidence Semantics (a transverse rule, not a sixth capability).

Founder decision D6 (`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md`
SS C, SS E): FREKCORE must be able to distinguish, at the type level, a
handful of concepts the historical `backend/frek/` routes routinely
conflated. SS E's own audit against the founder's evolved trust model
(IDENTITY -> AUTHORITY -> OBJECT -> EVENT -> CLAIM/ASSERTION -> PROVENANCE
-> EVIDENCE -> PROOF -> VERIFICATION) found 7 of 9 concepts already exist
under some name (IDENTITY, AUTHORITY, OBJECT, EVENT, PROVENANCE, PROOF,
VERIFICATION) -- CLAIM and EVIDENCE were the one genuine, narrow gap. This
module adds exactly those two, as typed Pydantic models, plus a
VerificationResult type that makes the founder's required distinctions
structurally impossible to collapse.

What this module deliberately does NOT do:

- It does not touch `proof_engine/models.py` -- ProofState/ProofReceipt
  (PROOF) are unchanged, already a clean 6-level ladder that "never
  claims more than state supports" (see that module's own docstring).
- It does not create a second proof/trust engine -- Claim and Evidence
  sit *above* ProofState in the founder's chain, feeding into it, not
  replacing it.
- It does not wire into any existing route, model, or event producer --
  no behavior anywhere in FREKCORE changes by this file existing. Per
  the founder's execution protocol, D6 is a foundation for the later,
  separately-authorized D1-D5 work, not a retrofit of it.
- It does not invent an identity/object system -- `subject_id`,
  `claimant_id`, and `produced_by` are plain string ids, the exact same
  convention `proof_engine.models.ProofReceipt.subject_id` already uses.

Required distinctions (founder invariants), and how each is enforced here:

- CLAIM_EQUALS_EVIDENCE=FALSE, CLAIM_EQUALS_PROOF=FALSE,
  CLAIM_EQUALS_VERIFIED_FACT=FALSE: `Claim` carries no proof/verification
  field of any kind -- it is exactly "someone/something asserted X".
- EVIDENCE_EQUALS_PROOF=FALSE: `Evidence` has no `state: ProofState`
  field; `to_proof_state_hint()` returns a *hint*, never a claim that
  proof already exists, and returns None for most evidence kinds.
- PROOF_EQUALS_VERIFICATION=FALSE: `VerificationResult.proof_state` is
  optional and separate from the axes that actually decide
  `is_fully_verified`.
- SIGNATURE_VALID_EQUALS_CLAIM_TRUE=FALSE: `signature_valid` says a
  signature checks out cryptographically, nothing about the signed
  claim's truth.
- SIGNATURE_VALID_EQUALS_CURRENT_AUTHORITY=FALSE: `signature_valid` and
  `authority_status` are independent fields; `is_fully_verified` requires
  both, and `authority_status` defaults to UNKNOWN rather than being
  inferred from `signature_valid`.
- ANCHOR_EXISTS_EQUALS_LEGAL_OWNERSHIP=FALSE and
  ANCHOR_EXISTS_EQUALS_LEGAL_AUTHORSHIP=FALSE: `legal_status` is typed
  `None` -- the schema has no place to put a legal claim, by construction
  (see the field's own docstring).
- INFERENCE_EQUALS_VERIFIED_FACT=FALSE and
  CRYPTOGRAPHICALLY_VALID_EQUALS_FULLY_VERIFIED=FALSE: `is_fully_verified`
  is a read-only computed property, never a settable input -- an
  INFERENCE-kind Evidence, or a signature check alone, can never make it
  True on their own.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .models import ProofState


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ClaimOrigin(str, Enum):
    """How a claim came to exist -- who/what is asserting it.

    Covers the founder's DISTINGUISH_OBSERVATION_WHERE_REQUIRED,
    DISTINGUISH_ATTESTATION_WHERE_REQUIRED,
    DISTINGUISH_COMPUTATION_WHERE_REQUIRED, and
    DISTINGUISH_INFERENCE_WHERE_REQUIRED goals for the assertion side.
    """

    DECLARED = "declared"  # A human/actor stated it directly (e.g. a GENESIS intent).
    OBSERVED = (
        "observed"  # A device/sensor recorded it (e.g. an FAP capture, a geo trail).
    )
    ATTESTED = "attested"  # A third party formally attests it (e.g. a notary block).
    COMPUTED = "computed"  # Derived by a deterministic algorithm (e.g. a hash).
    INFERRED = "inferred"  # Derived by a non-deterministic/statistical process (e.g. similarity).


class Claim(BaseModel):
    """An assertion about a subject. Not evidence. Not proof. Not verified.

    See module docstring for CLAIM_EQUALS_EVIDENCE/CLAIM_EQUALS_PROOF/
    CLAIM_EQUALS_VERIFIED_FACT=FALSE -- there is no field on this type
    that could be mistaken for any of those three.
    """

    subject_id: str = Field(..., description="FREK-ID or object id the claim is about.")
    claimant_id: Optional[str] = Field(
        None, description="Who/what made the claim (identity/device id), if known."
    )
    origin: ClaimOrigin
    statement: str = Field(..., description="Human-readable content of the claim.")
    data: dict = Field(default_factory=dict, description="Structured claim payload.")
    made_at: datetime = Field(default_factory=_now)


class EvidenceKind(str, Enum):
    """What kind of material backs a claim.

    A Claim's `origin` and its supporting Evidence's `kind` are
    independent: an OBSERVED claim can still have zero Evidence records
    (e.g. an unwitnessed human statement never followed up).
    """

    OBSERVATION = "observation"
    ATTESTATION = "attestation"
    COMPUTATION = "computation"
    INFERENCE = "inference"
    SIGNATURE = "signature"
    ANCHOR = "anchor"


class Evidence(BaseModel):
    """Material supporting a claim. Not proof by itself.

    See module docstring for EVIDENCE_EQUALS_PROOF=FALSE.
    """

    subject_id: str
    claim_id: Optional[str] = Field(
        None, description="Which Claim this evidence supports, if any."
    )
    kind: EvidenceKind
    data: dict = Field(
        default_factory=dict,
        description="The supporting material itself (a hash, an observation payload, etc).",
    )
    produced_by: Optional[str] = None
    produced_at: datetime = Field(default_factory=_now)

    def to_proof_state_hint(self) -> Optional[ProofState]:
        """Best-effort suggestion of where a *future* real proof pipeline
        could start from this evidence -- never a claim that proof
        already exists. Returns None for every evidence kind that has no
        unambiguous proof-engine equivalent.
        """
        if self.kind == EvidenceKind.SIGNATURE:
            return ProofState.SIGNED_PROOF
        if self.kind == EvidenceKind.ANCHOR:
            return ProofState.EXTERNAL_ANCHOR_PROOF
        return None


class AuthorityStatus(str, Enum):
    """SIGNATURE_VALID_EQUALS_CURRENT_AUTHORITY=FALSE, made explicit: a
    signature can be cryptographically valid while the signer's authority
    to have made it has since changed."""

    CURRENT = "current"  # Checked live/fresh: the signer holds this authority now.
    STALE = "stale"  # Checked against a cached/offline state, may be outdated.
    REVOKED = "revoked"  # Explicitly known to no longer hold this authority.
    UNKNOWN = "unknown"  # Not checked / cannot be determined right now.


class VerificationResult(BaseModel):
    """The result of checking evidence/proof against a claim.

    Deliberately has no single collapsing "verified: bool" input field --
    each axis is recorded independently, and `is_fully_verified` is a
    read-only computed property so nothing upstream can set "verified"
    directly without the axes actually supporting it. See the module
    docstring for the full list of invariants this type enforces.
    """

    subject_id: str
    signature_valid: Optional[bool] = None
    authority_status: AuthorityStatus = AuthorityStatus.UNKNOWN
    proof_state: Optional[ProofState] = None
    checked_at: datetime = Field(default_factory=_now)
    legal_status: None = Field(
        default=None,
        description=(
            "Always None. FREKCORE technical proof never asserts legal "
            "ownership/authorship/qualified-timestamp status (D5's legal-"
            "hardening guardrail). This field exists only so that "
            "guardrail is visible in the schema -- it is not meant to be "
            "populated, and any non-None value fails validation."
        ),
    )

    @property
    def is_fully_verified(self) -> bool:
        """True only when every independently-checked axis supports it.

        A missing/unknown axis (None, or AuthorityStatus.UNKNOWN) can
        never read as True -- see INFERENCE_EQUALS_VERIFIED_FACT=FALSE
        and CRYPTOGRAPHICALLY_VALID_EQUALS_FULLY_VERIFIED=FALSE in the
        module docstring.
        """
        return bool(
            self.signature_valid and self.authority_status == AuthorityStatus.CURRENT
        )
