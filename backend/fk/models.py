"""FK — Modeles Pydantic pour les 7 couches du Cultural Object Container.

Ces modeles definissent la structure canonique d'un .fk v0.1 :
- manifest.fk.json (racine)
- metadata/identity.json
- metadata/creators.json
- metadata/timeline.json
- media/media.json (manifeste des fichiers presents)
- intelligence/intelligence.json (reserve pour FREKANSLA — vide en v0.1)
- rights/ownership.json (optionnel)
- proof/frekcore-attestation.json (signature Ed25519)
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


FK_VERSION = "0.1"
OBJECT_TYPES = [
    "song", "album", "event", "heritage",
    "photo", "captation", "document", "artwork", "other",
]


# ---------- IDENTITE ----------

class Context(BaseModel):
    location: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None  # {lat, lon}
    date: Optional[str] = None  # ISO 8601
    institution: Optional[str] = None


class IdentityLayer(BaseModel):
    frek_id: str
    title: str
    object_type: str = "other"
    description: Optional[str] = None
    context: Context = Field(default_factory=Context)
    external_refs: Dict[str, Optional[str]] = Field(default_factory=dict)  # isni, iswc, doi, wikidata...


# ---------- CREATEURS ----------

class Contributor(BaseModel):
    name: str
    role: Optional[str] = None
    isni: Optional[str] = None


class CreatorsLayer(BaseModel):
    primary_creator: Contributor
    contributors: List[Contributor] = Field(default_factory=list)


# ---------- TIMELINE / HISTOIRE ----------

class Version(BaseModel):
    version: str = "1.0"
    created_at: str  # ISO 8601
    note: Optional[str] = None
    based_on: Optional[str] = None
    hash: Optional[str] = None  # SHA-256 du .fk a ce moment
    frek_block: Optional[str] = None  # block_hash FREK-Chain


class TimelineLayer(BaseModel):
    created_at: str
    description: Optional[str] = None
    versions: List[Version] = Field(default_factory=list)


# ---------- MEDIA ----------

class MediaItem(BaseModel):
    path: str  # Chemin dans le ZIP, ex: "media/audio/song.wav"
    content_type: str
    size: int
    sha256: str
    kind: str  # "audio" | "video" | "image" | "document" | "data"
    original_name: Optional[str] = None


class MediaLayer(BaseModel):
    items: List[MediaItem] = Field(default_factory=list)


# ---------- INTELLIGENCE (reserve v0.1) ----------

class IntelligenceLayer(BaseModel):
    """Reservee pour FREKANSLA. Vide en v0.1 — structure figee des maintenant."""
    fingerprints: Optional[Dict[str, Any]] = None  # chromaprint, audiotag, etc.
    analysis: Optional[Dict[str, Any]] = None  # bpm, key, spectral, structure
    signatures: Optional[Dict[str, Any]] = None  # patterns creatifs
    note: str = "Reserved for FREKANSLA integration"


# ---------- DROITS ----------

class RightsLayer(BaseModel):
    owner: Optional[Contributor] = None
    co_owners: List[Dict[str, Any]] = Field(default_factory=list)
    licenses: List[Dict[str, Any]] = Field(default_factory=list)
    transfers: List[Dict[str, Any]] = Field(default_factory=list)


# ---------- PREUVE ----------

class BlockRef(BaseModel):
    block_hash: str
    height: Optional[int] = None
    created_at: Optional[str] = None


class BtcAnchor(BaseModel):
    enabled: bool = False
    ots_file: Optional[str] = None
    confirmed_at: Optional[str] = None


class ProofLayer(BaseModel):
    frek_id: str
    issued_at: str
    issuer: str = "frekcore-notary-v1"
    signature_algo: str = "ed25519"
    public_key_pem: str
    public_key_raw_b64: str
    signature: str  # base64 de sign(root_hash)
    layer_hashes: Dict[str, str]  # sha256 de chaque layer canonicalisee
    root_hash: str  # sha256 des layer_hashes canonicalisees
    block: Optional[BlockRef] = None
    btc_anchor: BtcAnchor = Field(default_factory=BtcAnchor)


# ---------- MANIFEST RACINE ----------

class LayersMap(BaseModel):
    identity: str = "metadata/identity.json"
    creators: str = "metadata/creators.json"
    timeline: str = "metadata/timeline.json"
    media: str = "media/media.json"
    intelligence: str = "intelligence/intelligence.json"
    rights: str = "rights/ownership.json"
    proof: str = "proof/frekcore-attestation.json"


class AttestationRef(BaseModel):
    block_hash: Optional[str] = None
    signature_algo: str = "ed25519"
    key_id: str = "frek-passport-v1"


class ManifestFK(BaseModel):
    fk_version: str = FK_VERSION
    frek_id: str
    object_type: str
    created_at: str
    layers: LayersMap = Field(default_factory=LayersMap)
    attestation_ref: AttestationRef = Field(default_factory=AttestationRef)


# ---------- FK OBJECT COMPLET (in-memory) ----------

class FKObject(BaseModel):
    """Representation complete en memoire d'un .fk avant serialisation ZIP."""
    manifest: ManifestFK
    identity: IdentityLayer
    creators: CreatorsLayer
    timeline: TimelineLayer
    media: MediaLayer
    intelligence: IntelligenceLayer = Field(default_factory=IntelligenceLayer)
    rights: RightsLayer = Field(default_factory=RightsLayer)
    proof: ProofLayer
