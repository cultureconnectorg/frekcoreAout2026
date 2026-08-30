"""Unit tests for Proof Engine readiness states (Phase 2, Priority 12).

Pure Python — no notary module import, no MongoDB, no live server.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from proof_engine import ProofState, proof_state_from_notary_block  # noqa: E402
from proof_engine.models import state_rank  # noqa: E402

pytestmark = pytest.mark.unit


def test_state_order_is_strictly_increasing():
    ordered = [
        ProofState.FINGERPRINT,
        ProofState.LOCAL_PROOF,
        ProofState.SIGNED_PROOF,
        ProofState.TIMESTAMP_PROOF,
        ProofState.OPENTIMESTAMPS_PROOF,
        ProofState.EXTERNAL_ANCHOR_PROOF,
    ]
    ranks = [state_rank(s) for s in ordered]
    assert ranks == sorted(ranks)


def test_no_block_data_is_fingerprint_only():
    receipt = proof_state_from_notary_block("id-x", "a" * 64, block={})
    assert receipt.state == ProofState.FINGERPRINT


def test_block_hash_without_timestamp_or_ots_is_local_proof():
    """Reflects the real backend/notary/chain.py shape: a block_hash exists
    from hash-chaining, but the module has no Ed25519 signature on the block
    itself (verified: no `sign`/`Ed25519` reference in backend/notary/*.py)."""
    receipt = proof_state_from_notary_block(
        "id-x", "a" * 64, block={"block_hash": "deadbeef"}
    )
    assert receipt.state == ProofState.LOCAL_PROOF


def test_timestamp_present_upgrades_to_timestamp_proof():
    receipt = proof_state_from_notary_block(
        "id-x",
        "a" * 64,
        block={"block_hash": "deadbeef", "timestamp": "2026-08-30T00:00:00Z"},
    )
    assert receipt.state == ProofState.TIMESTAMP_PROOF


def test_ots_proof_upgrades_to_opentimestamps_proof():
    receipt = proof_state_from_notary_block(
        "id-x",
        "a" * 64,
        block={
            "block_hash": "deadbeef",
            "timestamp": "2026-08-30T00:00:00Z",
            "ots_proof_b64": "b64==",
        },
    )
    assert receipt.state == ProofState.OPENTIMESTAMPS_PROOF


def test_btc_anchored_is_the_strongest_state():
    receipt = proof_state_from_notary_block(
        "id-x",
        "a" * 64,
        block={
            "block_hash": "deadbeef",
            "timestamp": "2026-08-30T00:00:00Z",
            "ots_proof_b64": "b64==",
            "btc_anchored": True,
            "btc_block_height": 900000,
        },
    )
    assert receipt.state == ProofState.EXTERNAL_ANCHOR_PROOF
    assert receipt.btc_block_height == 900000


def test_receipt_never_claims_more_than_the_evidence_given():
    """No ots_proof_b64/btc fields on the receipt when the block never had them."""
    receipt = proof_state_from_notary_block(
        "id-x", "a" * 64, block={"block_hash": "deadbeef"}
    )
    assert receipt.ots_proof_b64 is None
    assert receipt.btc_block_height is None
