"""
FREK Staff — Auth PIN pour PWA Scanner terrain.

Modele : un staff = {agent_id, nom, role, pin_hash, allowed_zones, active}.
PIN court (4-6 chiffres), hashe en base. Token JWT court (8h) embarque agent_id + role.
Le staff utilise ce token pour TOUS les calls scan/paiement/emission via Bearer.
Le client_id reste celui de Kiltikonet (delegation).
"""
import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from frek_v1.utils import now_iso, get_env

logger = logging.getLogger("frek.staff")
staff_router = APIRouter(prefix="/staff", tags=["FREK Staff PWA"])
bearer = HTTPBearer(auto_error=False)

db = None
STAFF_TOKEN_HOURS = 8
STAFF_TOKEN_TYPE = "staff"

# Roles : agent_acces, agent_cashless, agent_emission, superviseur
ROLE_PERMISSIONS = {
    "agent_acces": ["scan_access"],
    "agent_cashless": ["scan_cashless", "scan_access"],
    "agent_emission": ["scan_access", "scan_cashless", "emit_walkin"],
    "superviseur": ["scan_access", "scan_cashless", "emit_walkin", "view_stats"],
}


def set_db(database):
    global db
    db = database


def _hash_pin(pin: str) -> str:
    salt = os.environ.get("FREK_STAFF_PIN_SALT", "frek-staff-default-salt")
    return hashlib.sha256(f"{salt}:{pin}".encode()).hexdigest()


def _create_staff_token(agent_id: str, role: str) -> str:
    secret = get_env("SECRET_KEY")
    payload = {
        "sub": agent_id,
        "role": role,
        "type": STAFF_TOKEN_TYPE,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=STAFF_TOKEN_HOURS),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _decode_staff_token(token: str) -> dict:
    secret = get_env("SECRET_KEY")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Token invalide: {e}")
    if payload.get("type") != STAFF_TOKEN_TYPE:
        raise HTTPException(status_code=401, detail="Token non staff")
    return payload


