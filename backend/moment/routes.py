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
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import storage as media_storage

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
    media_hash: Optional[str] = None
    media_kind: Optional[str] = None  # "image" | "audio" | None
    media_stored: bool = False
    media_url: Optional[str] = None


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


async def _sign_moment_core(
    *,
    title: Optional[str],
    context: Optional[str],
    geo: Optional[Dict[str, Any]],
    audio_fingerprint: Optional[str],
    image_fingerprint: Optional[str],
    witnesses: Optional[list],
    session_id: Optional[str],
    http_request: Request,
    media: Optional[Dict[str, Any]] = None,
    identity_frek_id: Optional[str] = None,
) -> "SignMomentResponse":
    """Logique commune de signature partagee entre /sign (JSON) et /sign-media (multipart).

    `media` (optionnel) = {"hash": sha256, "kind": "image|audio", "content_type": str,
    "size": int, "stored": bool, "storage_path": Optional[str], "ext": str}
    """
    ip_key = _ip_hash(http_request)
    if not await _check_rate_limit(ip_key):
        raise HTTPException(429, "Trop de signatures depuis ton IP dans la derniere heure. Reessaye plus tard.")

    frek_id = _generate_frek_id()
    now = _now_iso()

    # Determiner les couches capturees
    layers = ["timestamp"]
    if geo:
        layers.append("geo")
    if audio_fingerprint or (media and media.get("kind") == "audio"):
        layers.append("audio")
    if image_fingerprint or (media and media.get("kind") == "image"):
        layers.append("image")
    if title or context:
        layers.append("context")
    if witnesses:
        layers.append("witnesses")
    if media and media.get("stored"):
        layers.append("media_kept")

    session_id = session_id or secrets.token_urlsafe(16)

    identity = {
        "frek_id": frek_id,
        "email_hash": None,
        "client_id": PUBLIC_CLIENT_ID,
        "source": "public_window",
        "event": None,
        "current_stage": "GENESIS",
        "stages_completed": ["GENESIS"],
        "active": True,
        "qr_token": secrets.token_urlsafe(12),
        "created_at": now,
        "activated_at": now,
        "revoked": False,
        "expires_at": None,
        "metadata": {
            "title": title,
            "context": context,
            "geo": geo,
            "audio_fingerprint": audio_fingerprint,
            "image_fingerprint": image_fingerprint,
            "witnesses": witnesses or [],
            "session_id": session_id,
            "layers_captured": layers,
            "ip_key": ip_key[:16],
            "media": media,  # None si aucun fichier
        },
    }

    await db.frek_identities.insert_one(identity)

    fingerprint_material = "|".join([
        frek_id,
        now,
        audio_fingerprint or "",
        image_fingerprint or "",
        (media or {}).get("hash", ""),
        str(geo) if geo else "",
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
            "geo": geo,
            "audio_fingerprint": audio_fingerprint,
            "image_fingerprint": image_fingerprint,
            "media_hash": (media or {}).get("hash"),
            "media_kind": (media or {}).get("kind"),
            "title_hash": hashlib.sha256((title or "").encode()).hexdigest() if title else None,
        },
        metadata={"client_id": PUBLIC_CLIENT_ID, "public_window": True},
        event_id=None,
    )

    await _record_rate_limit(ip_key)

    # Auto-link a une FREK Identity si un session token identity valide est fourni
    if identity_frek_id:
        try:
            await db.frek_persons.update_one(
                {"frek_id": identity_frek_id},
                {"$addToSet": {"linked_objects": frek_id}},
            )
        except Exception as e:
            logger.warning(f"identity auto-link failed for {frek_id}: {e}")

    block_hash = block.get("block_hash") if isinstance(block, dict) else None

    logger.info(
        f"Moment signed: frek_id={frek_id} layers={layers} "
        f"media={(media or {}).get('kind') or 'none'} "
        f"block={block_hash[:12] if block_hash else 'pending'}"
    )

    return SignMomentResponse(
        frek_id=frek_id,
        stage="GENESIS",
        created_at=now,
        block_hash=block_hash,
        proof_url=f"/proof/{block_hash}" if block_hash else "",
        passport_url=f"/api/v1/passport/{frek_id}",
        verify_url=f"/verify/{frek_id}",
        layers_captured=layers,
        media_hash=(media or {}).get("hash"),
        media_kind=(media or {}).get("kind"),
        media_stored=bool((media or {}).get("stored")),
        media_url=f"/api/v1/moment/media/{frek_id}" if (media or {}).get("stored") else None,
    )


