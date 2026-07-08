"""
FREKCORE — Fenetre d'acces #1 : "Signer le moment present"

Endpoint public, anonyme, sans auth. Un tap dans le navigateur cree :
- un FREK-ID silencieux (client_id = "public-window-1")
- un block FREK-Chain notarise (identity_emit)
- un passport Ed25519 signe

C'est la porte grand public de l'infrastructure. Le cœur reste intact.

Doctrine :
- Aucun email requis. Identifiant anonyme geree cote navigateur.
- Aucune donnee sensible collectee par defaut (timestamp + user_agent hash + IP-derived rate limit key).
- Options opt-in : geo (H3), audio (hash), titre libre.
- Rate limit par IP : 20 signatures / heure / IP pour eviter abus.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("frek.moment")

moment_router = APIRouter(prefix="/moment", tags=["FREK Moment (Public Window)"])

db = None
PUBLIC_CLIENT_ID = "public-window-1"


def set_db(database):
    global db
    db = database


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ip_hash(request: Request) -> str:
    """Hash de l'IP + jour, pour rate limit sans stocker d'IP."""
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return hashlib.sha256(f"{ip}|{day}".encode()).hexdigest()[:32]


class SignMomentRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Titre libre (optionnel)")
    context: Optional[str] = Field(None, max_length=1000, description="Contexte / description (optionnel)")
    geo: Optional[Dict[str, Any]] = Field(None, description="H3 + Plus Code si autorise")
    audio_fingerprint: Optional[str] = Field(None, max_length=128, description="Hash SHA-256 audio ambiant (optionnel)")
    image_fingerprint: Optional[str] = Field(None, max_length=128, description="Hash SHA-256 image (optionnel)")
    witnesses: Optional[list] = Field(default_factory=list, description="Autres FREK-IDs qui co-signent")
    session_id: Optional[str] = Field(None, max_length=64, description="ID de session anonyme cote client")


class SignMomentResponse(BaseModel):
    frek_id: str
    stage: str
    created_at: str
    block_hash: Optional[str] = None
    proof_url: str
    passport_url: str
    verify_url: str
    layers_captured: list


async def _check_rate_limit(ip_key: str) -> bool:
    """20 signatures / heure / IP."""
    hour_ago = (datetime.now(timezone.utc).timestamp() - 3600)
    count = await db.moment_rate_limits.count_documents({
        "ip_key": ip_key,
        "created_at_ts": {"$gte": hour_ago},
    })
    return count < 20


async def _record_rate_limit(ip_key: str):
    await db.moment_rate_limits.insert_one({
        "ip_key": ip_key,
        "created_at_ts": datetime.now(timezone.utc).timestamp(),
    })


def _generate_frek_id() -> str:
    """UUID4 short-form (12 hex chars, format lisible)."""
    return f"m-{secrets.token_hex(6)}-{secrets.token_hex(4)}"


@moment_router.post("/sign", response_model=SignMomentResponse)
async def sign_moment(request: SignMomentRequest, http_request: Request):
    """Signe le moment present. Public, anonyme, un tap.

    Cree :
    - FREK-ID stage GENESIS
    - Block FREK-Chain notarise (identity_emit + moment_signed)
    - Passport Ed25519 recuperable

    Anti-abus : rate limit 20/h/IP.
    """
    ip_key = _ip_hash(http_request)
    if not await _check_rate_limit(ip_key):
        raise HTTPException(429, "Trop de signatures depuis ton IP dans la derniere heure. Reessaye plus tard.")

    frek_id = _generate_frek_id()
    now = _now_iso()

    # Determiner les couches capturees
    layers = ["timestamp"]
    if request.geo:
        layers.append("geo")
    if request.audio_fingerprint:
        layers.append("audio")
    if request.image_fingerprint:
        layers.append("image")
    if request.title or request.context:
        layers.append("context")
    if request.witnesses:
        layers.append("witnesses")

    # Session anonyme (permet a l'utilisateur de retrouver ses moments cote client)
    session_id = request.session_id or secrets.token_urlsafe(16)

    identity = {
        "frek_id": frek_id,
        "email_hash": None,  # Anonyme par defaut
        "client_id": PUBLIC_CLIENT_ID,
        "source": "public_window",
        "event": None,
        "current_stage": "GENESIS",
        "stages_completed": ["GENESIS"],
        "active": True,  # Auto-active pour la fenetre publique
        "qr_token": secrets.token_urlsafe(12),
        "created_at": now,
        "activated_at": now,
        "revoked": False,
        "expires_at": None,
        "metadata": {
            "title": request.title,
            "context": request.context,
            "geo": request.geo,
            "audio_fingerprint": request.audio_fingerprint,
            "image_fingerprint": request.image_fingerprint,
            "witnesses": request.witnesses or [],
            "session_id": session_id,
            "layers_captured": layers,
            "ip_key": ip_key[:16],  # Prefixe seulement, pour audit anti-abus
        },
    }

    await db.frek_identities.insert_one(identity)

    # Stage GENESIS trace
    fingerprint_material = "|".join([
        frek_id,
        now,
        request.audio_fingerprint or "",
        request.image_fingerprint or "",
        str(request.geo) if request.geo else "",
    ])
    fingerprint = hashlib.sha256(fingerprint_material.encode()).hexdigest()

    await db.frek_stages.insert_one({
        "frek_id": frek_id,
        "stage": "GENESIS",
        "fingerprint": fingerprint,
        "metadata_hash": None,
        "timestamp": now,
        "source": "public_window",
        "sequence": 1,
        "client_id": PUBLIC_CLIENT_ID,
    })

    # Notarisation
    from notary.service import notarize_event
    block = await notarize_event(
        payload_type="moment_signed",
        payload_id=frek_id,
        payload_data={
            "frek_id": frek_id,
            "created_at": now,
            "layers": layers,
            "geo": request.geo,
            "audio_fingerprint": request.audio_fingerprint,
            "image_fingerprint": request.image_fingerprint,
            "title_hash": hashlib.sha256((request.title or "").encode()).hexdigest() if request.title else None,
        },
        metadata={"client_id": PUBLIC_CLIENT_ID, "public_window": True},
        event_id=None,
    )

    await _record_rate_limit(ip_key)

    block_hash = block.get("block_hash") if isinstance(block, dict) else None

    logger.info(f"Moment signed: frek_id={frek_id} layers={layers} block={block_hash[:12] if block_hash else 'pending'}")

    return SignMomentResponse(
        frek_id=frek_id,
        stage="GENESIS",
        created_at=now,
        block_hash=block_hash,
        proof_url=f"/proof/{block_hash}" if block_hash else "",
        passport_url=f"/api/v1/passport/{frek_id}",
        verify_url=f"/verify/{frek_id}",
        layers_captured=layers,
    )


@moment_router.get("/mine")
async def get_my_moments(session_id: str, limit: int = 50):
    """Liste des moments d'une session anonyme (cote client).
    Le session_id est genere cote navigateur et stocke en localStorage.
    """
    if limit > 200:
        limit = 200

    identities = await db.frek_identities.find(
        {
            "client_id": PUBLIC_CLIENT_ID,
            "metadata.session_id": session_id,
        },
        {"_id": 0, "email_hash": 0, "metadata.ip_key": 0},
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return {
        "session_id": session_id,
        "count": len(identities),
        "moments": identities,
    }


@moment_router.get("/stats")
async def get_public_window_stats():
    """Stats publiques : combien de moments ont ete signes via la fenetre grand public."""
    total = await db.frek_identities.count_documents({"client_id": PUBLIC_CLIENT_ID})
    last24h_cutoff = (datetime.now(timezone.utc).timestamp() - 86400)
    last24h = await db.frek_identities.count_documents({
        "client_id": PUBLIC_CLIENT_ID,
        "created_at": {"$gte": datetime.fromtimestamp(last24h_cutoff, tz=timezone.utc).isoformat()},
    })
    return {
        "total_moments_signed": total,
        "last_24h": last24h,
        "public_window": "/moment/sign",
    }
