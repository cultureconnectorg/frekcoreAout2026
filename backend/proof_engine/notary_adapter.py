"""Maps a real backend/notary BlockResponse onto an explicit ProofState.

This is a pure function over a dict shaped like
`backend/notary/models.py:BlockResponse` — it does not import `notary`
itself (keeping proof_engine importable with zero MongoDB/FastAPI
dependency, like backend/registry and backend/eventbus), and it does not
call the network. A caller that already has a block (from
`POST /api/v1/notary/notarize` or `db.notary_blocks`) passes its fields in.
"""

from __future__ import annotations

from typing import Any, Dict

from .models import ProofReceipt, ProofState


def proof_state_from_notary_block(
    subject_id: str, fingerprint_sha256: str, block: Dict[str, Any]
) -> ProofReceipt:
    """`block` is expected to have the same keys as
    backend/notary/models.py:BlockResponse (block_hash, height, timestamp,
    btc_anchored, btc_block_height, btc_attestation_time, ...).
    """
    btc_anchored = bool(block.get("btc_anchored"))
    ots_proof = block.get("ots_proof_b64")
    block_hash = block.get("block_hash")

    if btc_anchored:
        state = ProofState.EXTERNAL_ANCHOR_PROOF
    elif ots_proof:
        state = ProofState.OPENTIMESTAMPS_PROOF
    elif block.get("timestamp"):
        state = ProofState.TIMESTAMP_PROOF
    elif block_hash:
        # backend/notary/chain.py hash-chains blocks (block_hash =
        # sha256(prev_hash + payload_hash)) but does NOT itself apply an
        # Ed25519 signature to the block — verified by inspection: no
        # `sign`/`Ed25519` reference anywhere in backend/notary/*.py, and
        # BlockResponse (backend/notary/models.py) has no `signature` field.
        # This corrects an overclaim in ecosystem/registry.json's frek_chain
        # entry ("Ed25519 signed blocks") — see
        # reports/13_PHASE2_GAP_ANALYSIS.md. A block on its own is therefore
        # only LOCAL_PROOF; SIGNED_PROOF requires a separate Passport
        # envelope (backend/passport/service.py:build_passport, which IS
        # genuinely Ed25519-signed) — not represented in a bare BlockResponse,
        # so this adapter never returns SIGNED_PROOF from a block alone.
        state = ProofState.LOCAL_PROOF
    else:
        state = ProofState.FINGERPRINT

    return ProofReceipt(
        subject_id=subject_id,
        fingerprint_sha256=fingerprint_sha256,
        state=state,
        block_hash=block_hash,
        block_height=block.get("height"),
        timestamp=block.get("timestamp"),
        ots_proof_b64=ots_proof,
        btc_block_height=block.get("btc_block_height"),
        btc_attestation_time=block.get("btc_attestation_time"),
    )
