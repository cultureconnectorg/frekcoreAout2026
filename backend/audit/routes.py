"""
FREK Audit — endpoints de timeline humaine.
Agrege frek_stages, scans, transactions, notary_blocks (revocation, renewal, walkin, identity_emit, etc)
et retourne une chronologie lisible francais avec etiquettes humaines.

Different de /api/v1/notary/* qui est cryptographique.
Ici : "qui a fait quoi quand" pour ops + audit reglementaire.
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from frek_v1.auth import get_current_client, require_permission

logger = logging.getLogger("frek.audit")
audit_router = APIRouter(prefix="/audit", tags=["FREK Audit — Timeline humaine"])

db = None


def set_db(database):
    global db
    db = database


class TimelineEvent(BaseModel):
    timestamp: str
    kind: str
    label: str
    actor: Optional[str] = None
    details: Optional[dict] = None


# Etiquettes humaines par type d'evenement
LABELS = {
    "identity_emit": "Identite FREK emise",
    "stage_transition": "Stage culturel franchi",
    "access_scan": "Scan d'acces",
    "jeton_tx": "Mouvement jetons",
    "walkin_emit": "Emission walk-in terrain",
    "revocation": "Identite revoquee",
    "renewal": "Identite renouvelee",
    "transfer": "Transmission identite",
    "GENESIS": "Premiere apparition (GENESIS)",
    "WORKSHOP": "Atelier (WORKSHOP)",
    "METAMORPHOSE": "Mutation (METAMORPHOSE)",
    "EMISSION": "Diffusion (EMISSION)",
    "LEGACY": "Heritage (LEGACY)",
    "PAIEMENT": "Paiement marchand",
    "RECHARGE": "Recharge wallet",
    "NFC_PAIEMENT": "Paiement NFC",
    "REMBOURSEMENT_MARCHAND": "Remboursement marchand",
}


def _label(kind: str) -> str:
    return LABELS.get(kind, kind)


@audit_router.get("/{frek_id}", response_model=List[TimelineEvent])
async def audit_frek_id(
    frek_id: str,
    limit: int = Query(500, ge=1, le=5000),
):
    """Timeline humaine consolidee pour un FREK-ID (publique-friendly)."""
    identity = await db.frek_identities.find_one({"frek_id": frek_id}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    events: list[dict] = []

    # 1. Stages (Luciole)
    stages = await db.frek_stages.find({"frek_id": frek_id}, {"_id": 0}).sort("sequence", 1).to_list(1000)
    for s in stages:
        events.append({
            "timestamp": s.get("timestamp"),
            "kind": "stage",
            "label": f"{_label(s['stage'])} — seq #{s.get('sequence')}",
            "actor": s.get("client_id"),
            "details": {
                "stage": s["stage"],
                "source": s.get("source"),
                "fingerprint": s.get("fingerprint"),
                "sequence": s.get("sequence"),
            },
        })

    # 2. Scans
    scans = await db.scans.find({"frek_id": frek_id}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    for sc in scans:
        events.append({
            "timestamp": sc.get("timestamp"),
            "kind": "scan",
            "label": f"Acces zone {sc.get('zone')}",
            "actor": sc.get("agent_id") or sc.get("client_id"),
            "details": {
                "scan_id": sc.get("scan_id"),
                "zone": sc.get("zone"),
                "via": sc.get("via", "api"),
            },
        })

    # 3. Transactions
    txs = await db.transactions.find({"frek_id": frek_id}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    for tx in txs:
        events.append({
            "timestamp": tx.get("timestamp"),
            "kind": "transaction",
            "label": f"{_label(tx.get('type', 'tx'))} — {tx.get('montant_jetons', 0)}J",
            "actor": tx.get("agent_id") or tx.get("marchand_id") or tx.get("client_id"),
            "details": {
                "tx_id": tx.get("tx_id"),
                "type": tx.get("type"),
                "montant_jetons": tx.get("montant_jetons"),
                "montant_eur": tx.get("montant_eur"),
                "marchand_id": tx.get("marchand_id"),
                "solde_apres": tx.get("solde_apres"),
            },
        })

    # 4. Notary blocks (revocation, renewal, transfer, walkin_emit)
    blocks = await db.notary_blocks.find(
        {"payload_id": frek_id, "payload_type": {"$in": ["revocation", "renewal", "transfer", "walkin_emit"]}},
        {"_id": 0, "ots_proof": 0},
    ).sort("timestamp", 1).to_list(500)
    for b in blocks:
        pd = b.get("payload_data") or {}
        kind = b["payload_type"]
        label = _label(kind)
        if kind == "revocation":
            label = f"REVOCATION — {pd.get('reason', 'sans motif')}"
        elif kind == "renewal":
            label = f"RENOUVELLEMENT — exp: {pd.get('new_expires_at') or 'perpetuel'}"
        events.append({
            "timestamp": b.get("timestamp"),
            "kind": kind,
            "label": label,
            "actor": (b.get("metadata") or {}).get("client_id") or pd.get("revoked_by"),
            "details": {
                "block_height": b["height"],
                "block_hash": b["block_hash"],
                "btc_anchored": b.get("btc_anchored", False),
                "btc_block_height": b.get("btc_block_height"),
                **pd,
            },
        })

    # 5. Identity creation (GENESIS implicite)
    events.append({
        "timestamp": identity["created_at"],
        "kind": "identity_emit",
        "label": _label("identity_emit"),
        "actor": identity.get("client_id"),
        "details": {
            "source": identity.get("source"),
            "event": identity.get("event"),
            "expires_at": identity.get("expires_at"),
        },
    })

    events.sort(key=lambda e: e.get("timestamp") or "")
    return [TimelineEvent(**e) for e in events[:limit]]


@audit_router.get("/agent/{agent_id}/actions", response_model=List[TimelineEvent])
async def audit_agent(
    agent_id: str,
    limit: int = Query(200, ge=1, le=2000),
    client: dict = Depends(get_current_client),
):
    """Timeline des actions effectuees par un agent staff (auth requise)."""
    events: list[dict] = []
    scans = await db.scans.find({"agent_id": agent_id}, {"_id": 0}).sort("timestamp", -1).to_list(2000)
    for sc in scans:
        events.append({
            "timestamp": sc.get("timestamp"),
            "kind": "scan",
            "label": f"Scan {sc.get('zone')} - {sc.get('badge_id')}",
            "actor": agent_id,
            "details": {"scan_id": sc.get("scan_id"), "frek_id": sc.get("frek_id"), "zone": sc.get("zone")},
        })
    txs = await db.transactions.find({"agent_id": agent_id}, {"_id": 0}).sort("timestamp", -1).to_list(2000)
    for tx in txs:
        events.append({
            "timestamp": tx.get("timestamp"),
            "kind": "transaction",
            "label": f"{_label(tx.get('type', 'tx'))} {tx.get('montant_jetons', 0)}J",
            "actor": agent_id,
            "details": {"tx_id": tx.get("tx_id"), "badge_id": tx.get("badge_id"), "marchand_id": tx.get("marchand_id"), "montant_jetons": tx.get("montant_jetons")},
        })
    walkins = await db.badges.find({"agent_id": agent_id}, {"_id": 0}).sort("created_at", -1).to_list(2000)
    for w in walkins:
        events.append({
            "timestamp": w.get("created_at"),
            "kind": "walkin_emit",
            "label": f"Emission walk-in - {w.get('prenom', '')} {w.get('nom', '')}",
            "actor": agent_id,
            "details": {"badge_id": w.get("badge_id"), "frek_id": w.get("frek_id"), "type_badge": w.get("type_badge")},
        })
    events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    return [TimelineEvent(**e) for e in events[:limit]]


@audit_router.get("/event/{event}/recent", response_model=List[TimelineEvent])
async def audit_event(
    event: str,
    limit: int = Query(100, ge=1, le=1000),
    client: dict = Depends(require_permission("stats")),
):
    """Audit live event-wide (auth client + permission stats requise)."""
    events: list[dict] = []
    badges = await db.badges.find({"event": event}, {"_id": 0, "frek_id": 1}).limit(5000).to_list(5000)
    frek_ids = [b["frek_id"] for b in badges if b.get("frek_id")]
    if not frek_ids:
        return []
    cursor = db.scans.find({"frek_id": {"$in": frek_ids}}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    async for sc in cursor:
        events.append({
            "timestamp": sc.get("timestamp"),
            "kind": "scan",
            "label": f"Scan {sc.get('zone')} - {sc.get('prenom', '')} {sc.get('nom', '')}",
            "actor": sc.get("agent_id") or sc.get("client_id"),
            "details": {"frek_id": sc.get("frek_id"), "zone": sc.get("zone"), "badge_id": sc.get("badge_id")},
        })
    cursor = db.transactions.find({"frek_id": {"$in": frek_ids}, "type": {"$ne": "REMBOURSEMENT_MARCHAND"}}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    async for tx in cursor:
        events.append({
            "timestamp": tx.get("timestamp"),
            "kind": "transaction",
            "label": f"{_label(tx.get('type', 'tx'))} {tx.get('montant_jetons', 0)}J",
            "actor": tx.get("agent_id") or tx.get("marchand_id"),
            "details": {"frek_id": tx.get("frek_id"), "tx_id": tx.get("tx_id"), "marchand_id": tx.get("marchand_id")},
        })
    events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    return [TimelineEvent(**e) for e in events[:limit]]
