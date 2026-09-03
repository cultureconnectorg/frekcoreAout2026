"""D6 -- Evidence Semantics unit tests.

Each test maps directly to one item in the founder execution protocol's
D6_ACCEPTANCE_REQUIRED list -- these are not incidental type-checks, they
are the acceptance evidence for D6 itself. Pure Python, no notary/Mongo
import, no live server (same isolation as test_proof_engine.py).
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from proof_engine import (  # noqa: E402
    AuthorityStatus,
    Claim,
    ClaimOrigin,
    Evidence,
    EvidenceKind,
    ProofState,
    VerificationResult,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------
# CLAIM_NE_EVIDENCE
# ---------------------------------------------------------------------
class TestClaimNotEvidence:
    def test_claim_and_evidence_are_distinct_types(self):
        claim = Claim(
            subject_id="frek-001", origin=ClaimOrigin.DECLARED, statement="I made this"
        )
        evidence = Evidence(subject_id="frek-001", kind=EvidenceKind.COMPUTATION)
        assert not isinstance(claim, Evidence)
        assert not isinstance(evidence, Claim)

    def test_claim_has_no_evidence_or_proof_fields(self):
        claim = Claim(
            subject_id="frek-001", origin=ClaimOrigin.DECLARED, statement="I made this"
        )
        fields = set(type(claim).model_fields.keys())
        assert "kind" not in fields  # Evidence's discriminator
        assert "state" not in fields  # ProofReceipt's discriminator
        assert "signature_valid" not in fields  # VerificationResult's axis

    def test_evidence_can_reference_a_claim_but_is_a_separate_record(self):
        claim = Claim(
            subject_id="frek-001",
            origin=ClaimOrigin.OBSERVED,
            statement="captured on device",
        )
        evidence = Evidence(
            subject_id="frek-001",
            claim_id="claim-1",
            kind=EvidenceKind.OBSERVATION,
        )
        assert evidence.claim_id == "claim-1"
        assert claim.subject_id == evidence.subject_id


# ---------------------------------------------------------------------
# EVIDENCE_NE_PROOF
# ---------------------------------------------------------------------
class TestEvidenceNotProof:
    def test_evidence_has_no_proof_state_field(self):
        evidence = Evidence(subject_id="frek-001", kind=EvidenceKind.SIGNATURE)
        assert "state" not in type(evidence).model_fields

    def test_to_proof_state_hint_is_a_hint_not_a_claim_of_proof(self):
        sig_evidence = Evidence(subject_id="frek-001", kind=EvidenceKind.SIGNATURE)
        anchor_evidence = Evidence(subject_id="frek-001", kind=EvidenceKind.ANCHOR)
        assert sig_evidence.to_proof_state_hint() == ProofState.SIGNED_PROOF
        assert anchor_evidence.to_proof_state_hint() == ProofState.EXTERNAL_ANCHOR_PROOF

    @pytest.mark.parametrize(
        "kind",
        [
            EvidenceKind.OBSERVATION,
            EvidenceKind.ATTESTATION,
            EvidenceKind.COMPUTATION,
            EvidenceKind.INFERENCE,
        ],
    )
    def test_most_evidence_kinds_have_no_proof_state_equivalent(self, kind):
        evidence = Evidence(subject_id="frek-001", kind=kind)
        assert evidence.to_proof_state_hint() is None


# ---------------------------------------------------------------------
# PROOF_NE_VERIFICATION
# ---------------------------------------------------------------------
class TestProofNotVerification:
    def test_proof_state_is_optional_and_separate_from_verification_axes(self):
        result = VerificationResult(
            subject_id="frek-001", proof_state=ProofState.LOCAL_PROOF
        )
        assert result.proof_state == ProofState.LOCAL_PROOF
        # Having a proof_state alone does not make the result verified --
        # the verification axes (signature_valid, authority_status) are
        # untouched by proof_state.
        assert result.is_fully_verified is False

    def test_verification_result_without_any_proof_state_is_still_valid(self):
        result = VerificationResult(subject_id="frek-001")
        assert result.proof_state is None


# ---------------------------------------------------------------------
# INFERENCE_NE_VERIFIED_FACT
# ---------------------------------------------------------------------
class TestInferenceNotVerifiedFact:
    def test_inference_evidence_alone_never_yields_full_verification(self):
        Evidence(subject_id="frek-001", kind=EvidenceKind.INFERENCE)
        result = VerificationResult(subject_id="frek-001")  # nothing checked
        assert result.is_fully_verified is False

    def test_inferred_claim_origin_is_recorded_but_not_a_verification_axis(self):
        claim = Claim(
            subject_id="frek-001",
            origin=ClaimOrigin.INFERRED,
            statement="likely influenced by X",
        )
        assert claim.origin == ClaimOrigin.INFERRED
        # Claim has no verified/is_fully_verified concept at all.
        assert not hasattr(claim, "is_fully_verified")


# ---------------------------------------------------------------------
# SIGNATURE_VALID_NE_CURRENT_AUTHORITY
# ---------------------------------------------------------------------
class TestSignatureValidNotCurrentAuthority:
    def test_valid_signature_with_unknown_authority_is_not_fully_verified(self):
        result = VerificationResult(subject_id="frek-001", signature_valid=True)
        assert (
            result.authority_status == AuthorityStatus.UNKNOWN
        )  # default, not inferred
        assert result.is_fully_verified is False

    def test_valid_signature_with_revoked_authority_is_not_fully_verified(self):
        result = VerificationResult(
            subject_id="frek-001",
            signature_valid=True,
            authority_status=AuthorityStatus.REVOKED,
        )
        assert result.is_fully_verified is False

    def test_valid_signature_with_current_authority_is_fully_verified(self):
        result = VerificationResult(
            subject_id="frek-001",
            signature_valid=True,
            authority_status=AuthorityStatus.CURRENT,
        )
        assert result.is_fully_verified is True

    def test_current_authority_without_valid_signature_is_not_fully_verified(self):
        result = VerificationResult(
            subject_id="frek-001",
            signature_valid=False,
            authority_status=AuthorityStatus.CURRENT,
        )
        assert result.is_fully_verified is False

    def test_signature_valid_none_never_reads_as_verified(self):
        result = VerificationResult(
            subject_id="frek-001", authority_status=AuthorityStatus.CURRENT
        )
        assert result.signature_valid is None
        assert result.is_fully_verified is False


# ---------------------------------------------------------------------
# ANCHOR_NE_LEGAL_OWNERSHIP
# ---------------------------------------------------------------------
class TestAnchorNotLegalOwnership:
    def test_legal_status_defaults_to_none(self):
        result = VerificationResult(
            subject_id="frek-001", proof_state=ProofState.EXTERNAL_ANCHOR_PROOF
        )
        assert result.legal_status is None

    def test_legal_status_cannot_be_set_to_anything_but_none(self):
        with pytest.raises(ValidationError):
            VerificationResult(subject_id="frek-001", legal_status="owner")

    def test_external_anchor_proof_state_does_not_imply_full_verification(self):
        result = VerificationResult(
            subject_id="frek-001", proof_state=ProofState.EXTERNAL_ANCHOR_PROOF
        )
        assert result.is_fully_verified is False


# ---------------------------------------------------------------------
# BACKWARD_COMPATIBILITY
# ---------------------------------------------------------------------
class TestBackwardCompatibility:
    def test_existing_proof_engine_symbols_are_unchanged(self):
        from proof_engine import (
            ProofReceipt,
            ProofProvider,
            proof_state_from_notary_block,
        )
        from proof_engine.models import state_rank

        receipt = proof_state_from_notary_block("id-x", "a" * 64, block={})
        assert receipt.state == ProofState.FINGERPRINT
        assert state_rank(ProofState.FINGERPRINT) == 0
        assert ProofProvider is not None
        assert ProofReceipt is not None

    def test_new_symbols_are_exported_from_the_package_root(self):
        import proof_engine

        for name in (
            "Claim",
            "ClaimOrigin",
            "Evidence",
            "EvidenceKind",
            "AuthorityStatus",
            "VerificationResult",
        ):
            assert name in proof_engine.__all__
            assert hasattr(proof_engine, name)

    def test_evidence_semantics_module_has_no_side_effects_on_import(self):
        # Re-importing must not raise and must not mutate any existing
        # ProofState/ProofReceipt behavior.
        import importlib
        import proof_engine.evidence_semantics as mod

        importlib.reload(mod)
        assert mod.ProofState is ProofState
