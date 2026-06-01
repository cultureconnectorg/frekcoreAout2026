"""FREK CFL — Endpoints HTTP /api/core/fingerprint/*."""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from . import consent as consent_mod
from . import cadence as cadence_mod
from . import affinity as affinity_mod
from . import device as device_mod
from . import layers as layers_mod
from .consent import LAYERS, has_consent

logger = logging.getLogger("frek.fingerprint.routes")

# Sous-namespace de /core (souverainete CVLN)
fp_router = APIRouter(prefix="/core/fingerprint", tags=["FREK Cultural Fingerprint Layer"])

db = None


def set_db(database):
    global db
    db = database
    consent_mod.set_db(database)
    cadence_mod.set_db(database)
    affinity_mod.set_db(database)
    device_mod.set_db(database)
    layers_mod.set_db(database)


async def ensure_indexes():
    await consent_mod.ensure_indexes()
    await device_mod.ensure_indexes()
    await layers_mod.ensure_indexes()
    await db.frek_fingerprint.create_index("frek_id", unique=True)


def _admin_or_403(x_admin_key: str):
    expected = os.environ.get("SECRET_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="invalid_admin_key")


# ---------- Consent ----------
class ConsentUpdate(BaseModel):
    layers: dict = Field(..., description="Mapping layer_name -> bool (opt-in/out)")


@fp_router.get("/consent/{frek_id}")
async def get_consent(frek_id: str):
    return await consent_mod.get_consent(frek_id)


@fp_router.post("/consent/{frek_id}")
async def update_consent(frek_id: str, payload: ConsentUpdate):
    """Le porteur (ou un client autorise mandate par lui) met a jour ses choix.

    Toute revocation declenche un purge_layer_data (RGPD/AfCFTA).
    """
    # Quelles couches sont desactivees par cette update ?
    current = await consent_mod.get_consent(frek_id)
    revoked = [
        layer for layer, granted in (payload.layers or {}).items()
        if layer in LAYERS and current["layers"].get(layer) and not granted
    ]
    updated = await consent_mod.update_consent(frek_id, payload.layers)
    for layer in revoked:
        await consent_mod.purge_layer_data(frek_id, layer)
    return {"updated": updated, "purged_layers": revoked}


# ---------- Observe (entrant — collect signals) ----------
class DeviceObservation(BaseModel):
    frek_id: str
    raw_device_hash: str = Field(..., min_length=8, max_length=256)
    surface: str = Field(default="verify")


@fp_router.post("/observe/device")
async def observe_device(payload: DeviceObservation):
    if not await has_consent(payload.frek_id, "device"):
        # Silence : on accuse reception sans collecter (zero fuite info)
        return {"recorded": False, "reason": "consent_required"}
    return await device_mod.observe(payload.frek_id, payload.raw_device_hash, payload.surface)


class NFCScan(BaseModel):
    frek_id: str
    nfc_scan_id: str
    surface: str = Field(default="scan")


@fp_router.post("/observe/nfc")
async def observe_nfc(payload: NFCScan):
    if not await has_consent(payload.frek_id, "coupling"):
        return {"recorded": False, "reason": "consent_required"}
    return await layers_mod.record_nfc_scan(payload.frek_id, payload.nfc_scan_id, payload.surface)


class WebVerify(BaseModel):
    frek_id: str
    nfc_scan_id: Optional[str] = None


@fp_router.post("/observe/web-verify")
async def observe_web_verify(payload: WebVerify):
    if not await has_consent(payload.frek_id, "coupling"):
        return {"coupled": False, "reason": "consent_required"}
    return await layers_mod.record_web_verify(payload.frek_id, payload.nfc_scan_id)


# ---------- Read fingerprint (admin) ----------
@fp_router.get("/{frek_id}")
async def get_fingerprint(frek_id: str, x_admin_key: str = Header(default="")):
    """Lecture COMPLETE — admin uniquement. Respecte le consent par couche.

    Les couches non-consenties retournent `{available: false, reason: 'consent_required'}`.
    """
    _admin_or_403(x_admin_key)

    consent = await consent_mod.get_consent(frek_id)
    layers_data = {}
    if consent["layers"].get("cadence"):
        layers_data["cadence"] = await cadence_mod.compute(frek_id)
    else:
        layers_data["cadence"] = {"available": False, "reason": "consent_required"}

    if consent["layers"].get("affinity"):
        layers_data["affinity"] = await affinity_mod.compute(frek_id)
    else:
        layers_data["affinity"] = {"available": False, "reason": "consent_required"}

    if consent["layers"].get("device"):
        layers_data["device"] = await device_mod.compute(frek_id)
    else:
        layers_data["device"] = {"available": False, "reason": "consent_required"}

    if consent["layers"].get("social"):
        layers_data["social"] = await layers_mod.compute_social(frek_id)
    else:
        layers_data["social"] = {"available": False, "reason": "consent_required"}

    if consent["layers"].get("anomaly"):
        layers_data["anomaly"] = await layers_mod.compute_anomaly(frek_id)
    else:
        layers_data["anomaly"] = {"available": False, "reason": "consent_required"}

    if consent["layers"].get("coupling"):
        layers_data["coupling"] = await layers_mod.compute_coupling(frek_id)
    else:
        layers_data["coupling"] = {"available": False, "reason": "consent_required"}

    if consent["layers"].get("linguistic"):
        layers_data["linguistic"] = await layers_mod.compute_linguistic(frek_id)
    else:
        layers_data["linguistic"] = {"available": False, "reason": "consent_required"}

    return {
        "frek_id": frek_id,
        "consent": consent["layers"],
        "layers": layers_data,
        "ownership": "CVLN Group — Cultural Fingerprint Layer v1",
    }


# ---------- Compare 2 fingerprints (affinite cosinus) ----------
class MatchRequest(BaseModel):
    frek_id_a: str
    frek_id_b: str


@fp_router.post("/match")
async def match(payload: MatchRequest, x_admin_key: str = Header(default="")):
    _admin_or_403(x_admin_key)
    # Necessite consent affinity sur les 2 sujets
    if not (await has_consent(payload.frek_id_a, "affinity") and await has_consent(payload.frek_id_b, "affinity")):
        raise HTTPException(status_code=403, detail="consent_required_on_both")
    va = await affinity_mod.compute(payload.frek_id_a)
    vb = await affinity_mod.compute(payload.frek_id_b)
    if not (va.get("available") and vb.get("available")):
        return {"similarity": 0.0, "available": False}
    sim = affinity_mod.cosine(va["vector"], vb["vector"])
    return {
        "similarity": sim,
        "interpretation": (
            "tres similaire" if sim > 0.8 else
            "similaire" if sim > 0.5 else
            "distinct" if sim > 0.2 else
            "orthogonal"
        ),
        "available": True,
    }


# ---------- Export RGPD ----------
@fp_router.get("/export/{frek_id}")
async def export_self(frek_id: str, x_export_key: str = Header(default="")):
    """Export RGPD : le porteur recupere tout ce que FREKCORE detient sur son fingerprint.

    Protege par X-Export-Key (token jetable a generer cote /verify, hors-scope ici :
    on accepte la SECRET_KEY pour la v1 — sera remplace par un token specifique a
    la Phase 5.5 quand le flux porteur sera defini).
    """
    _admin_or_403(x_export_key)  # placeholder porteur-key
    consent = await consent_mod.get_consent(frek_id)
    payload = {
        "frek_id": frek_id,
        "consent": consent,
        "layers": {
            "cadence": await cadence_mod.compute(frek_id),
            "affinity": await affinity_mod.compute(frek_id),
            "device": await device_mod.compute(frek_id),
            "social": await layers_mod.compute_social(frek_id),
            "anomaly": await layers_mod.compute_anomaly(frek_id),
            "coupling": await layers_mod.compute_coupling(frek_id),
            "linguistic": await layers_mod.compute_linguistic(frek_id),
        },
        "rights": {
            "rectify": "Modifier le consentement via POST /core/fingerprint/consent/{frek_id}",
            "erase": "Revoquer un layer = purge des donnees associees",
            "portability": "Cet export contient toutes les donnees brutes",
        },
        "ownership": "CVLN Group — souverainete absolue, aucune donnee partagee avec des tiers",
    }
    return payload
