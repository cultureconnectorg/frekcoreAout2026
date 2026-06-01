"""FREK CFL — Couche affinite : vecteur d'affinite culturelle 64-dim.

Feature hashing deterministe (sans entrainement ML — la v1 est totalement
deterministique et explicable). Le vecteur est calcule a la volee a partir des
frek_events. Deux FREK avec des trajectoires similaires auront des vecteurs
proches en cosinus.

Pas de dependance ML lourde (sklearn/numpy non-required pour la v1).
"""
import hashlib
import math
from collections import Counter

DIM = 64

db = None


def set_db(database):
    global db
    db = database


def _hash_to_bucket(token: str) -> int:
    h = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") % DIM


def _sign(token: str) -> int:
    """Sign hashing trick : evite que des collisions s'additionnent toujours en positif."""
    return 1 if hashlib.sha256((token + ":sign").encode()).digest()[0] & 1 else -1


def _normalize(vec: list[float]) -> list[float]:
    n = math.sqrt(sum(v * v for v in vec))
    if n == 0:
        return vec
    return [round(v / n, 6) for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    num = sum(x * y for x, y in zip(a, b))
    return round(num, 6)  # vecteurs deja normalises


async def compute(frek_id: str) -> dict:
    cursor = db.frek_events.find({"frek_id": frek_id}, {"_id": 0, "badge_type": 1, "event_id": 1, "action": 1})
    events = await cursor.to_list(length=10000)
    if not events:
        return {"available": False, "vector": [0.0] * DIM, "dim": DIM, "components": 0}

    # Tokens = action / badge_type / event_id (et leurs combinaisons)
    counter = Counter()
    for e in events:
        action = e.get("action") or ""
        bt = e.get("badge_type") or ""
        eid = e.get("event_id") or ""
        if action:
            counter[f"action:{action}"] += 1
        if bt:
            counter[f"badge:{bt}"] += 1
        if eid:
            counter[f"event:{eid}"] += 1
        if bt and eid:
            counter[f"badge_event:{bt}|{eid}"] += 1

    # Aussi : stages depuis frek_stages (signal supplementaire si disponible)
    stage_cursor = db.frek_stages.find({"frek_id": frek_id}, {"_id": 0, "stage": 1})
    async for s in stage_cursor:
        st = s.get("stage")
        if st:
            counter[f"stage:{st}"] += 1

    vec = [0.0] * DIM
    for token, count in counter.items():
        bucket = _hash_to_bucket(token)
        sign = _sign(token)
        # TF brut (count) — pas d'IDF en v1, l'IDF necessiterait un corpus global
        vec[bucket] += sign * count

    return {
        "available": True,
        "vector": _normalize(vec),
        "dim": DIM,
        "components": len(counter),
        "alg": "feature_hashing_v1",
    }
