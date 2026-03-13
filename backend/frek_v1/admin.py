"""
FREK v1 — Endpoints Admin (protege par X-Admin-Key)
"""
import secrets
import logging

from fastapi import APIRouter, HTTPException, Header

from .models import CreateClientRequest, ClientInfoResponse
from .utils import hash_secret, now_iso, get_env

admin_router = APIRouter(prefix="/admin", tags=["FREK v1 Admin"])
logger = logging.getLogger("frek.admin")

db = None


def set_db(database):
    global db
    db = database


async def verify_admin_key(x_admin_key: str = Header(...)):
    """Verifie que la cle admin correspond a SECRET_KEY"""
    if x_admin_key != get_env("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Cle admin invalide")
    return True


@admin_router.get("/clients")
async def list_clients():
    """Liste les clients API (public — sans secret)"""
    clients = await db.frek_clients.find(
        {}, {"_id": 0, "secret_hash": 0}
    ).to_list(100)
    return {"clients": clients}


@admin_router.post("/clients")
async def create_client(
    request: CreateClientRequest,
    x_admin_key: str = Header(...),
):
    if x_admin_key != get_env("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Cle admin invalide")

    existing = await db.frek_clients.find_one(
        {"client_id": request.client_id}, {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Client '{request.client_id}' existe deja")

    client_secret = secrets.token_urlsafe(32)

    client_doc = {
        "client_id": request.client_id,
        "name": request.name,
        "secret_hash": hash_secret(client_secret),
        "permissions": request.permissions,
        "created_at": now_iso(),
    }

    await db.frek_clients.insert_one(client_doc)
    logger.info(f"Nouveau client API cree: {request.client_id}")

    return {
        "client_id": request.client_id,
        "client_secret": client_secret,
        "name": request.name,
        "permissions": request.permissions,
        "message": "Client cree. Conservez le secret — il ne sera plus affiche.",
    }


@admin_router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    x_admin_key: str = Header(...),
):
    if x_admin_key != get_env("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Cle admin invalide")

    result = await db.frek_clients.delete_one({"client_id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' introuvable")

    # Revoke all tokens
    await db.frek_tokens.update_many(
        {"client_id": client_id},
        {"$set": {"revoked": True}}
    )

    logger.info(f"Client API supprime: {client_id}")
    return {"deleted": client_id, "message": "Client et tokens revoques"}


# --- RGPD: Droit a l'oubli ---
@admin_router.delete("/identity/{frek_id}/gdpr")
async def gdpr_delete(
    frek_id: str,
    x_admin_key: str = Header(...),
):
    """
    RGPD — Droit a l'oubli
    Supprime frek_identity + stages.
    Le frek_id devient orphelin, les fingerprints restent pour integrite.
    """
    if x_admin_key != get_env("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Cle admin invalide")

    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id}, {"_id": 0}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    # Supprimer l'identite
    await db.frek_identities.delete_one({"frek_id": frek_id})

    # Supprimer les stages (append-only exception pour RGPD)
    deleted_stages = await db.frek_stages.delete_many({"frek_id": frek_id})

    logger.info(f"RGPD suppression: {frek_id} ({deleted_stages.deleted_count} stages)")

    return {
        "frek_id": frek_id,
        "identity_deleted": True,
        "stages_deleted": deleted_stages.deleted_count,
        "message": "Identite et stages supprimes (RGPD droit a l'oubli)",
    }
