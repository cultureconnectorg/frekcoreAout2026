"""Identity Engine — routes API.

Endpoints publics :
- POST /identity/init                    -> bootstrap FREKIdentity (attache moments session_id)
- POST /identity/{frek_id}/register/begin
- POST /identity/{frek_id}/register/complete
- POST /identity/authenticate/begin       -> auth username-less (discovery)
- POST /identity/authenticate/complete    -> retourne session token
- GET  /identity/{frek_id}                -> vue publique safe
- GET  /identity/me                       -> identite courante via header X-FREK-Session
- POST /identity/link-object              -> associe un FK ou moment a l'identite
- GET  /identity/{frek_id}/objects        -> liste des objets attaches
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from .models import (
    IDENTITY_TYPES,
    Credential,
    FREKIdentity,
    InitIdentityRequest,
    RegisterBeginRequest,
    RegisterCompleteRequest,
    AuthBeginRequest,
    AuthCompleteRequest,
    IdentityPublicResponse,
)
from . import service

try:
    # Phase 2 Priorite 6 (Event Producers) — additive, best-effort. A publish
    # failure must never break identity creation itself, matching the
    # existing defensive import pattern in backend/frek_v1/stages.py:10-14.
    from eventbus.bus import default_bus as _event_bus
    from eventbus.producers import build_identity_created_event as _build_identity_created_event
except Exception:  # pragma: no cover - defensive, see comment above
    _event_bus = None
    _build_identity_created_event = None

logger = logging.getLogger("frek.identity_engine.routes")

identity_router = APIRouter(prefix="/identity", tags=["Identity Engine"])

db = None


def set_db(mongo_db):
    global db
    db = mongo_db


CHALLENGE_TTL_SECONDS = 300  # 5 min


async def ensure_indexes():
    if db is None:
        return
    await db.frek_persons.create_index("frek_id", unique=True)
    await db.frek_persons.create_index("credentials.credential_id")
    await db.frek_persons.create_index("linked_sessions")
    await db.frek_persons_challenges.create_index("created_at", expireAfterSeconds=CHALLENGE_TTL_SECONDS)
    await db.frek_persons_challenges.create_index("frek_id")
    await db.frek_persons_challenges.create_index("challenge", unique=True)


async def _store_challenge(challenge_b64: str, frek_id: Optional[str], kind: str):
    await db.frek_persons_challenges.insert_one({
        "challenge": challenge_b64,
        "frek_id": frek_id,
        "kind": kind,  # "register" | "authenticate"
        "created_at": datetime.now(timezone.utc),
    })


async def _pop_challenge(challenge_b64: str) -> Optional[dict]:
    doc = await db.frek_persons_challenges.find_one_and_delete({"challenge": challenge_b64})
    return doc


def _to_public(identity: dict) -> dict:
    return {
        "frek_id": identity["frek_id"],
        "identity_type": identity.get("identity_type", "individual"),
        "display_name": identity.get("display_name"),
        "status": identity.get("status", "anonymous"),
        "created_at": identity.get("created_at"),
        "credentials_count": len(identity.get("credentials", [])),
        "linked_objects_count": len(identity.get("linked_objects", [])),
        "protected": identity.get("status") == "protected",
    }


# ---------------- INIT ----------------

@identity_router.post("/init")
async def init_identity(req: InitIdentityRequest):
    """Cree une FREKIdentity (anonyme au depart, sans credential).
    Si session_id fourni, attache les moments existants a cette identite.
    """
    # Note: identity_type is validated by Pydantic Literal; invalid -> 422 auto.

    frek_id = service.generate_identity_id()
    now = service.now_iso()

    identity = {
        "frek_id": frek_id,
        "identity_type": req.identity_type,
        "display_name": req.display_name,
        "created_at": now,
        "status": "anonymous",
        "credentials": [],
        "linked_objects": [],
        "linked_sessions": [req.session_id] if req.session_id else [],
        "permissions": [],
        "metadata": {},
    }
    await db.frek_persons.insert_one(identity)

    # Phase 2 Priorite 6 (Event Producers) — publish identity.created.
    # Best-effort: never allowed to fail the identity-creation response.
    if _event_bus is not None and _build_identity_created_event is not None:
        try:
            _event_bus.publish(_build_identity_created_event(identity))
        except Exception:
            logger.warning("identity.created event publish failed (non-blocking)", exc_info=True)

    # Compte les moments deja signes sous cette session (pour affichage UI)
    linked_moments_count = 0
    if req.session_id:
        linked_moments_count = await db.frek_identities.count_documents({
            "client_id": "public-window-1",
            "metadata.session_id": req.session_id,
        })

    return {
        **_to_public(identity),
        "linked_moments_count": linked_moments_count,
    }


# ---------------- REGISTER ----------------

@identity_router.post("/{frek_id}/register/begin")
async def register_begin(frek_id: str, req: RegisterBeginRequest):
    """Genere les options WebAuthn pour enregistrer une Passkey."""
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "FREK identity introuvable")

    options_json, challenge_b64 = service.registration_options(
        frek_id=frek_id,
        display_name=identity.get("display_name") or frek_id,
        existing_credentials=identity.get("credentials", []),
    )
    await _store_challenge(challenge_b64, frek_id, "register")

    return json.loads(options_json)


@identity_router.post("/{frek_id}/register/complete")
async def register_complete(frek_id: str, req: RegisterCompleteRequest):
    """Verifie la Passkey et l'attache a l'identite. Retourne un session token."""
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "FREK identity introuvable")

    cred = req.credential or {}
    # Le challenge attendu est retrouve via la derniere entree register pour ce frek_id
    challenge_doc = await db.frek_persons_challenges.find_one(
        {"frek_id": frek_id, "kind": "register"},
        sort=[("created_at", -1)],
    )
    if not challenge_doc:
        raise HTTPException(400, "Challenge introuvable ou expire — recommence l'enregistrement")

    try:
        cred_info = service.verify_registration(cred, challenge_doc["challenge"])
    except Exception as e:
        logger.warning(f"WebAuthn registration verification failed: {e}")
        raise HTTPException(400, f"Verification Passkey echouee: {e}")

    # Cleanup
    await db.frek_persons_challenges.delete_one({"_id": challenge_doc["_id"]})

    new_credential = {
        "credential_id": cred_info["credential_id"],
        "public_key": cred_info["public_key"],
        "sign_count": cred_info["sign_count"],
        "aaguid": cred_info["aaguid"],
        "transports": cred_info["transports"],
        "label": req.label,
        "created_at": service.now_iso(),
        "last_used_at": None,
    }

    await db.frek_persons.update_one(
        {"frek_id": frek_id},
        {
            "$push": {"credentials": new_credential},
            "$set": {"status": "protected"},
        },
    )

    session_token = service.issue_session_token(frek_id)
    updated = await db.frek_persons.find_one({"frek_id": frek_id})
    return {
        "session_token": session_token,
        "identity": _to_public(updated),
    }


# ---------------- AUTHENTICATE ----------------

@identity_router.post("/authenticate/begin")
async def authenticate_begin(req: AuthBeginRequest):
    """Auth WebAuthn username-less. Retourne un challenge public."""
    options_json, challenge_b64 = service.authentication_options(allowed_credentials=None)
    await _store_challenge(challenge_b64, None, "authenticate")
    return json.loads(options_json)


@identity_router.post("/authenticate/complete")
async def authenticate_complete(req: AuthCompleteRequest):
    """Verifie l'assertion Passkey. Retourne session token + identity publique."""
    cred = req.credential or {}
    credential_id = cred.get("id")
    if not credential_id:
        raise HTTPException(400, "credential.id manquant")

    challenge_doc = await db.frek_persons_challenges.find_one(
        {"kind": "authenticate", "frek_id": None},
        sort=[("created_at", -1)],
    )
    if not challenge_doc:
        raise HTTPException(400, "Challenge auth introuvable ou expire")

    # Retrouver l'identite qui possede ce credential
    identity = await db.frek_persons.find_one({"credentials.credential_id": credential_id})
    if not identity:
        raise HTTPException(404, "Passkey inconnue")

    target_cred = next(
        (c for c in identity["credentials"] if c["credential_id"] == credential_id),
        None,
    )
    if not target_cred:
        raise HTTPException(500, "credential referencee introuvable")

    try:
        new_sign_count = service.verify_authentication(
            credential=cred,
            expected_challenge_b64=challenge_doc["challenge"],
            credential_public_key_b64=target_cred["public_key"],
            current_sign_count=target_cred.get("sign_count", 0),
        )
    except Exception as e:
        logger.warning(f"WebAuthn authentication verification failed: {e}")
        raise HTTPException(401, f"Authentification Passkey echouee: {e}")

    # Cleanup + update sign_count + last_used_at
    await db.frek_persons_challenges.delete_one({"_id": challenge_doc["_id"]})
    await db.frek_persons.update_one(
        {"frek_id": identity["frek_id"], "credentials.credential_id": credential_id},
        {
            "$set": {
                "credentials.$.sign_count": new_sign_count,
                "credentials.$.last_used_at": service.now_iso(),
            }
        },
    )

    session_token = service.issue_session_token(identity["frek_id"])
    return {
        "session_token": session_token,
        "identity": _to_public(identity),
    }


