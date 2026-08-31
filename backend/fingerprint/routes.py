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
from identity_engine import service as identity_service
from security.policies import check_rate_limit

logger = logging.getLogger("frek.fingerprint.routes")

# Sous-namespace de /core (souverainete CVLN)
fp_router = APIRouter(
    prefix="/core/fingerprint", tags=["FREK Cultural Fingerprint Layer"]
)

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


async def _is_holder(frek_id: str, x_frek_session: Optional[str]) -> bool:
    """True per-holder proof (P1 backlog #3, closes the interim-admin-key
    caveat every route below used to carry — see
    docs/architecture/FREK_ID_RECONCILIATION.md and
    reports/FREKCORE_COMPLETION_BACKLOG.md P1 #3).

    Two ways a session proves it owns `frek_id`:
    1. `frek_id` IS the session's own identity_engine FREK-ID (this
       fingerprint record belongs to an identity_engine person directly).
    2. The session's identity has `frek_id` in `linked_objects` — the
       already-existing mechanism (`POST /identity/link-object`,
       `identity_engine/routes.py`) for "this object is mine," which is
       what actually applies for the realistic case: fingerprint/geo data
       is keyed by whatever `frek_id` an external caller supplies (often
       a `frek_v1`-minted UUID4 — a different ID space `frek_v1` has no
       holder-session concept for at all, see Contradiction C1), and a
       person later links that external ID to their own identity_engine
       identity to claim it.

    No admin fallback here by design — callers combine this with their
    own admin-key check (see `_holder_or_admin` below) so the two
    authority paths stay individually auditable.
    """
    if not x_frek_session:
        return False
    session_frek_id = identity_service.verify_session_token(x_frek_session)
    if not session_frek_id:
        return False
    if session_frek_id == frek_id:
        return True
    identity = await db.frek_persons.find_one(
        {"frek_id": session_frek_id}, {"_id": 0, "linked_objects": 1}
    )
    return bool(identity and frek_id in identity.get("linked_objects", []))


async def _holder_or_admin(
    frek_id: str, x_frek_session: Optional[str], x_admin_key: str
):
    if await _is_holder(frek_id, x_frek_session):
        return
    _admin_or_403(x_admin_key)


# ---------- Consent ----------
class ConsentUpdate(BaseModel):
    layers: dict = Field(..., description="Mapping layer_name -> bool (opt-in/out)")


@fp_router.get("/consent/{frek_id}")
async def get_consent(frek_id: str):
    return await consent_mod.get_consent(frek_id)


