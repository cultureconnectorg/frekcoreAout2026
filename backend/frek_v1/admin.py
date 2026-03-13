"""
FREK v1 — Endpoints Admin
"""
import secrets

from fastapi import APIRouter, HTTPException

from .models import CreateClientRequest, ClientInfoResponse
from .utils import hash_secret, now_iso

admin_router = APIRouter(prefix="/admin", tags=["FREK v1 Admin"])

db = None


def set_db(database):
    global db
    db = database


@admin_router.get("/clients")
async def list_clients():
    clients = await db.frek_clients.find(
        {}, {"_id": 0, "secret_hash": 0}
    ).to_list(100)
    return {"clients": clients}


@admin_router.post("/clients")
async def create_client(request: CreateClientRequest):
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

    return {
        "client_id": request.client_id,
        "client_secret": client_secret,
        "name": request.name,
        "permissions": request.permissions,
        "message": "Client cree. Conservez le secret — il ne sera plus affiche.",
    }
