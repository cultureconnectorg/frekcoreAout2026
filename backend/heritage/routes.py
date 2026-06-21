"""
FREK Heritage / Transmission — Routes
"""
import hashlib
import secrets
import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger("frek.heritage")

heritage_router = APIRouter(prefix="/heritage", tags=["FREK Heritage"])

db = None


def set_db(database):
    global db
    db = database


# ---------- helpers ----------
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _hash_secret(secret: str) -> str:
    # secret bind sur (frek_id, secret) pour empecher rejeu cross-FREK
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


# Resolveurs lazy pour eviter cycles
def _notarize():
    try:
        from notary.service import notarize_event
        return notarize_event
    except Exception:
        async def _noop(*a, **k):
            return None
        return _noop


def _auth_get_current_client():
    """Reuse l'auth FREK v1 (OAuth2 client_credentials)."""
    from frek_v1.auth import get_current_client
    return get_current_client


def _auth_require_permission(perm: str):
    from frek_v1.auth import require_permission
    return require_permission(perm)


# ---------- Models ----------
class DeclareRequest(BaseModel):
    beneficiary_email: EmailStr = Field(..., description="Email du beneficiaire (hash seul stocke)")
    conditions: List[str] = Field(
        default_factory=lambda: ["on_revocation"],
        description="Declencheurs : on_revocation | on_expiry | manual",
    )
    note: Optional[str] = Field(None, max_length=280, description="Note libre (optionnel)")


class DeclareResponse(BaseModel):
    frek_id: str
    declaration_id: str
    declared_at: str
    beneficiary_email_hash: str
    claim_secret: str
    conditions: List[str]
    message: str


class ClaimRequest(BaseModel):
    frek_id: str
    beneficiary_email: EmailStr
    claim_secret: str = Field(..., min_length=8, description="Secret remis lors de la declaration")
    new_owner_email: Optional[EmailStr] = Field(None, description="Nouvel email proprietaire (optionnel)")


class TransferRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Justification (deces, donation, retraite...)")
    force: bool = Field(False, description="Forcer meme si conditions=manual pas presente")


# ---------- Endpoints ----------
@heritage_router.post("/{frek_id}/declare", response_model=DeclareResponse)
async def declare_beneficiary(
    frek_id: str,
    request: DeclareRequest,
    client: dict = Depends(_auth_require_permission("emit")),
):
    """Declare un beneficiaire pour ce FREK-ID. Idempotent : remplace la declaration active."""
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]}, {"_id": 0}
    )
    if not identity:
        raise HTTPException(404, f"FREK-ID {frek_id} introuvable")
    if identity.get("revoked"):
        raise HTTPException(400, "FREK-ID revoque, declaration impossible")
    if identity.get("transferred"):
        raise HTTPException(400, "FREK-ID deja transfere a un nouveau detenteur")

    # Desactive l'ancienne declaration active si presente
    await db.frek_heritage_declarations.update_many(
        {"frek_id": frek_id, "active": True},
        {"$set": {"active": False, "superseded_at": _now()}},
    )

    declaration_id = secrets.token_urlsafe(12)
    claim_secret = secrets.token_urlsafe(24)  # remis au declarant pour le beneficiaire
    beneficiary_hash = _hash_email(request.beneficiary_email)
    now = _now()

    doc = {
        "declaration_id": declaration_id,
        "frek_id": frek_id,
        "declared_by_client_id": client["client_id"],
        "declared_at": now,
        "beneficiary_email_hash": beneficiary_hash,
        "claim_secret_hash": _hash_secret(claim_secret),
        "conditions": request.conditions,
        "note": request.note,
        "active": True,
        "claimed": False,
        "claimed_at": None,
    }
    await db.frek_heritage_declarations.insert_one(doc)

    notarize_event = _notarize()
    await notarize_event(
        payload_type="heritage_declare",
        payload_id=declaration_id,
        payload_data={
            "frek_id": frek_id,
            "declaration_id": declaration_id,
            "beneficiary_email_hash": beneficiary_hash,
            "conditions": request.conditions,
            "declared_at": now,
        },
        metadata={"client_id": client["client_id"]},
        event_id=identity.get("event"),
    )

    logger.info(f"Heritage declared : {frek_id} -> {beneficiary_hash[:12]}...")
    return DeclareResponse(
        frek_id=frek_id,
        declaration_id=declaration_id,
        declared_at=now,
        beneficiary_email_hash=beneficiary_hash,
        claim_secret=claim_secret,
        conditions=request.conditions,
        message=(
            "Declaration enregistree. Transmettez le claim_secret au beneficiaire "
            "de facon securisee — il sera detruit cote serveur (hash seul conserve)."
        ),
    )


