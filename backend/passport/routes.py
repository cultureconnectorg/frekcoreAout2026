"""FREK Passport — endpoints HTTP.

Tous les endpoints sont publics (la passeport est destine au porteur ; la verification
ne necessite que la cle publique). Aucun secret n'est expose.

Endpoints :
    GET  /api/v1/passport/key                Cle publique Ed25519 (PEM + raw b64)
    GET  /api/v1/passport/{frek_id}          Passeport complet signe (full)
    POST /api/v1/passport/disclose           Disclosure selective (porteur)
    POST /api/v1/passport/verify             Verification utilitaire serveur
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
from pydantic import BaseModel, Field

from . import keys, service

logger = logging.getLogger("frek.passport.routes")

passport_router = APIRouter(prefix="/passport", tags=["FREK Passport — Souverainete porteur"])

db = None


def set_db(database):
    global db
    db = database
    service.set_db(database)


@passport_router.get("/key")
async def get_public_key():
    return {
        "key_id": keys.KEY_ID,
        "algorithm": "Ed25519",
        "public_key_pem": keys.public_key_pem(),
        "public_key_raw_b64": keys.public_key_raw_b64(),
    }


@passport_router.get("/{frek_id}")
async def export_passport(frek_id: str):
    """Retourne un passeport complet signe pour le frek_id donne.

    Rate-limit-friendly : pas de cout de calcul significatif (1 lookup + 1 hash).
    Chaque appel produit un nouveau passeport (nonces frais, signature differente, meme contenu).
    """
    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")
    return await service.build_passport(identity)


class DiscloseRequest(BaseModel):
    passport: dict = Field(..., description="Passeport complet (output de GET /passport/{frek_id})")
    reveal: list[str] = Field(..., description="Liste des cles claims a reveler", min_length=1)


@passport_router.post("/disclose")
async def disclose_passport(request: DiscloseRequest):
    """Genere un sous-passeport ne revelant que les claims demandes.

    Calcul cote client possible — l'endpoint est fourni par commodite.
    """
    try:
        return service.disclose(request.passport, request.reveal)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class VerifyRequest(BaseModel):
    document: dict = Field(..., description="Passeport (full) ou disclosure (partial)")


@passport_router.post("/verify")
async def verify_passport(request: VerifyRequest):
    """Verification utilitaire serveur. La meme logique tourne offline avec la cle publique."""
    return service.verify(request.document)


VERIFIER_DIR = Path(__file__).resolve().parent.parent.parent / "verifier"


@passport_router.get("/verifier/{lang}")
async def download_verifier(lang: str):
    """Telechargement du verifier offline standalone (Python ou JS).

    `lang` : python | js | js-demo | readme
    Le verifier ne necessite aucune dependance reseau a FREKCORE pour fonctionner.
    """
    targets = {
        "python": (VERIFIER_DIR / "python" / "verify_passport.py", "text/x-python"),
        "js": (VERIFIER_DIR / "js" / "verify_passport.js", "application/javascript"),
        "js-demo": (VERIFIER_DIR / "js" / "demo.html", "text/html"),
        "readme": (VERIFIER_DIR / "README.md", "text/markdown"),
    }
    if lang not in targets:
        raise HTTPException(
            status_code=404,
            detail=f"lang inconnue. Choix : {sorted(targets.keys())}",
        )
    path, mime = targets[lang]
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"verifier file introuvable : {path}")
    return FileResponse(str(path), media_type=mime, filename=path.name)