@moment_router.post("/sign", response_model=SignMomentResponse)
async def sign_moment(request: SignMomentRequest, http_request: Request,
                     x_frek_session: Optional[str] = Header(None)):
    """Signe le moment present (JSON pur, sans media binaire). Public, anonyme.

    Si un header X-FREK-Session valide est fourni, le moment est automatiquement
    lie a la FREK Identity correspondante.
    """
    from identity_engine import service as _idsvc
    identity_frek_id = _idsvc.verify_session_token(x_frek_session) if x_frek_session else None
    return await _sign_moment_core(
        title=request.title,
        context=request.context,
        geo=request.geo,
        audio_fingerprint=request.audio_fingerprint,
        image_fingerprint=request.image_fingerprint,
        witnesses=request.witnesses,
        session_id=request.session_id,
        http_request=http_request,
        media=None,
        identity_frek_id=identity_frek_id,
    )


@moment_router.post("/sign-media", response_model=SignMomentResponse)
async def sign_moment_with_media(
    http_request: Request,
    file: UploadFile = File(..., description="Photo ou audio a signer"),
    store: bool = Form(False, description="Conserver le binaire (True) ou hash seul (False)"),
    title: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    geo: Optional[str] = Form(None, description="JSON geo optionnel"),
    session_id: Optional[str] = Form(None),
    x_frek_session: Optional[str] = Header(None),
):
    """Signe un moment avec un fichier joint (photo ou audio).

    - `store=False` : hash SHA-256 seul, aucun binaire conserve (pur notaire).
    - `store=True`  : hash + fichier chiffre-au-transit conserve, recuperable via /moment/media/{frek_id}.

    Le binaire peut disparaitre plus tard sans casser la preuve (le hash reste ancre).
    """
    # Lecture + validation
    data = await file.read()
    size = len(data)
    content_type = file.content_type or "application/octet-stream"

    ok, reason = media_storage.validate_media(content_type, size)
    if not ok:
        raise HTTPException(400, reason)

    media_hash = media_storage.sha256_bytes(data)
    kind = media_storage.media_kind(content_type)
    ext = media_storage.extension_for(content_type)

    # Geo parse
    geo_obj: Optional[Dict[str, Any]] = None
    if geo:
        try:
            geo_obj = json.loads(geo)
            if not isinstance(geo_obj, dict):
                geo_obj = None
        except json.JSONDecodeError:
            geo_obj = None

    media_payload = {
        "hash": media_hash,
        "kind": kind,
        "content_type": content_type,
        "size": size,
        "ext": ext,
        "stored": False,
        "storage_path": None,
    }

    # On genere le frek_id AVANT l'upload pour l'utiliser dans le path
    # Mais _sign_moment_core genere son propre frek_id. On appelle donc d'abord
    # le core, puis on upload avec le frek_id retourne, puis on met a jour la DB.
    from identity_engine import service as _idsvc
    identity_frek_id = _idsvc.verify_session_token(x_frek_session) if x_frek_session else None
    result = await _sign_moment_core(
        title=title,
        context=context,
        geo=geo_obj,
        audio_fingerprint=media_hash if kind == "audio" else None,
        image_fingerprint=media_hash if kind == "image" else None,
        witnesses=None,
        session_id=session_id,
        http_request=http_request,
        media=media_payload,
        identity_frek_id=identity_frek_id,
    )

    # Si l'utilisateur a demande le stockage, upload maintenant
    if store:
        if not media_storage.is_available():
            logger.warning(f"Stockage demande mais indisponible pour {result.frek_id}")
            # On retourne quand meme le succes de la signature — le hash est ancre
        else:
            try:
                path = media_storage.build_path(result.frek_id, ext)
                media_storage.put_object(path, data, content_type)
                # Update DB avec le storage_path
                await db.frek_identities.update_one(
                    {"frek_id": result.frek_id},
                    {"$set": {
                        "metadata.media.stored": True,
                        "metadata.media.storage_path": path,
                    }},
                )
                result.media_stored = True
                result.media_url = f"/api/v1/moment/media/{result.frek_id}"
                if "media_kept" not in result.layers_captured:
                    result.layers_captured.append("media_kept")
                logger.info(f"Media stored for {result.frek_id}: {path}")
            except Exception as e:
                logger.error(f"Media upload failed for {result.frek_id}: {e}")
                # Signature deja creee — on retourne quand meme

    return result