@heritage_router.get("/{frek_id}")
async def get_declaration(
    frek_id: str,
    client: dict = Depends(_auth_get_current_client()),
):
    """Retourne la declaration active (sans secret)."""
    decl = await db.frek_heritage_declarations.find_one(
        {"frek_id": frek_id, "active": True}, {"_id": 0, "claim_secret_hash": 0}
    )
    if not decl:
        raise HTTPException(404, "Aucune declaration active")
    return decl


@heritage_router.delete("/{frek_id}")
async def revoke_declaration(
    frek_id: str,
    client: dict = Depends(_auth_require_permission("emit")),
):
    """Revoque la declaration active (le porteur change d'avis)."""
    decl = await db.frek_heritage_declarations.find_one(
        {"frek_id": frek_id, "active": True, "declared_by_client_id": client["client_id"]},
        {"_id": 0},
    )
    if not decl:
        raise HTTPException(404, "Aucune declaration active a revoquer")

    await db.frek_heritage_declarations.update_one(
        {"declaration_id": decl["declaration_id"]},
        {"$set": {"active": False, "revoked_at": _now()}},
    )
    notarize_event = _notarize()
    await notarize_event(
        payload_type="heritage_revoke",
        payload_id=decl["declaration_id"],
        payload_data={
            "frek_id": frek_id,
            "declaration_id": decl["declaration_id"],
            "revoked_at": _now(),
        },
        metadata={"client_id": client["client_id"]},
        event_id=None,
    )
    return {"frek_id": frek_id, "revoked": True, "declaration_id": decl["declaration_id"]}


