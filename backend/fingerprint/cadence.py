"""FREK CFL — Couche cadence : velocite, frequence, patterns horaires.

Calculee a partir de frek_events. Aucune donnee additionnelle n'est stockee :
la cadence est une lecture statistique des events deja consentis a l'ingest.
"""
import statistics
from datetime import datetime, timezone
from typing import Optional

db = None


def set_db(database):
    global db
    db = database


def _parse_iso(s: Optional[str]):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


async def compute(frek_id: str) -> dict:
    """Retourne un dict de metriques cadence.

    - event_count : nb total
    - inter_event_seconds_mean / median / stddev
    - hour_histogram : repartition par heure UTC (0..23)
    - weekday_histogram : repartition par jour (0=lundi..6=dimanche)
    - velocity_24h : nb events sur 24h glissantes
    - last_inter_event_seconds : dernier ecart (signal de freshness)
    """
    cursor = db.frek_events.find(
        {"frek_id": frek_id},
        {"_id": 0, "timestamp": 1, "ingested_at": 1},
    ).sort("ingested_at", 1)
    events = await cursor.to_list(length=10000)
    if not events:
        return {"event_count": 0, "available": False}

    ts = [(_parse_iso(e.get("ingested_at")) or _parse_iso(e.get("timestamp"))) for e in events]
    ts = [t for t in ts if t is not None]
    if not ts:
        return {"event_count": 0, "available": False}

    inter = [(ts[i] - ts[i - 1]).total_seconds() for i in range(1, len(ts))]
    inter_mean = statistics.fmean(inter) if inter else 0.0
    inter_median = statistics.median(inter) if inter else 0.0
    inter_stdev = statistics.pstdev(inter) if len(inter) > 1 else 0.0

    hour_hist = [0] * 24
    weekday_hist = [0] * 7
    for t in ts:
        hour_hist[t.hour] += 1
        weekday_hist[t.weekday()] += 1

    now = datetime.now(timezone.utc)
    velocity_24h = sum(1 for t in ts if (now - t).total_seconds() <= 86400)

    return {
        "available": True,
        "event_count": len(ts),
        "inter_event_seconds_mean": round(inter_mean, 2),
        "inter_event_seconds_median": round(inter_median, 2),
        "inter_event_seconds_stddev": round(inter_stdev, 2),
        "last_inter_event_seconds": round(inter[-1], 2) if inter else None,
        "hour_histogram": hour_hist,
        "weekday_histogram": weekday_hist,
        "velocity_24h": velocity_24h,
        "first_seen": ts[0].isoformat(),
        "last_seen": ts[-1].isoformat(),
    }