# --- Auth dependency ---
async def get_current_staff(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> dict:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token requis")
    payload = _decode_staff_token(creds.credentials)
    agent_id = payload["sub"]
    staff = await db.staff.find_one({"agent_id": agent_id, "active": True}, {"_id": 0, "pin_hash": 0})
    if not staff:
        raise HTTPException(status_code=401, detail="Agent inconnu ou desactive")
    staff["role"] = payload.get("role", staff.get("role"))
    staff["permissions"] = ROLE_PERMISSIONS.get(staff["role"], [])
    return staff


def require_staff_perm(perm: str):
    async def _dep(staff: dict = Depends(get_current_staff)) -> dict:
        if perm not in staff.get("permissions", []):
            raise HTTPException(status_code=403, detail=f"Permission requise: {perm}")
        return staff
    return _dep


# --- Models ---
class StaffLoginRequest(BaseModel):
    agent_id: str = Field(..., description="ID agent (ex: STAFF-01)")
    pin: str = Field(..., min_length=4, max_length=8)


class StaffLoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = STAFF_TOKEN_HOURS * 3600
    agent_id: str
    nom: str
    role: str
    permissions: List[str]


class StaffMeResponse(BaseModel):
    agent_id: str
    nom: str
    role: str
    permissions: List[str]
    allowed_zones: List[str]


class StaffCreateRequest(BaseModel):
    agent_id: str
    nom: str
    role: str = Field(..., description=f"Roles: {list(ROLE_PERMISSIONS.keys())}")
    pin: str = Field(..., min_length=4, max_length=8)
    allowed_zones: List[str] = Field(default_factory=list)


# --- Routes ---
@staff_router.post("/login", response_model=StaffLoginResponse)
async def staff_login(request: StaffLoginRequest):
    try:
        from security.policies import is_staff_locked, register_staff_login_attempt
    except Exception:
        async def is_staff_locked(_): return False
        async def register_staff_login_attempt(*args, **kwargs): return None

    # Generic 401 si compte locked (pas d'info attaquant)
    if await is_staff_locked(request.agent_id):
        raise HTTPException(status_code=401, detail="Agent ou PIN invalide")

    staff = await db.staff.find_one(
        {"agent_id": request.agent_id, "active": True}, {"_id": 0}
    )
    if not staff:
        await register_staff_login_attempt(request.agent_id, success=False)
        raise HTTPException(status_code=401, detail="Agent ou PIN invalide")
    if staff.get("pin_hash") != _hash_pin(request.pin):
        await register_staff_login_attempt(request.agent_id, success=False)
        raise HTTPException(status_code=401, detail="Agent ou PIN invalide")

    # Success
    await register_staff_login_attempt(request.agent_id, success=True)

    role = staff["role"]
    token = _create_staff_token(staff["agent_id"], role)
    return StaffLoginResponse(
        access_token=token,
        agent_id=staff["agent_id"],
        nom=staff["nom"],
        role=role,
        permissions=ROLE_PERMISSIONS.get(role, []),
    )


@staff_router.get("/me", response_model=StaffMeResponse)
async def staff_me(staff: dict = Depends(get_current_staff)):
    return StaffMeResponse(
        agent_id=staff["agent_id"],
        nom=staff["nom"],
        role=staff["role"],
        permissions=staff["permissions"],
        allowed_zones=staff.get("allowed_zones", []),
    )


@staff_router.post("/admin/create")
async def staff_create(
    request: StaffCreateRequest,
    staff: dict = Depends(require_staff_perm("view_stats")),
):
    if request.role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Role invalide: {request.role}")
    existing = await db.staff.find_one({"agent_id": request.agent_id})
    if existing:
        raise HTTPException(status_code=409, detail="agent_id existant")
    doc = {
        "agent_id": request.agent_id,
        "nom": request.nom,
        "role": request.role,
        "pin_hash": _hash_pin(request.pin),
        "allowed_zones": request.allowed_zones,
        "active": True,
        "created_at": now_iso(),
        "last_login": None,
        "created_by": staff["agent_id"],
    }
    await db.staff.insert_one(doc)
    return {"agent_id": request.agent_id, "created": True}


@staff_router.get("/admin/list")
async def staff_list(staff: dict = Depends(require_staff_perm("view_stats"))):
    docs = await db.staff.find({}, {"_id": 0, "pin_hash": 0}).to_list(500)
    return {"count": len(docs), "staff": docs}


# --- Seeding ---
async def seed_default_staff():
    """Cree les comptes staff CC2026 par defaut s'ils n'existent pas."""
    defaults = [
        {
            "agent_id": "SUPERVISEUR-01",
            "nom": "Superviseur CC2026",
            "role": "superviseur",
            "pin_env": "FREK_STAFF_SUPERVISEUR_PIN",
            "default_pin": "9999",
            "allowed_zones": ["ENTREE", "SCENE", "VIP_LOUNGE", "BACKSTAGE", "EXPOSANTS", "PRESSE", "ATELIERS"],
        },
        {
            "agent_id": "EMISSION-01",
            "nom": "Agent Emission Walk-in",
            "role": "agent_emission",
            "pin_env": "FREK_STAFF_EMISSION_PIN",
            "default_pin": "1111",
            "allowed_zones": ["ENTREE"],
        },
        {
            "agent_id": "ACCES-01",
            "nom": "Agent Acces Entree",
            "role": "agent_acces",
            "pin_env": "FREK_STAFF_ACCES_PIN",
            "default_pin": "2222",
            "allowed_zones": ["ENTREE", "SCENE"],
        },
        {
            "agent_id": "CASHLESS-01",
            "nom": "Agent Cashless Marchand",
            "role": "agent_cashless",
            "pin_env": "FREK_STAFF_CASHLESS_PIN",
            "default_pin": "3333",
            "allowed_zones": ["EXPOSANTS"],
        },
    ]
    for d in defaults:
        existing = await db.staff.find_one({"agent_id": d["agent_id"]})
        if existing:
            continue
        pin = os.environ.get(d["pin_env"], d["default_pin"])
        await db.staff.insert_one({
            "agent_id": d["agent_id"],
            "nom": d["nom"],
            "role": d["role"],
            "pin_hash": _hash_pin(pin),
            "allowed_zones": d["allowed_zones"],
            "active": True,
            "created_at": now_iso(),
            "last_login": None,
            "created_by": "system",
        })
        logger.info(f"Staff seeded: {d['agent_id']} ({d['role']})")
