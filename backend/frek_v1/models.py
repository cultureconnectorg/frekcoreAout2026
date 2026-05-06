"""
FREK v1 — Modeles Pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class FrekStage(str, Enum):
    GENESIS = "GENESIS"
    WORKSHOP = "WORKSHOP"
    METAMORPHOSE = "METAMORPHOSE"
    EMISSION = "EMISSION"
    LEGACY = "LEGACY"


STAGE_ORDER = {
    FrekStage.GENESIS: 1,
    FrekStage.WORKSHOP: 2,
    FrekStage.METAMORPHOSE: 3,
    FrekStage.EMISSION: 4,
    FrekStage.LEGACY: 5,
}


# --- Auth ---
class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    grant_type: str = "client_credentials"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400


# --- Identity ---
class EmitRequest(BaseModel):
    email: str = Field(..., description="Email de l'identite culturelle")
    source: str = Field("api", description="Source de creation (api, scan, import)")
    event: Optional[str] = Field(None, description="Evenement associe (ex: CC2026)")
    metadata: Optional[dict] = Field(None, description="Metadonnees supplementaires")
    expires_at: Optional[str] = Field(None, description="Date ISO 8601 d'expiration (optionnel, perpetuel par defaut)")


class EmitResponse(BaseModel):
    frek_id: str
    created: bool
    stage: str = "GENESIS"
    message: str


class ActivateRequest(BaseModel):
    qr_token: Optional[str] = None


class RevokeRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Raison de la revocation (audit trail)")


class RenewRequest(BaseModel):
    expires_at: Optional[str] = Field(None, description="Nouvelle date d'expiration ISO (None = perpetuel)")
    reason: Optional[str] = Field(None, description="Justification (audit)")


class StatusResponse(BaseModel):
    frek_id: str
    active: bool
    current_stage: str
    stages_completed: List[str]
    progression: float
    created_at: str
    revoked: bool = False
    revoked_at: Optional[str] = None
    revoke_reason: Optional[str] = None
    expires_at: Optional[str] = None
    expired: bool = False


class DetailResponse(BaseModel):
    frek_id: str
    active: bool
    current_stage: str
    stages: List[dict]
    email_hash: str
    source: str
    event: Optional[str]
    created_at: str
    activated_at: Optional[str]


class LookupRequest(BaseModel):
    qr_token: str


# --- Stages ---
class StageRequest(BaseModel):
    stage: FrekStage
    fingerprint: str = Field(..., description="SHA256 fingerprint")
    source: str = Field("api", description="Source du stage")
    metadata: Optional[dict] = Field(None, description="Metadonnees du stage")


class StageResponse(BaseModel):
    id: str
    frek_id: str
    stage: str
    fingerprint: str
    sequence: int
    timestamp: str
    source: str


# --- Stats ---
class ClientStatsResponse(BaseModel):
    client_id: str
    total_identities: int
    active_identities: int
    stages_breakdown: dict
    recent_activity: List[dict]


# --- Admin ---
class CreateClientRequest(BaseModel):
    client_id: str
    name: str
    permissions: List[str] = Field(..., description="ex: ['emit', 'stage', 'stats']")


class ClientInfoResponse(BaseModel):
    client_id: str
    name: str
    permissions: List[str]
    created_at: str
