"""FREK Geo — Routes HTTP /api/geo/*."""
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from . import encoder, satellite, service
from notary.service import notarize_event

logger = logging.getLogger("frek.geo.routes")

geo_router = APIRouter(prefix="/geo", tags=["FREK Geo — Couche geolocalite souveraine"])


def set_db(database):
    service.set_db(database)


# ---------- Encode (zero call externe) ----------
class EncodeRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


@geo_router.post("/encode")
async def encode(req: EncodeRequest):
    """Encode lat/lon en Plus Code + H3 + Geohash. 100% local, instantane."""
    return encoder.encode_all(req.lat, req.lon)


# ---------- Consent ----------
class ConsentRequest(BaseModel):
    level: str = Field(..., description="none | country | city | precise")


@geo_router.get("/consent/{frek_id}")
async def get_consent(frek_id: str):
    return await service.get_consent(frek_id)


@geo_router.post("/consent/{frek_id}")
async def set_consent(frek_id: str, req: ConsentRequest):
    try:
        return await service.set_consent(frek_id, req.level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Observation ----------
class ObserveRequest(BaseModel):
    frek_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    accuracy_m: Optional[float] = None
    source_event_id: Optional[str] = None
    skip_reverse: bool = False


@geo_router.post("/observe")
async def observe(req: ObserveRequest):
    return await service.observe(
        frek_id=req.frek_id,
        lat=req.lat,
        lon=req.lon,
        accuracy_m=req.accuracy_m,
        source_event_id=req.source_event_id,
        skip_reverse=req.skip_reverse,
    )


@geo_router.get("/trail/{frek_id}")
async def get_trail(frek_id: str, limit: int = Query(50, ge=1, le=500)):
    return await service.get_trail(frek_id, limit=limit)


# ---------- Heatmap publique anonyme ----------
@geo_router.get("/heatmap")
async def heatmap(min_count: int = Query(1, ge=1)):
    return await service.heatmap(min_count=min_count)


# ---------- Satellite gratuit (URL constructor) ----------
@geo_router.get("/satellite")
async def satellite_tile(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    provider: str = Query("eox_s2", description="eox_s2 | gibs | osm"),
    zoom: int = Query(13, ge=0, le=18),
):
    """Retourne l'URL d'une tuile satellite gratuite (aucun secret).

    - eox_s2  : Sentinel-2 cloudless 10m (par defaut)
    - gibs    : NASA MODIS Terra quotidien
    - osm     : OpenStreetMap basemap
    """
    if provider == "gibs":
        return satellite.gibs_tile_url(lat, lon, zoom=zoom)
    if provider == "osm":
        return satellite.osm_tile_url(lat, lon, zoom=zoom)
    return satellite.eox_s2_tile_url(lat, lon, zoom=zoom)


@geo_router.get("/satellite/sources")
async def satellite_sources():
    """Liste les sources satellite gratuites cablees."""
    return {
        "sources": [
            {"id": "eox_s2", "name": "EOX Sentinel-2 Cloudless", "resolution_m": 10, "auth": False, "free": True},
            {"id": "gibs", "name": "NASA EOSDIS GIBS (MODIS Terra)", "resolution_m": 250, "auth": False, "free": True},
            {"id": "osm", "name": "OpenStreetMap", "resolution_m": None, "auth": False, "free": True},
        ],
        "geocoding": {
            "provider": "nominatim_osm",
            "rate_limit": "1 req/s public",
            "auth": False,
            "free": True,
        },
    }


# ---------- Notarisation geo-situee Bitcoin (Phase 6.1) ----------
class GeoNotarizeRequest(BaseModel):
    frek_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    event_id: Optional[str] = None
    observation_at: Optional[str] = Field(None, description="ISO 8601, sinon now()")


@geo_router.post("/notarize")
async def geo_notarize(req: GeoNotarizeRequest):
    """Ancre une presence geo-situee dans FREK-Chain + Bitcoin OTS.

    Le payload notarise contient le couple (plus_code, h3_9, sentinel_tile, capture_date).
    Ce qui rend la preuve **temoin spatial independant** : un tiers peut verifier
    qu'a telle date il existait une image satellite reelle correspondant a la zone.

    Respecte le consentement : si level=='none', retourne 403 sans appel notary.
    """
    consent = await service.get_consent(req.frek_id)
    if consent.get("level", "none") == "none":
        raise HTTPException(status_code=403, detail="consent_required")

    encoded = encoder.encode_all(req.lat, req.lon)
    sat_eox = satellite.eox_s2_tile_url(req.lat, req.lon, zoom=13)
    sat_gibs = satellite.gibs_tile_url(req.lat, req.lon, zoom=8)
    observation_at = req.observation_at or service.now_iso()

    payload = {
        "frek_id": req.frek_id,
        "geo": {
            "plus_code": encoded["plus_code"],
            "plus_code_hd": encoded["plus_code_hd"],
            "h3_9": encoded["h3_9"],
            "h3_12": encoded["h3_12"],
            "geohash_8": encoded["geohash_8"],
            "lat": encoded["lat"],
            "lon": encoded["lon"],
        },
        "satellite_witness": {
            "eox_s2": {"provider": sat_eox["provider"], "layer": sat_eox["layer"],
                       "x": sat_eox["x"], "y": sat_eox["y"], "zoom": sat_eox["zoom"]},
            "nasa_gibs": {"provider": sat_gibs["provider"], "layer": sat_gibs["layer"],
                          "date": sat_gibs["date"], "x": sat_gibs["x"], "y": sat_gibs["y"], "zoom": sat_gibs["zoom"]},
        },
        "observation_at": observation_at,
    }

    blk = await notarize_event(
        payload_type="geo_anchor",
        payload_id=f"geo:{req.frek_id}:{encoded['h3_12']}",
        payload_data=payload,
        metadata={"phase": "6.1", "consent_level": consent["level"]},
        event_id=req.event_id,
    )
    if not blk:
        raise HTTPException(status_code=503, detail="notary_unavailable")

    return {
        "anchored": True,
        "block_height": blk.get("height"),
        "block_hash": blk.get("block_hash"),
        "payload_type": "geo_anchor",
        "geo": payload["geo"],
        "satellite_witness": payload["satellite_witness"],
        "observation_at": observation_at,
    }
