"""FREK CFL — Couche device : empreinte d'appareil souveraine.

Le client (page /verify, scanner PWA, seal embeddable) calcule un device_hash
deterministe (canvas + fonts + WebGL + audio context + screen + tz) et l'envoie
au backend. Le backend ne fait QUE stocker le hash + agreger les observations.

Aucun cookie tiers. Aucun signal envoye sans consentement explicite (couche `device`).
"""
import hashlib
from datetime import datetime, timezone

db = None


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.frek_device_observations.create_index([("frek_id", 1), ("device_hash", 1)], unique=True)
    await db.frek_device_observations.create_index("device_hash")  # detection collision multi-FREK
    await db.frek_device_observations.create_index([("frek_id", 1), ("last_seen", -1)])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_device_hash(raw: str) -> str:
    """Renforce le hash client avec un sel serveur pour eviter le reuse cross-app."""
    pepper = "FREKCORE-CFL-DEVICE-v1"
    return hashlib.sha256(f"{pepper}|{raw}".encode("utf-8")).hexdigest()


async def observe(frek_id: str, raw_device_hash: str, surface: str = "verify") -> dict:
    """Upsert d'une observation. surface = `verify` | `scan` | `seal` | `passport`."""
    if not raw_device_hash:
        return {"recorded": False}
    h = normalize_device_hash(raw_device_hash)
    now = _now()
    await db.frek_device_observations.find_one_and_update(
        {"frek_id": frek_id, "device_hash": h},
        {
            "$setOnInsert": {"first_seen": now, "frek_id": frek_id, "device_hash": h},
            "$set": {"last_seen": now, "surface": surface},
            "$inc": {"observations": 1},
        },
        upsert=True,
    )
    return {"recorded": True, "device_hash_prefix": h[:12]}


async def compute(frek_id: str) -> dict:
    devices = await db.frek_device_observations.find(
        {"frek_id": frek_id},
        {"_id": 0, "device_hash": 1, "first_seen": 1, "last_seen": 1, "observations": 1, "surface": 1},
    ).sort("last_seen", -1).to_list(length=100)
    if not devices:
        return {"available": False, "device_count": 0}

    # Collision : un device partage entre plusieurs FREK ?
    shared = []
    for d in devices[:5]:  # ne compute que pour les 5 derniers devices
        other = await db.frek_device_observations.count_documents(
            {"device_hash": d["device_hash"], "frek_id": {"$ne": frek_id}}
        )
        if other > 0:
            shared.append({"device_hash_prefix": d["device_hash"][:12], "shared_with_count": other})

    return {
        "available": True,
        "device_count": len(devices),
        "devices": [
            {
                "device_hash_prefix": d["device_hash"][:12],
                "first_seen": d.get("first_seen"),
                "last_seen": d.get("last_seen"),
                "observations": d.get("observations", 1),
                "surface": d.get("surface"),
            }
            for d in devices[:10]
        ],
        "shared_devices": shared,
    }
