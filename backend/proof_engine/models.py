"""Explicit proof maturity states.

Ordered from weakest to strongest evidence of existence/integrity/origin.
Each state is a strict superset of guarantees over the previous one — see
`notary_adapter.py` for how a real `backend/notary` block maps onto these.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProofState(str, Enum):
    FINGERPRINT = "fingerprint"  # A hash exists. Nothing else.
    LOCAL_PROOF = "local_proof"  # Hash-chained into the local FREK-Chain (backend/notary/chain.py).
    SIGNED_PROOF = (
        "signed_proof"  # Additionally Ed25519-signed (backend/passport/keys.py).
    )
    TIMESTAMP_PROOF = "timestamp_proof"  # A timestamp claim exists (block.timestamp), not yet OTS-submitted.
    # An OTS proof artifact exists (backend/notary/anchor.py), pending Bitcoin confirmation.
    OPENTIMESTAMPS_PROOF = "opentimestamps_proof"
    EXTERNAL_ANCHOR_PROOF = "external_anchor_proof"  # OTS-confirmed against a Bitcoin block (btc_anchored=True).


# Total order, weakest first — used to compare/upgrade a receipt's state.
_STATE_ORDER = [
    ProofState.FINGERPRINT,
    ProofState.LOCAL_PROOF,
    ProofState.SIGNED_PROOF,
    ProofState.TIMESTAMP_PROOF,
    ProofState.OPENTIMESTAMPS_PROOF,
    ProofState.EXTERNAL_ANCHOR_PROOF,
]


def state_rank(state: ProofState) -> int:
    return _STATE_ORDER.index(state)


class ProofReceipt(BaseModel):
    """What a caller actually gets back — never claims more than `state` supports."""

    subject_id: str = Field(
        ..., description="FREK-ID or object id this proof is about."
    )
    fingerprint_sha256: str
    state: ProofState
    block_hash: Optional[str] = None
    block_height: Optional[int] = None
    signature: Optional[str] = None
    timestamp: Optional[str] = None
    ots_proof_b64: Optional[str] = None
    btc_block_height: Optional[int] = None
    btc_attestation_time: Optional[str] = None