@fp_router.post("/consent/{frek_id}")
async def update_consent(
    frek_id: str,
    payload: ConsentUpdate,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Le porteur met a jour ses choix — vraie autorisation per-holder
    (P1 backlog #3, `docs/architecture/FREK_ID_RECONCILIATION.md`).

    Toute revocation declenche un purge_layer_data (RGPD/AfCFTA).

    P0 fix (docs/decisions/0001-founder-decisions-2026-08-31.md) closed the
    "reachable by anyone" gap with an interim admin-key gate. This P1 pass
    replaces the interim with real holder authority (`_holder_or_admin`,
    see its docstring): the admin key remains only as the documented
    override for cases the holder can't self-serve.
    """
    await _holder_or_admin(frek_id, x_frek_session, x_admin_key)
    # Quelles couches sont desactivees par cette update ?
    current = await consent_mod.get_consent(frek_id)
    revoked = [
        layer
        for layer, granted in (payload.layers or {}).items()
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


async def _fp_rate_limited(frek_id: str) -> bool:
    """Rate-limit /observe/* per FREK-ID (docs/decisions/0001-...): these routes
    are called directly by an end-user's own device/browser reporting on
    itself, so gating them behind a client credential would break the real
    flow (no session system exists for that caller). Consent-gating already
    stops silent data collection; this bounds abuse volume against a
    frek_id that HAS granted consent."""
    return not await check_rate_limit(scope=frek_id, action="fingerprint_observe")


@fp_router.post("/observe/device")
async def observe_device(payload: DeviceObservation):
    if not await has_consent(payload.frek_id, "device"):
        # Silence : on accuse reception sans collecter (zero fuite info)
        return {"recorded": False, "reason": "consent_required"}
    if await _fp_rate_limited(payload.frek_id):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    return await device_mod.observe(
        payload.frek_id, payload.raw_device_hash, payload.surface
    )


class NFCScan(BaseModel):
    frek_id: str
    nfc_scan_id: str
    surface: str = Field(default="scan")


@fp_router.post("/observe/nfc")
async def observe_nfc(payload: NFCScan):
    if not await has_consent(payload.frek_id, "coupling"):
        return {"recorded": False, "reason": "consent_required"}
    if await _fp_rate_limited(payload.frek_id):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    return await layers_mod.record_nfc_scan(
        payload.frek_id, payload.nfc_scan_id, payload.surface
    )


class WebVerify(BaseModel):
    frek_id: str
    nfc_scan_id: Optional[str] = None


@fp_router.post("/observe/web-verify")
async def observe_web_verify(payload: WebVerify):
    if not await has_consent(payload.frek_id, "coupling"):
        return {"coupled": False, "reason": "consent_required"}
    if await _fp_rate_limited(payload.frek_id):
        raise HTTPException(status_code=429, detail="Trop de requetes")
    return await layers_mod.record_web_verify(payload.frek_id, payload.nfc_scan_id)


# ---------- Read fingerprint (holder or admin) ----------
@fp_router.get("/{frek_id}")
async def get_fingerprint(
    frek_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Lecture COMPLETE — le titulaire (P1, `_holder_or_admin`) ou l'admin.
    Respecte le consent par couche.

    Les couches non-consenties retournent `{available: false, reason: 'consent_required'}`.
    """
    await _holder_or_admin(frek_id, x_frek_session, x_admin_key)

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
    """Deliberately stays admin-only (P1, `_holder_or_admin` was NOT applied
    here): this compares TWO subjects, and a single holder session can only
    prove ownership of one of them — proving frek_id_a's holder-ship is not
    proof of authority to run a cross-subject comparison involving
    frek_id_b too. This is a genuinely different shape of operation than
    every other route in this file (all single-subject), so it keeps the
    SYSTEM/ADMIN authority level rather than being widened alongside them."""
    _admin_or_403(x_admin_key)
    # Necessite consent affinity sur les 2 sujets
    if not (
        await has_consent(payload.frek_id_a, "affinity")
        and await has_consent(payload.frek_id_b, "affinity")
    ):
        raise HTTPException(status_code=403, detail="consent_required_on_both")
    va = await affinity_mod.compute(payload.frek_id_a)
    vb = await affinity_mod.compute(payload.frek_id_b)
    if not (va.get("available") and vb.get("available")):
        return {"similarity": 0.0, "available": False}
    sim = affinity_mod.cosine(va["vector"], vb["vector"])
    return {
        "similarity": sim,
        "interpretation": (
            "tres similaire"
            if sim > 0.8
            else "similaire" if sim > 0.5 else "distinct" if sim > 0.2 else "orthogonal"
        ),
        "available": True,
    }


# ---------- Export RGPD ----------
@fp_router.get("/export/{frek_id}")
async def export_self(
    frek_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_export_key: str = Header(default=""),
):
    """Export RGPD : le porteur recupere tout ce que FREKCORE detient sur son fingerprint.

    P1 (2026-08-31): this route's own docstring always said "le porteur" —
    now it actually is. `X-FREK-Session` (real per-holder proof, see
    `_holder_or_admin`) is the primary path; `X-Export-Key` (matching
    `SECRET_KEY`, this route's pre-existing admin-key placeholder) remains
    as the override, unchanged in name/behavior for existing callers.
    """
    if not await _is_holder(frek_id, x_frek_session):
        _admin_or_403(x_export_key)
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
