"""FREK Geo — Encodage local (zero call externe)."""
import h3
from openlocationcode import openlocationcode as olc

GEOHASH_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode_plus_code(lat: float, lon: float, code_length: int = 10) -> str:
    """Plus Code 10 chars = ~14m precision. 11 chars = ~3m."""
    return olc.encode(lat, lon, code_length)


def encode_h3(lat: float, lon: float, resolution: int = 9) -> str:
    """H3 hex cell. resolution 9 = ~175m, 12 = ~7m."""
    return h3.latlng_to_cell(lat, lon, resolution)


def h3_neighbors(cell: str, ring: int = 1) -> list[str]:
    """Voisins H3 pour clustering."""
    return list(h3.grid_disk(cell, ring))


def encode_geohash(lat: float, lon: float, precision: int = 8) -> str:
    """Geohash classique (precision 8 = ~19m)."""
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True
    while len(geohash) < precision:
        if even:
            mid = (lon_range[0] + lon_range[1]) / 2
            if lon >= mid:
                ch |= bits[bit]
                lon_range[0] = mid
            else:
                lon_range[1] = mid
        else:
            mid = (lat_range[0] + lat_range[1]) / 2
            if lat >= mid:
                ch |= bits[bit]
                lat_range[0] = mid
            else:
                lat_range[1] = mid
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(GEOHASH_BASE32[ch])
            bit = 0
            ch = 0
    return "".join(geohash)


def encode_all(lat: float, lon: float) -> dict:
    """Calcule tous les encodages souverains en une passe (local, instantane)."""
    return {
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "plus_code": encode_plus_code(lat, lon, 10),
        "plus_code_hd": encode_plus_code(lat, lon, 11),
        "h3_9": encode_h3(lat, lon, 9),
        "h3_12": encode_h3(lat, lon, 12),
        "geohash_8": encode_geohash(lat, lon, 8),
    }
