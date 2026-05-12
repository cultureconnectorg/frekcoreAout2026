"""FREK EUDI — Endpoints OID4VCI."""
import json
import logging
import urllib.parse
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Header
from pydantic import BaseModel, Field

from did.vc import build_credential
from .metadata import (
    issuer_metadata,
    oauth_authorization_server_metadata,
    CREDENTIAL_CONFIG_ID,
    PUBLIC_BASE_URL,
)
from .sdjwt import issue_sd_jwt_vc
from . import service

logger = logging.getLogger("frek.eudi.routes")

eudi_router = APIRouter(prefix="/eudi", tags=["FREK EUDI Wallet — OID4VCI"])
wellknown_router = APIRouter(prefix="/.well-known", tags=["FREK Well-Known endpoints"])

db = None


def set_db(database):
    global db
    db = database
    service.set_db(database)


# ---------- Well-known (OID4VCI / OAuth 2.0) ----------
@wellknown_router.get("/openid-credential-issuer")
async def wk_credential_issuer():
    """OpenID4VCI issuer metadata.

    Tout wallet EUDI compatible utilise ce document pour decouvrir comment
    importer les credentials emis par FREKCORE.
    """
    return issuer_metadata()


@wellknown_router.get("/oauth-authorization-server")
async def wk_oauth_metadata():
    """RFC 8414 OAuth 2.0 Authorization Server Metadata (pre-authorized flow only)."""
    return oauth_authorization_server_metadata()


# ---------- Credential offer (genere par FREKCORE pour le porteur) ----------
@eudi_router.post("/credential-offer/{frek_id}")
async def create_offer(frek_id: str):
    """Genere un credential offer URI scannable (QR code) pour un FREK-ID donne.

    Le porteur scanne le QR avec son wallet EUDI → import automatique.
    Pre-authorized code TTL 5 min, single-use.
    """
    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    offer = await service.create_credential_offer(frek_id)

    # Format OID4VCI standard
    credential_offer = {
        "credential_issuer": PUBLIC_BASE_URL,
        "credential_configuration_ids": [CREDENTIAL_CONFIG_ID],
        "grants": {
            "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                "pre-authorized_code": offer["pre_authorized_code"],
            }
        },
    }
    encoded = urllib.parse.quote(json.dumps(credential_offer, separators=(",", ":")))
    deep_link = f"openid-credential-offer://?credential_offer={encoded}"
    universal_link = f"https://wallet.eudi.europa.eu/credential-offer?credential_offer={encoded}"

    return {
        "credential_offer": credential_offer,
        "credential_offer_uri_deep_link": deep_link,
        "credential_offer_uri_universal_link": universal_link,
        "expires_at": offer["expires_at"],
    }


# ---------- Token endpoint ----------
@eudi_router.post("/token")
async def token_endpoint(
    grant_type: str = Form(...),
    pre_authorized_code: Optional[str] = Form(None, alias="pre-authorized_code"),
):
    """Echange un pre-authorized_code contre un access_token.

    OID4VCI : grant_type doit etre 'urn:ietf:params:oauth:grant-type:pre-authorized_code'.
    """
    if grant_type != "urn:ietf:params:oauth:grant-type:pre-authorized_code":
        raise HTTPException(status_code=400, detail={"error": "unsupported_grant_type"})
    if not pre_authorized_code:
        raise HTTPException(status_code=400, detail={"error": "invalid_request"})

    result = await service.consume_pre_authorized_code(pre_authorized_code)
    if not result:
        raise HTTPException(status_code=400, detail={"error": "invalid_grant"})

    return {
        "access_token": result["access_token"],
        "token_type": "Bearer",
        "expires_in": result["expires_in"],
    }


# ---------- Credential endpoint ----------
class CredentialRequest(BaseModel):
    format: str = Field(default="ldp_vc")
    credential_definition: Optional[dict] = None
    proof: Optional[dict] = None


@eudi_router.post("/credential")
async def credential_endpoint(
    req: CredentialRequest,
    authorization: str = Header(...),
):
    """Le wallet POST son access_token + format → recoit le VC W3C signe.

    Format supporte : `ldp_vc` (W3C VC Data Model 2.0 + DataIntegrityProof / eddsa-jcs-2022).
    """
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"error": "invalid_token"})
    token = authorization[7:].strip()

    frek_id = await service.resolve_token(token)
    if not frek_id:
        raise HTTPException(status_code=401, detail={"error": "invalid_token"})

    if req.format not in ("ldp_vc", "vc+sd-jwt"):
        raise HTTPException(status_code=400, detail={"error": "unsupported_credential_format"})

    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail={"error": "credential_not_found"})

    # Chain anchor
    chain_anchor = await db.notary_blocks.find_one(
        {}, {"_id": 0, "height": 1, "block_hash": 1, "btc_anchored": 1},
        sort=[("height", -1)],
    )

    if req.format == "vc+sd-jwt":
        return issue_sd_jwt_vc(identity, chain_anchor=chain_anchor)

    vc = build_credential(identity, chain_anchor=chain_anchor)
    return {"format": "ldp_vc", "credential": vc}


class SDJWTVerifyRequest(BaseModel):
    credential: str = Field(..., description="SD-JWT VC string <jwt>~<disc>~...")


@eudi_router.post("/credential/verify-sdjwt")
async def verify_sdjwt_endpoint(req: SDJWTVerifyRequest):
    """Utilitaire serveur pour verifier un SD-JWT VC. Verification offline aussi possible
    avec la cle publique exposee via /api/v1/passport/key et /.well-known/jwks.json."""
    from .sdjwt import verify_sd_jwt_vc
    return verify_sd_jwt_vc(req.credential)
