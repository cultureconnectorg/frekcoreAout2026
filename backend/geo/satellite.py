"""FREK Geo — Acces satellite gratuit (NASA GIBS + EOX Sentinel-2 cloudless).

Aucun secret. Aucun compte. Ces 2 services WMTS/WMS sont publics et gratuits.
"""
import math
from datetime import datetime, timedelta, timezone

# NASA GIBS — imagerie quotidienne, MODIS Terra true color, gratuit no-auth.
# Doc : https://wiki.earthdata.nasa.gov/display/GIBS
GIBS_TEMPLATE = (
    "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
    "MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}/"
    "GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg"
)

# EOX Sentinel-2 cloudless mosaic — Sentinel-2 10m resolution composite.
# Service WMS public gratuit, attribution requise.
# Doc : https://maps.eox.at/
EOX_S2_WMS_TEMPLATE = (
    "https://tiles.maps.eox.at/wms?service=WMS&version=1.1.1&request=GetMap"
    "&layers=s2cloudless-2023_3857&styles=&format=image/jpeg"
    "&srs=EPSG:3857&bbox={bbox}&width={w}&height={h}"
)

# OSM tiles classiques (fallback ou complement)
OSM_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

ATTRIBUTION = {
    "gibs": "Imagery: NASA EOSDIS GIBS — MODIS Terra",
    "eox_s2": "Imagery: Sentinel-2 cloudless 2023 by EOX IT Services GmbH (CC-BY 4.0)",
    "osm": "© OpenStreetMap contributors",
}


def lonlat_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to XYZ tile coordinates (Web Mercator)."""
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_to_bbox(x: int, y: int, zoom: int) -> tuple[float, float, float, float]:
    """Tile XYZ -> bbox EPSG:3857 (minx, miny, maxx, maxy)."""
    n = 2.0 ** zoom
    R = 20037508.342789244  # half circumference of Earth in EPSG:3857
    minx = x / n * 2 * R - R
    maxx = (x + 1) / n * 2 * R - R
    maxy = R - y / n * 2 * R
    miny = R - (y + 1) / n * 2 * R
    return minx, miny, maxx, maxy


def gibs_tile_url(lat: float, lon: float, zoom: int = 8, days_back: int = 2) -> dict:
    """Retourne l'URL d'une tuile satellite GIBS reelle (date la plus recente disponible).

    GIBS publie a J+1 environ. On prend J-2 pour garantir disponibilite.
    """
    if zoom < 0:
        zoom = 0
    if zoom > 9:
        zoom = 9  # GIBS MODIS level 9 max
    x, y = lonlat_to_tile(lat, lon, zoom)
    date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = GIBS_TEMPLATE.format(date=date, z=zoom, x=x, y=y)
    return {
        "provider": "nasa_gibs",
        "layer": "MODIS_Terra_CorrectedReflectance_TrueColor",
        "date": date,
        "zoom": zoom,
        "x": x,
        "y": y,
        "url": url,
        "attribution": ATTRIBUTION["gibs"],
        "auth_required": False,
    }


def eox_s2_tile_url(lat: float, lon: float, zoom: int = 13, size: int = 512) -> dict:
    """Retourne l'URL EOX Sentinel-2 cloudless 10m pour une tuile donnee."""
    if zoom < 0:
        zoom = 0
    if zoom > 18:
        zoom = 18
    x, y = lonlat_to_tile(lat, lon, zoom)
    minx, miny, maxx, maxy = tile_to_bbox(x, y, zoom)
    bbox = f"{minx},{miny},{maxx},{maxy}"
    url = EOX_S2_WMS_TEMPLATE.format(bbox=bbox, w=size, h=size)
    return {
        "provider": "eox_sentinel2_cloudless",
        "layer": "s2cloudless-2023_3857",
        "resolution_m": 10,
        "zoom": zoom,
        "x": x,
        "y": y,
        "bbox_3857": [minx, miny, maxx, maxy],
        "url": url,
        "attribution": ATTRIBUTION["eox_s2"],
        "auth_required": False,
    }


def osm_tile_url(lat: float, lon: float, zoom: int = 13) -> dict:
    x, y = lonlat_to_tile(lat, lon, zoom)
    return {
        "provider": "osm",
        "zoom": zoom,
        "x": x,
        "y": y,
        "url": OSM_TEMPLATE.format(z=zoom, x=x, y=y),
        "attribution": ATTRIBUTION["osm"],
        "auth_required": False,
    }