@moment_router.get("/media/{frek_id}")
async def get_moment_media(frek_id: str):
    """Recupere le binaire d'un moment (si l'utilisateur a choisi de le conserver).

    Route publique : anonyme, comme la signature. Le FREK-ID est le seul secret.
    """
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": PUBLIC_CLIENT_ID},
        {"metadata.media": 1},
    )
    if not identity:
        raise HTTPException(404, "Moment introuvable")

    media = (identity.get("metadata") or {}).get("media") or {}
    if not media.get("stored") or not media.get("storage_path"):
        raise HTTPException(404, "Aucun media conserve pour ce moment")

    try:
        data, content_type = media_storage.get_object(media["storage_path"])
    except Exception as e:
        logger.error(f"Media fetch failed for {frek_id}: {e}")
        raise HTTPException(502, "Media indisponible temporairement")

    return Response(
        content=data,
        media_type=media.get("content_type") or content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@moment_router.get("/detail/{frek_id}")
async def get_moment_detail(frek_id: str):
    """Details publics d'un moment signe (metadata safe pour affichage /verify).

    Retourne uniquement les infos publiques : titre, media_hash, media_url,
    couches capturees, timestamp, block_hash. Aucune donnee sensible.
    """
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": PUBLIC_CLIENT_ID},
        {"_id": 0, "email_hash": 0, "qr_token": 0, "metadata.ip_key": 0, "metadata.session_id": 0},
    )
    if not identity:
        raise HTTPException(404, "Moment introuvable")

    meta = identity.get("metadata") or {}
    media = meta.get("media") or {}

    # Block hash (dernier block ou notarisation liee)
    block = await db.notary_blocks.find_one(
        {"payload_id": frek_id, "payload_type": "moment_signed"},
        {"_id": 0, "block_hash": 1, "height": 1, "created_at": 1, "btc_anchored": 1},
        sort=[("height", -1)],
    )

    return {
        "frek_id": frek_id,
        "created_at": identity.get("created_at"),
        "stage": identity.get("current_stage"),
        "title": meta.get("title"),
        "layers_captured": meta.get("layers_captured") or [],
        "geo": meta.get("geo"),
        "media": {
            "hash": media.get("hash"),
            "kind": media.get("kind"),
            "content_type": media.get("content_type"),
            "size": media.get("size"),
            "stored": bool(media.get("stored")),
            "url": f"/api/v1/moment/media/{frek_id}" if media.get("stored") else None,
        } if media else None,
        "block": block or None,
        "verify_url": f"/verify/{frek_id}",
    }


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
    from fastapi.responses import JSONResponse
    return JSONResponse(
        {
            "total_moments_signed": total,
            "last_24h": last24h,
            "public_window": "/moment/sign",
        },
        headers={"Cache-Control": "public, max-age=30"},
    )
