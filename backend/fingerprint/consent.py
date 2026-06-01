"""FREK CFL — Gestion du consentement granulaire par couche."""
from datetime import datetime, timezone

LAYERS = ["cadence", "affinity", "device", "social", "anomaly", "coupling", "linguistic"]

db = None


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.frek_consent.create_index("frek_id", unique=True)
    await db.frek_consent.create_index([("frek_id", 1), ("updated_at", -1)])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_layers() -> dict:
    return {layer: False for layer in LAYERS}


async def get_consent(frek_id: str) -> dict:
    """Retourne l'etat du consentement (toutes couches a False par defaut)."""
    doc = await db.frek_consent.find_one({"frek_id": frek_id}, {"_id": 0})
    if not doc:
        return {
            "frek_id": frek_id,
            "layers": _default_layers(),
            "granted_at": None,
            "updated_at": None,
            "revoked_layers_history": [],
        }
    # Garantie de schema : toutes les couches presentes
    layers = {**_default_layers(), **(doc.get("layers") or {})}
    return {**doc, "layers": layers}


async def update_consent(frek_id: str, layers_update: dict) -> dict:
    """Mise a jour partielle des couches. Trace les revocations dans l'historique."""
    current = await get_consent(frek_id)
    new_layers = {**current["layers"]}
    revocations = list(current.get("revoked_layers_history") or [])

    for layer, granted in (layers_update or {}).items():
        if layer not in LAYERS:
            continue
        granted = bool(granted)
        # Trace de revocation
        if current["layers"].get(layer) is True and granted is False:
            revocations.append({"layer": layer, "revoked_at": _now()})
        new_layers[layer] = granted

    doc = {
        "frek_id": frek_id,
        "layers": new_layers,
        "granted_at": current.get("granted_at") or _now(),
        "updated_at": _now(),
        "revoked_layers_history": revocations,
    }
    await db.frek_consent.update_one(
        {"frek_id": frek_id}, {"$set": doc}, upsert=True
    )
    return doc


async def has_consent(frek_id: str, layer: str) -> bool:
    """Test rapide pour un layer donne, utilise par les collecteurs."""
    if layer not in LAYERS:
        return False
    doc = await db.frek_consent.find_one(
        {"frek_id": frek_id}, {"_id": 0, f"layers.{layer}": 1}
    )
    if not doc:
        return False
    return bool((doc.get("layers") or {}).get(layer, False))


async def purge_layer_data(frek_id: str, layer: str):
    """Supprime les donnees collectees pour une couche revoquee.

    Reglement RGPD/AfCFTA : la revocation entraine effacement effectif.
    """
    if layer == "device":
        await db.frek_device_observations.delete_many({"frek_id": frek_id})
    if layer == "coupling":
        await db.frek_coupling_observations.delete_many({"frek_id": frek_id})
    # cadence / affinity / social / anomaly sont calcules a la volee sur frek_events
    # => rien a effacer en plus, la couche cesse simplement d'etre exposee.
    # Marquer dans le snapshot
    await db.frek_fingerprint.update_one(
        {"frek_id": frek_id},
        {"$unset": {f"layers.{layer}": ""}},
    )
