"""FK Routes — endpoints publics pour creer, verifier et retrouver des objets FK.

Endpoints :
- POST /api/v1/fk/create       (multipart : metadonnees + medias) -> .fk binaire + JSON info
- POST /api/v1/fk/verify       (upload .fk) -> rapport de validation offline
- GET  /api/v1/fk/detail/{id}  -> metadata publique safe (comme /moment/detail)
- GET  /api/v1/fk/{id}/download -> re-telecharger un .fk deja emballe (si conserve)
- GET  /api/v1/fk/stats        -> compteur public
- GET  /api/v1/fk/pubkey       -> cle publique FREKCORE pour verification tiers
"""
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

from passport import keys as passport_keys

from .models import FK_VERSION, OBJECT_TYPES
from .packager import create_fk
from .validator import validate_fk, summary

logger = logging.getLogger("frek.fk.routes")

fk_router = APIRouter(prefix="/fk", tags=["FK Cultural Object"])

db = None


def set_db(mongo_db):
    global db
    db = mongo_db


MAX_MEDIA_TOTAL = 100 * 1024 * 1024  # 100 MB total upload par .fk
MAX_MEDIA_ITEMS = 20


# ---------- CREATE ----------

@fk_router.post("/create")
async def create_fk_endpoint(
    title: str = Form(..., description="Titre de l'objet culturel"),
    object_type: str = Form("other", description=f"Type : {', '.join(OBJECT_TYPES)}"),
    primary_creator_name: str = Form(..., description="Nom du createur principal"),
    primary_creator_role: Optional[str] = Form("creator"),
    description: Optional[str] = Form(None),
    context: Optional[str] = Form(None, description="JSON optionnel : location, coordinates, date, institution"),
    contributors: Optional[str] = Form(None, description="JSON optionnel : liste de {name, role}"),
    external_refs: Optional[str] = Form(None, description="JSON optionnel : isni, iswc, doi..."),
    rights_owner_name: Optional[str] = Form(None),
    keep: bool = Form(False, description="Si true, .fk conserve cote serveur (recuperable via /download)"),
    files: List[UploadFile] = File(default_factory=list, description="Medias a inclure"),
    return_json: bool = Form(False, description="Si true, renvoie JSON info + fk_base64 au lieu du binaire"),
):
    """Cree un objet culturel FK signe. Retourne le .fk binaire par defaut."""
    # Validation
    if object_type not in OBJECT_TYPES:
        raise HTTPException(400, f"object_type invalide. Valides : {OBJECT_TYPES}")
    if len(files) > MAX_MEDIA_ITEMS:
        raise HTTPException(400, f"Trop de medias ({len(files)} > {MAX_MEDIA_ITEMS})")

    # Parse JSON optionnels
    def _try_json(s: Optional[str], default):
        if not s:
            return default
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return default

    ctx = _try_json(context, {})
    contribs = _try_json(contributors, [])
    refs = _try_json(external_refs, {})

    # Lecture des medias + verification taille
    media_files = []
    total_bytes = 0
    for f in files:
        data = await f.read()
        total_bytes += len(data)
        if total_bytes > MAX_MEDIA_TOTAL:
            raise HTTPException(400, f"Volume total > {MAX_MEDIA_TOTAL} octets")
        media_files.append((f.filename or "file", data,
                            f.content_type or "application/octet-stream"))

    # Creation FK
    try:
        fk_bytes, fk_obj = await create_fk(
            title=title,
            object_type=object_type,
            primary_creator_name=primary_creator_name,
            primary_creator_role=primary_creator_role,
            contributors=contribs if isinstance(contribs, list) else [],
            description=description,
            context=ctx if isinstance(ctx, dict) else {},
            external_refs=refs if isinstance(refs, dict) else {},
            media_files=media_files,
            rights_owner_name=rights_owner_name,
        )
    except Exception as e:
        logger.exception(f"FK creation failed: {e}")
        raise HTTPException(500, f"Erreur lors de la creation FK: {e}")

    frek_id = fk_obj.manifest.frek_id

    # Persistance metadata en DB (toujours)
    doc = {
        "frek_id": frek_id,
        "fk_version": FK_VERSION,
        "object_type": object_type,
        "title": title,
        "creator_name": primary_creator_name,
        "description": description,
        "created_at": fk_obj.manifest.created_at,
        "block_hash": fk_obj.proof.block.block_hash if fk_obj.proof.block else None,
        "root_hash": fk_obj.proof.root_hash,
        "media_count": len(fk_obj.media.items),
        "size_bytes": len(fk_bytes),
        "kept": bool(keep),
        "storage_path": None,
    }

    # Conservation optionnelle du binaire (Object Storage best effort)
    if keep:
        try:
            from moment import storage as media_storage
            if media_storage.is_available():
                path = f"frekcore/fk/{frek_id}.fk"
                media_storage.put_object(path, fk_bytes, "application/vnd.frek.culture+zip")
                doc["storage_path"] = path
                logger.info(f"FK stored: {frek_id} -> {path}")
        except Exception as e:
            logger.warning(f"FK storage failed for {frek_id}: {e}")

    try:
        await db.fk_objects.insert_one(doc)
    except Exception as e:
        logger.warning(f"FK metadata insert failed: {e}")

    # Reponse
    info = {
        "frek_id": frek_id,
        "fk_version": FK_VERSION,
        "object_type": object_type,
        "title": title,
        "creator": primary_creator_name,
        "created_at": fk_obj.manifest.created_at,
        "media_count": len(fk_obj.media.items),
        "size_bytes": len(fk_bytes),
        "block_hash": doc["block_hash"],
        "root_hash": fk_obj.proof.root_hash,
        "kept": bool(keep and doc.get("storage_path")),
        "detail_url": f"/api/v1/fk/detail/{frek_id}",
        "download_url": f"/api/v1/fk/{frek_id}/download" if doc.get("storage_path") else None,
        "verify_url": f"/verify/fk/{frek_id}",
    }

    if return_json:
        return JSONResponse({
            "info": info,
            "fk_base64": base64.b64encode(fk_bytes).decode("ascii"),
        })

    filename = f"{title.replace(' ', '_')[:40] or 'creation'}.fk"
    return Response(
        content=fk_bytes,
        media_type="application/vnd.frek.culture+zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-FREK-ID": frek_id,
            "X-FK-Info": json.dumps(info, ensure_ascii=False),
        },
    )


