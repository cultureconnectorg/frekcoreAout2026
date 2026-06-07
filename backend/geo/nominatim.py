"""FREK Geo — Nominatim (OSM) reverse-geocoding.

Service public gratuit. Rate-limit 1 req/s. User-Agent obligatoire.
Cache memoire pour les coordonnees deja vues (par cellule H3 res 9 ≈ 175m).
"""
import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger("frek.geo.nominatim")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "FrekCore/1.0 (notaire culturel tech; contact@cvln.com)"
_TIMEOUT = 5.0

# Cache par H3 cell -> reverse geo (max 5000 entrees, simple FIFO)
_cache: dict[str, dict] = {}
_cache_order: list[str] = []
_CACHE_MAX = 5000

# Throttle pour respecter 1 req/s public Nominatim
_lock = asyncio.Lock()
_last_call = 0.0


async def reverse(lat: float, lon: float, h3_cell: Optional[str] = None) -> dict:
    """Retourne {country, country_code, region, city, suburb, display_name} ou {}.

    Aucun secret expose. Echec silencieux si Nominatim KO (offline-friendly).
    """
    cache_key = h3_cell or f"{round(lat, 4)}|{round(lon, 4)}"
    if cache_key in _cache:
        return _cache[cache_key]

    global _last_call
    async with _lock:
        now = asyncio.get_event_loop().time()
        if now - _last_call < 1.0:
            await asyncio.sleep(1.0 - (now - _last_call))
        _last_call = asyncio.get_event_loop().time()

    params = {
        "lat": str(lat),
        "lon": str(lon),
        "format": "json",
        "zoom": "10",
        "addressdetails": "1",
    }
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "fr,en"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(NOMINATIM_URL, params=params, headers=headers)
        if r.status_code != 200:
            return {}
        data = r.json() or {}
        addr = data.get("address", {}) or {}
        result = {
            "country": addr.get("country"),
            "country_code": (addr.get("country_code") or "").upper(),
            "region": addr.get("state") or addr.get("region"),
            "city": addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality"),
            "suburb": addr.get("suburb") or addr.get("neighbourhood"),
            "display_name": data.get("display_name"),
        }
        # cache
        _cache[cache_key] = result
        _cache_order.append(cache_key)
        if len(_cache_order) > _CACHE_MAX:
            old = _cache_order.pop(0)
            _cache.pop(old, None)
        return result
    except Exception as e:
        logger.info(f"nominatim_unavailable: {e}")
        return {}
