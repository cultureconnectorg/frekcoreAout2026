"""Identity Engine — modeles Pydantic.

FREKIdentity est distincte de :
- frek_identities (moments signes) : les MOMENTS sont des artefacts.
- fk_objects (.fk) : les OBJETS sont des conteneurs culturels.
FREKIdentity represente la PERSONNE ou l'ENTITE qui les possede.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


IDENTITY_TYPES = ["individual", "professional", "institution"]
# "revoked" was already reserved here before any route set it (P1 backlog:
# revoke/update/archive, see docs/architecture/FREK_ID_RECONCILIATION.md).
# "archived" added alongside it, same reservation-then-implementation pattern.
IDENTITY_STATUS = ["anonymous", "protected", "revoked", "archived"]


class Credential(BaseModel):
    """Un authenticator WebAuthn (Passkey) attache a une FREKIdentity."""
    credential_id: str  # base64url de rawId
    public_key: str  # base64url de la cle publique COSE
    sign_count: int = 0
    aaguid: Optional[str] = None
    transports: List[str] = Field(default_factory=list)  # ["internal", "hybrid", "usb", ...]
    label: Optional[str] = None  # "iPhone d'Alice", "Yubikey", etc.
    created_at: str
    last_used_at: Optional[str] = None


class Permission(BaseModel):
    """Extensible pour futur multi-tenant / role-based."""
    scope: str  # ex: "read:own_fk", "write:organization:*"
    granted_at: str
    granted_by: Optional[str] = None


class FREKIdentity(BaseModel):
    frek_id: str  # id-{12hex}-{4hex}
    identity_type: Literal["individual", "professional", "institution"] = "individual"
    display_name: Optional[str] = None
    created_at: str
    status: Literal["anonymous", "protected", "revoked", "archived"] = "anonymous"
    credentials: List[Credential] = Field(default_factory=list)
    linked_objects: List[str] = Field(default_factory=list)  # FK ids + moment frek_ids
    linked_sessions: List[str] = Field(default_factory=list)  # session_ids de moments
    permissions: List[Permission] = Field(default_factory=list)
    # Extensible metadata (pour orga / institution plus tard)
    metadata: dict = Field(default_factory=dict)


class InitIdentityRequest(BaseModel):
    session_id: Optional[str] = None  # attache les moments existants
    display_name: Optional[str] = None
    identity_type: Literal["individual", "professional", "institution"] = "individual"


class RegisterBeginRequest(BaseModel):
    label: Optional[str] = None  # nom donne a la passkey (ex: "iPhone perso")


class RegisterCompleteRequest(BaseModel):
    credential: dict  # PublicKeyCredential JSON serializable
    label: Optional[str] = None


class AuthBeginRequest(BaseModel):
    """Auth username-less : on ne fournit rien, WebAuthn revele le credential_id."""
    pass


class AuthCompleteRequest(BaseModel):
    credential: dict  # AuthenticationCredential JSON


class RevokeIdentityRequest(BaseModel):
    reason: Optional[str] = None


class UpdateIdentityRequest(BaseModel):
    """Only these two fields are mutable post-creation. `identity_type` is
    deliberately not updatable here — changing it after credentials/objects
    are attached is a bigger semantic question than this endpoint answers,
    left out rather than guessed at."""
    display_name: Optional[str] = None
    metadata: Optional[dict] = None


class ArchiveIdentityRequest(BaseModel):
    reason: Optional[str] = None


class IdentityPublicResponse(BaseModel):
    """Vue publique safe d'une identite (jamais de credentials en clair)."""
    frek_id: str
    identity_type: str
    display_name: Optional[str]
    status: str
    created_at: str
    credentials_count: int
    linked_objects_count: int
    protected: bool
