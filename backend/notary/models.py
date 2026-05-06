"""FREK Notary — Modeles Pydantic"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class NotarizeRequest(BaseModel):
    payload_type: str = Field(..., description="identity_emit | stage_transition | badge_issued | jeton_tx | custom")
    payload_id: str = Field(..., description="ID metier (ex: frek_id)")
    payload_data: dict = Field(..., description="Donnees a hasher (deterministe)")
    metadata: Optional[dict] = Field(default_factory=dict)


class BlockResponse(BaseModel):
    height: int
    prev_hash: str
    payload_type: str
    payload_id: str
    payload_hash: str
    block_hash: str
    timestamp: str
    metadata: dict
    event_id: Optional[str] = None
    spec_version: str = "1.0.0"
    btc_anchored: bool = False
    btc_block_height: Optional[int] = None
    btc_attestation_time: Optional[str] = None


class ProofResponse(BaseModel):
    payload_id: str
    block: BlockResponse
    chain_proof: dict = Field(..., description="Preuve cryptographique locale")
    ots_proof_b64: Optional[str] = Field(None, description="Preuve OpenTimestamps en base64")
    btc_anchored: bool = False
    btc_attestation: Optional[dict] = None
    verification_url: Optional[str] = None


class ChainStatusResponse(BaseModel):
    height: int
    spec_version: str = "1.0.0"
    genesis_at: Optional[str]
    last_block_at: Optional[str]
    last_block_hash: str
    total_anchored: int
    total_btc_confirmed: int
    pending_anchors: int
    last_anchor_at: Optional[str]
    integrity_ok: bool
    calendars: List[str]
    events: Optional[List[str]] = Field(default_factory=list, description="Liste des event_id uniques")


class VerifyResponse(BaseModel):
    valid: bool
    height: int
    blocks_checked: int
    first_invalid_height: Optional[int] = None
    message: str
