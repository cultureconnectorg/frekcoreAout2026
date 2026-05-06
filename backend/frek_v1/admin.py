"""
FREK v1 — Endpoints Admin (protege par X-Admin-Key)
"""
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Header

from .models import CreateClientRequest, UpdateClientRequest, ClientInfoResponse
from .utils import hash_secret, now_iso, get_env

admin_router = APIRouter(prefix="/admin", tags=["FREK v1 Admin"])
logger = logging.getLogger("frek.admin")

db = None


def set_db(database):
    global db
    db = database


async def verify_admin_key(x_admin_key: str = Header(..., description="Cle admin (env SECRET_KEY)")):
    """Verifie que la cle admin correspond a SECRET_KEY"""
    if x_admin_key != get_env("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Cle admin invalide")
    return True


@admin_router.get("/clients")
async def list_clients(active_only: bool = False):
    """Liste les clients API (public — sans secret). active_only=true filtre les desactives."""
    query = {}
    if active_only:
        query = {"$or": [{"active": True}, {"active": {"$exists": False}}]}
    clients = await db.frek_clients.find(query, {"_id": 0, "secret_hash": 0}).to_list(500)
    # Default active=true pour clients legacy
    for c in clients:
        c.setdefault("active", True)
    return {"count": len(clients), "clients": clients}


@admin_router.post("/clients")
async def create_client(
    request: CreateClientRequest,
    _: bool = Depends(verify_admin_key),
):
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
        "event": request.event,
        "active": True,
        "created_at": now_iso(),
        "last_used_at": None,
        "rotated_at": None,
    }

    await db.frek_clients.insert_one(client_doc)
    logger.info(f"Nouveau client API cree: {request.client_id} (event: {request.event})")

    return {
        "client_id": request.client_id,
        "client_secret": client_secret,
        "name": request.name,
        "permissions": request.permissions,
        "event": request.event,
        "active": True,
        "created_at": client_doc["created_at"],
        "message": "Client cree. Conservez le secret — il ne sera plus affiche.",
    }


@admin_router.post("/clients/{client_id}/rotate")
async def rotate_client_secret(
    client_id: str,
    _: bool = Depends(verify_admin_key),
):
    """Genere un nouveau client_secret. L'ancien est invalide immediatement.
    Tous les tokens en cours sont aussi revoques."""
    existing = await db.frek_clients.find_one({"client_id": client_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' introuvable")

    new_secret = secrets.token_urlsafe(32)
    now = now_iso()
    await db.frek_clients.update_one(
        {"client_id": client_id},
        {"$set": {"secret_hash": hash_secret(new_secret), "rotated_at": now}},
    )
    # Revoke active tokens
    await db.frek_tokens.update_many(
        {"client_id": client_id},
        {"$set": {"revoked": True}},
    )

    logger.info(f"Client API rotated secret: {client_id}")
    return {
        "client_id": client_id,
        "client_secret": new_secret,
        "rotated_at": now,
        "message": "Secret rote. Tokens existants revoques. Mettez a jour vos integrations.",
    }


@admin_router.patch("/clients/{client_id}")
async def update_client(
    client_id: str,
    request: UpdateClientRequest,
    _: bool = Depends(verify_admin_key),
):
    """Met a jour name/permissions/active/event d'un client (sans toucher au secret)."""
    existing = await db.frek_clients.find_one({"client_id": client_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' introuvable")

    update = {}
    if request.name is not None:
        update["name"] = request.name
    if request.permissions is not None:
        update["permissions"] = request.permissions
    if request.active is not None:
        update["active"] = request.active
    if request.event is not None:
        update["event"] = request.event
    if not update:
        raise HTTPException(status_code=400, detail="Aucun champ a mettre a jour")

    await db.frek_clients.update_one({"client_id": client_id}, {"$set": update})
    if update.get("active") is False:
        await db.frek_tokens.update_many(
            {"client_id": client_id},
            {"$set": {"revoked": True}},
        )
    logger.info(f"Client {client_id} mis a jour: {list(update.keys())}")
    return {"client_id": client_id, "updated": update}


@admin_router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    _: bool = Depends(verify_admin_key),
):
    """Desactivation soft (active=false) + revocation tokens. Garde la trace du client."""
    existing = await db.frek_clients.find_one({"client_id": client_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' introuvable")
    await db.frek_clients.update_one(
        {"client_id": client_id},
        {"$set": {"active": False, "deleted_at": now_iso()}},
    )
    await db.frek_tokens.update_many(
        {"client_id": client_id},
        {"$set": {"revoked": True}}
    )
    logger.info(f"Client API desactive: {client_id}")
    return {"client_id": client_id, "deactivated": True, "message": "Client desactive et tokens revoques"}


# --- RGPD: Droit a l'oubli ---
@admin_router.delete("/identity/{frek_id}/gdpr")
async def gdpr_delete(
    frek_id: str,
    _: bool = Depends(verify_admin_key),
):
    """
    RGPD — Droit a l'oubli
    Supprime frek_identity + stages.
    Le frek_id devient orphelin, les fingerprints restent pour integrite.
    """
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id}, {"_id": 0}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    await db.frek_identities.delete_one({"frek_id": frek_id})
    deleted_stages = await db.frek_stages.delete_many({"frek_id": frek_id})

    logger.info(f"RGPD suppression: {frek_id} ({deleted_stages.deleted_count} stages)")
    return {
        "frek_id": frek_id,
        "identity_deleted": True,
        "stages_deleted": deleted_stages.deleted_count,
        "message": "Identite et stages supprimes (RGPD droit a l'oubli)",
    }
