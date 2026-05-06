"""
FREK v1 — Authentification Client Credentials
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from .models import TokenRequest, TokenResponse
from .utils import hash_secret, create_access_token, verify_access_token, now_iso


auth_router = APIRouter(prefix="/auth", tags=["FREK v1 Auth"])

# Reference to db set from server.py
db = None


def set_db(database):
    global db
    db = database


async def get_current_client(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant ou invalide")
    token = authorization.split(" ", 1)[1]
    try:
        payload = verify_access_token(token)
        client_id = payload["sub"]
        client = await db.frek_clients.find_one(
            {"client_id": client_id}, {"_id": 0}
        )
        if not client:
            raise HTTPException(status_code=401, detail="Client inconnu")
        if client.get("active") is False:
            raise HTTPException(status_code=401, detail="Client desactive")
        return client
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide ou expire")


def require_permission(permission: str):
    async def checker(client: dict = Depends(get_current_client)):
        if permission not in client.get("permissions", []):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' requise"
            )
        return client
    return checker


@auth_router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    if request.grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="grant_type doit etre 'client_credentials'")

    client = await db.frek_clients.find_one(
        {"client_id": request.client_id}, {"_id": 0}
    )
    if not client:
        raise HTTPException(status_code=401, detail="Client inconnu")
    if client.get("active") is False:
        raise HTTPException(status_code=401, detail="Client desactive")

    if client["secret_hash"] != hash_secret(request.client_secret):
        raise HTTPException(status_code=401, detail="Secret invalide")

    access_token = create_access_token(request.client_id)

    # Store token
    await db.frek_tokens.insert_one({
        "token_hash": hash_secret(access_token),
        "client_id": request.client_id,
        "expires_at": now_iso(),
        "revoked": False,
    })

    return TokenResponse(
        access_token=access_token,
        expires_in=86400,
    )
