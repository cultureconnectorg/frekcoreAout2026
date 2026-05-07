"""FREK DID — endpoints HTTP."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .document import build_did_document, DID_METHOD_SPEC
from .vc import build_credential, verify_credential

logger = logging.getLogger("frek.did.routes")

did_router = APIRouter(prefix="/did", tags=["FREK DID — W3C interop"])
vc_router = APIRouter(prefix="/vc", tags=["FREK Verifiable Credentials — W3C interop"])

db = None


def set_db(database):
    global db
    db = database


@did_router.get("/method/spec")
async def did_method_spec():
    """Specification publique de la methode `did:frek`."""
    return DID_METHOD_SPEC


@did_router.get("/{frek_id}")
async def resolve_did(frek_id: str):
    """Resolution DID Document pour did:frek:{frek_id}."""
    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")
    doc = build_did_document(frek_id)
    # Ajout du status si revoque/expire (extension non-cassante)
    if identity.get("revoked"):
        doc["deactivated"] = True
        doc["deactivationReason"] = identity.get("revoke_reason") or "revoked"
    return doc


async def _get_chain_anchor() -> Optional[dict]:
    """Recupere le dernier block de la FREK-Chain pour l'inclure dans le VC."""
    try:
        last = await db.notary_blocks.find_one(
            {}, {"_id": 0, "height": 1, "block_hash": 1, "btc_anchored": 1},
            sort=[("height", -1)],
        )
        return last
    except Exception:
        return None


@vc_router.get("/{frek_id}")
async def issue_credential(frek_id: str):
    """Emet un Verifiable Credential W3C signe pour le FREK-ID."""
    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")
    chain_anchor = await _get_chain_anchor()
    return build_credential(identity, chain_anchor=chain_anchor)


class VCVerifyRequest(BaseModel):
    credential: dict = Field(..., description="VC W3C complet (avec proof)")


@vc_router.post("/verify")
async def verify_credential_endpoint(req: VCVerifyRequest):
    """Verification utilitaire serveur. La meme logique tourne offline avec la cle publique."""
    return verify_credential(req.credential)