# ---------------- QUERIES ----------------

@identity_router.get("/me")
async def get_me(x_frek_session: Optional[str] = Header(None)):
    """Retourne l'identite courante via le session token."""
    if not x_frek_session:
        raise HTTPException(401, "Session absente")
    frek_id = service.verify_session_token(x_frek_session)
    if not frek_id:
        raise HTTPException(401, "Session invalide ou expiree")
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "Identity introuvable")
    return _to_public(identity)


@identity_router.get("/{frek_id}")
async def get_identity(frek_id: str):
    """Vue publique safe (jamais de credentials en clair)."""
    identity = await db.frek_persons.find_one({"frek_id": frek_id})
    if not identity:
        raise HTTPException(404, "Identity introuvable")
    return _to_public(identity)


@identity_router.get("/{frek_id}/objects")
async def get_linked_objects(frek_id: str, x_frek_session: Optional[str] = Header(None)):
    """Liste des objets attaches. Requiert session valide pour le frek_id demande."""
    if not x_frek_session or service.verify_session_token(x_frek_session) != frek_id:
        raise HTTPException(401, "Session invalide pour cet identity")

    identity = await db.frek_persons.find_one({"frek_id": frek_id}, {"_id": 0, "credentials": 0})
    if not identity:
        raise HTTPException(404, "Identity introuvable")

    # Rassemble moments + fk lies + moments des linked_sessions
    linked_ids = set(identity.get("linked_objects", []))
    sessions = identity.get("linked_sessions", [])

    moments = []
    if sessions:
        cursor = db.frek_identities.find(
            {"client_id": "public-window-1", "metadata.session_id": {"$in": sessions}},
            {"_id": 0, "email_hash": 0, "metadata.ip_key": 0},
        ).sort("created_at", -1).limit(200)
        moments = await cursor.to_list(200)

    fks = []
    if linked_ids:
        cursor = db.fk_objects.find({"frek_id": {"$in": list(linked_ids)}}, {"_id": 0, "storage_path": 0})
        fks = await cursor.to_list(200)

    return {
        "frek_id": frek_id,
        "moments": moments,
        "fk_objects": fks,
        "linked_sessions_count": len(sessions),
    }


@identity_router.post("/link-object")
async def link_object(payload: dict, x_frek_session: Optional[str] = Header(None)):
    """Attache un frek_id d'objet (moment ou FK) a l'identite courante."""
    if not x_frek_session:
        raise HTTPException(401, "Session requise")
    frek_id = service.verify_session_token(x_frek_session)
    if not frek_id:
        raise HTTPException(401, "Session invalide")

    object_id = payload.get("object_id")
    if not object_id:
        raise HTTPException(400, "object_id requis")

    await db.frek_persons.update_one(
        {"frek_id": frek_id},
        {"$addToSet": {"linked_objects": object_id}},
    )
    return {"ok": True, "object_id": object_id}