# ---------- VERIFY ----------

@fk_router.post("/verify")
async def verify_fk_endpoint(file: UploadFile = File(..., description="Fichier .fk a verifier")):
    """Valide un .fk uploade — verification OFFLINE (aucune DB requise)."""
    data = await file.read()
    if len(data) > MAX_MEDIA_TOTAL * 2:
        raise HTTPException(400, "Fichier trop volumineux")
    report = validate_fk(data)
    report["summary"] = summary(report)
    return report


# ---------- DETAIL ----------

@fk_router.get("/detail/{frek_id}")
async def get_fk_detail(frek_id: str):
    """Metadata publique safe d'un FK (equivalent /moment/detail pour les .fk)."""
    doc = await db.fk_objects.find_one({"frek_id": frek_id}, {"_id": 0, "storage_path": 0})
    if not doc:
        raise HTTPException(404, "FK introuvable")
    return doc


# ---------- DOWNLOAD ----------

@fk_router.get("/{frek_id}/download")
async def download_fk(frek_id: str):
    """Re-telecharge un .fk conserve cote serveur (si keep=true a la creation)."""
    doc = await db.fk_objects.find_one({"frek_id": frek_id}, {"storage_path": 1, "title": 1})
    if not doc:
        raise HTTPException(404, "FK introuvable")
    if not doc.get("storage_path"):
        raise HTTPException(404, "Ce FK n'a pas ete conserve cote serveur")

    from moment import storage as media_storage
    try:
        data, _ = media_storage.get_object(doc["storage_path"])
    except Exception as e:
        logger.error(f"FK download failed for {frek_id}: {e}")
        raise HTTPException(502, "FK indisponible temporairement")

    filename = f"{(doc.get('title') or 'creation').replace(' ', '_')[:40]}.fk"
    return Response(
        content=data,
        media_type="application/vnd.frek.culture+zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------- STATS ----------

@fk_router.get("/stats")
async def fk_stats():
    """Compteur public."""
    if db is None:
        return {"count": 0}
    count = await db.fk_objects.count_documents({})
    return {"fk_version": FK_VERSION, "total_fk": count}


# ---------- PUBKEY ----------

@fk_router.get("/pubkey")
async def fk_pubkey():
    """Cle publique FREKCORE pour verification tiers."""
    return {
        "algo": "ed25519",
        "key_id": "frek-passport-v1",
        "public_key_pem": passport_keys.public_key_pem(),
        "public_key_raw_b64": passport_keys.public_key_raw_b64(),
    }
