"""FREK Standards — Routes well-known + manifest universel."""
import logging

from fastapi import APIRouter, HTTPException

from .manifest import (
    jwk_set,
    did_configuration,
    manifest_universal,
)

logger = logging.getLogger("frek.standards.routes")

# Well-known (universel) — relais ingress documente : .well-known/* -> /api/.well-known/*
standards_wellknown_router = APIRouter(prefix="/.well-known", tags=["FREK Well-Known endpoints"])

# Manifest universel
standards_router = APIRouter(prefix="/standards", tags=["FREK Standards — Manifest universel"])


@standards_wellknown_router.get("/jwks.json")
async def wk_jwks():
    """JWK Set RFC 7517 — cle publique Ed25519 universellement consommable.

    Format standard pour OIDC, OAuth2, EUDI, ID4Africa, ITU.
    """
    return jwk_set()


@standards_wellknown_router.get("/did-configuration.json")
async def wk_did_configuration():
    """DIF Well-Known DID Configuration v1.

    Prouve cryptographiquement que `frekcore.com` controle `did:frek:frekcore`.
    Verifiable par tout wallet conforme DIF.
    """
    return did_configuration()


@standards_router.get("/manifest")
async def standards_manifest():
    """Manifest declaratif global — liste tous les ecosystemes supportes."""
    return manifest_universal()


@standards_router.get("/{ecosystem}")
async def standards_ecosystem(ecosystem: str):
    """Mapping detaille pour un ecosysteme donne."""
    m = manifest_universal()
    if ecosystem not in m["ecosystems"]:
        raise HTTPException(
            status_code=404,
            detail=f"Ecosysteme inconnu. Choix : {sorted(m['ecosystems'].keys())}",
        )
    return {ecosystem: m["ecosystems"][ecosystem], "trust_root": m["trust_root"]}