@heritage_router.post("/claim")
async def claim_beneficiary(request: ClaimRequest):
    """Le beneficiaire revendique le FREK-ID avec son email + claim_secret.
    Public (pas d'auth) : la preuve repose sur le secret partage hors-bande.
    """
    decl = await db.frek_heritage_declarations.find_one(
        {"frek_id": request.frek_id, "active": True}, {"_id": 0}
    )
    if not decl:
        raise HTTPException(404, "Aucune declaration active pour ce FREK-ID")
    if decl.get("claimed"):
        raise HTTPException(409, "Declaration deja revendiquee")

    if _hash_email(request.beneficiary_email) != decl["beneficiary_email_hash"]:
        raise HTTPException(403, "Email beneficiaire ne correspond pas")
    if _hash_secret(request.claim_secret) != decl["claim_secret_hash"]:
        raise HTTPException(403, "claim_secret invalide")

    identity = await db.frek_identities.find_one({"frek_id": request.frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(404, "FREK-ID introuvable")

    now = _now()
    new_owner_hash = (
        _hash_email(request.new_owner_email) if request.new_owner_email else decl["beneficiary_email_hash"]
    )
    previous_owner_hash = identity.get("email_hash")

    transfer_id = secrets.token_urlsafe(12)
    transfer_doc = {
        "transfer_id": transfer_id,
        "frek_id": request.frek_id,
        "declaration_id": decl["declaration_id"],
        "previous_owner_email_hash": previous_owner_hash,
        "new_owner_email_hash": new_owner_hash,
        "transferred_at": now,
        "mode": "claim",
    }
    await db.frek_heritage_transfers.insert_one(transfer_doc)

    # Marquer la declaration claimed et l'identite transferee
    await db.frek_heritage_declarations.update_one(
        {"declaration_id": decl["declaration_id"]},
        {"$set": {"claimed": True, "claimed_at": now, "active": False}},
    )
    await db.frek_identities.update_one(
        {"frek_id": request.frek_id},
        {"$set": {
            "email_hash": new_owner_hash,
            "transferred": True,
            "transferred_at": now,
            "previous_owner_email_hash": previous_owner_hash,
        }},
    )

    notarize_event = _notarize()
    await notarize_event(
        payload_type="heritage_transfer",
        payload_id=transfer_id,
        payload_data={
            "frek_id": request.frek_id,
            "transfer_id": transfer_id,
            "declaration_id": decl["declaration_id"],
            "previous_owner_email_hash": previous_owner_hash,
            "new_owner_email_hash": new_owner_hash,
            "transferred_at": now,
            "mode": "claim",
        },
        metadata={},
        event_id=identity.get("event"),
    )

    logger.info(f"Heritage claimed : {request.frek_id} -> nouveau detenteur {new_owner_hash[:12]}...")
    return {
        "frek_id": request.frek_id,
        "transfer_id": transfer_id,
        "transferred_at": now,
        "message": "Transmission effectuee. Lignee cryptographique conservee sur FREK-Chain.",
    }


@heritage_router.post("/{frek_id}/transfer")
async def force_transfer(
    frek_id: str,
    request: TransferRequest,
    client: dict = Depends(_auth_require_permission("emit")),
):
    """Transfert ordonne par le client (ex: deces atteste, donation).
    Le beneficiaire devient automatiquement le nouveau detenteur (sans claim).
    """
    decl = await db.frek_heritage_declarations.find_one(
        {"frek_id": frek_id, "active": True}, {"_id": 0}
    )
    if not decl:
        raise HTTPException(404, "Aucune declaration active")
    if not request.force and "manual" not in decl.get("conditions", []):
        raise HTTPException(
            400,
            "Transfert manuel non autorise (conditions ne contiennent pas 'manual'). "
            "Passer force=true pour outrepasser.",
        )

    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]}, {"_id": 0}
    )
    if not identity:
        raise HTTPException(404, "FREK-ID introuvable ou pas autorise")

    now = _now()
    transfer_id = secrets.token_urlsafe(12)
    previous_owner_hash = identity.get("email_hash")
    new_owner_hash = decl["beneficiary_email_hash"]

    await db.frek_heritage_transfers.insert_one({
        "transfer_id": transfer_id,
        "frek_id": frek_id,
        "declaration_id": decl["declaration_id"],
        "previous_owner_email_hash": previous_owner_hash,
        "new_owner_email_hash": new_owner_hash,
        "transferred_at": now,
        "mode": "force",
        "reason": request.reason,
        "forced_by": client["client_id"],
    })
    await db.frek_heritage_declarations.update_one(
        {"declaration_id": decl["declaration_id"]},
        {"$set": {"claimed": True, "claimed_at": now, "active": False, "force_reason": request.reason}},
    )
    await db.frek_identities.update_one(
        {"frek_id": frek_id},
        {"$set": {
            "email_hash": new_owner_hash,
            "transferred": True,
            "transferred_at": now,
            "previous_owner_email_hash": previous_owner_hash,
        }},
    )

    notarize_event = _notarize()
    await notarize_event(
        payload_type="heritage_transfer",
        payload_id=transfer_id,
        payload_data={
            "frek_id": frek_id,
            "transfer_id": transfer_id,
            "declaration_id": decl["declaration_id"],
            "previous_owner_email_hash": previous_owner_hash,
            "new_owner_email_hash": new_owner_hash,
            "transferred_at": now,
            "mode": "force",
            "reason": request.reason,
        },
        metadata={"client_id": client["client_id"]},
        event_id=identity.get("event"),
    )

    return {
        "frek_id": frek_id,
        "transfer_id": transfer_id,
        "transferred_at": now,
        "reason": request.reason,
        "message": "Transfert force effectue. Lignee notarisee.",
    }


@heritage_router.get("/lineage/{frek_id}")
async def get_lineage(frek_id: str):
    """Lignee complete et publique d'un FREK-ID (chain of custody).
    Affiche uniquement les hash, jamais les emails clair.
    """
    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(404, "FREK-ID introuvable")

    transfers = await db.frek_heritage_transfers.find(
        {"frek_id": frek_id}, {"_id": 0}
    ).sort("transferred_at", 1).to_list(100)

    declarations = await db.frek_heritage_declarations.find(
        {"frek_id": frek_id}, {"_id": 0, "claim_secret_hash": 0}
    ).sort("declared_at", 1).to_list(100)

    return {
        "frek_id": frek_id,
        "created_at": identity.get("created_at"),
        "original_owner_email_hash": (
            identity.get("previous_owner_email_hash") or identity.get("email_hash")
        ),
        "current_owner_email_hash": identity.get("email_hash"),
        "transferred": bool(identity.get("transferred")),
        "transfers_count": len(transfers),
        "declarations": declarations,
        "transfers": transfers,
        "doctrine": "Lignee cryptographique conservee a vie sur FREK-Chain (Bitcoin-anchored).",
    }
