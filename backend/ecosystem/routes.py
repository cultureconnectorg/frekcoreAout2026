"""FREKCORE — Ecosystem awareness router.

Expose l'inventaire (registry + capabilities + integrations) sans dupliquer
la logique des branches. Pas de logique metier ici — juste de la conscience
architecturale.
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

ecosystem_router = APIRouter(prefix="/ecosystem", tags=["Ecosystem"])
_BASE = Path("/app/ecosystem")


def _load(name: str) -> dict:
    path = _BASE / name
    if not path.exists():
        raise HTTPException(500, f"Ecosystem file missing: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


@ecosystem_router.get("")
async def ecosystem_root():
    """Vue globale : doctrine + composants."""
    return _load("registry.json")


@ecosystem_router.get("/components")
async def list_components():
    """Liste des composants avec leurs statuts."""
    reg = _load("registry.json")
    return {"components": reg["components"]}


@ecosystem_router.get("/components/{component_id}")
async def get_component(component_id: str):
    reg = _load("registry.json")
    for c in reg["components"]:
        if c["id"] == component_id:
            return c
    raise HTTPException(404, f"Component '{component_id}' unknown")


@ecosystem_router.get("/capabilities")
async def list_capabilities():
    """Registry des capacites disponibles + leur etat."""
    return _load("capabilities.json")


@ecosystem_router.get("/integrations")
async def list_integrations():
    """Etat des integrations avec branches externes/specialisees.

    Une branche absente renvoie NOT_INSTALLED de facon propre —
    jamais une 500 opaque.
    """
    reg = _load("registry.json")
    integrations = []
    for c in reg["components"]:
        if c["status"] in ("external_specified", "specified_isolated"):
            integrations.append({
                "id": c["id"],
                "name": c["name"],
                "status": c["status"].upper() if c["status"] == "specified_isolated" else "NOT_INSTALLED",
                "role": c["role"],
                "contract": f"/app/ecosystem/contracts/{c['id']}.md",
                "note": c.get("note", ""),
            })
    return {"integrations": integrations}


@ecosystem_router.get("/integrations/{integration_id}/status")
async def integration_status(integration_id: str):
    """Statut ponctuel d'une integration nommee.

    Retourne toujours une reponse propre — jamais une 500.
    """
    reg = _load("registry.json")
    for c in reg["components"]:
        if c["id"] == integration_id:
            status_map = {
                "active": "ACTIVE",
                "external_specified": "NOT_INSTALLED",
                "specified_isolated": "SPECIFIED_ISOLATED",
            }
            return {
                "id": c["id"],
                "status": status_map.get(c["status"], c["status"].upper()),
                "endpoints": c.get("integration_points", []),
                "verification_method": c.get("verification_method"),
            }
    return {"id": integration_id, "status": "NOT_INSTALLED", "endpoints": [], "verification_method": None}
