"""
FREK Audit — endpoints de timeline humaine.
Agrege frek_stages, scans, transactions, notary_blocks (revocation, renewal, walkin, identity_emit, etc)
et retourne une chronologie lisible francais avec etiquettes humaines.

Different de /api/v1/notary/* qui est cryptographique.
Ici : "qui a fait quoi quand" pour ops + audit reglementaire.

Audit-event separation (P2, 2026-08-31 — reports/FREKCORE_COMPLETION_
BACKLOG.md P2 #4): this module is a READ-ONLY, non-authoritative
convenience aggregation for humans — it writes nothing, and its
underlying sources retain whatever integrity guarantee they already had
(notary_blocks stays hash-chained; frek_stages/scans/transactions stay
plain operational records) regardless of how this endpoint presents them.
The authoritative, immutable, security-audit WRITE path is
`backend/audit_trail/` (Phase 2/3) — it subscribes to the Event Bus and
writes append-only `AuditEvent` records to `audit_trail_events`,
independently of this module. This file mixed identity-security,
work-lifecycle, operational-access, and financial events into one
undifferentiated timeline with no way to tell them apart programmatically
— that was the actual, evidenced gap (not the underlying data's
integrity, which was never at risk). Closed by adding an explicit
`category` field per event (see `_category()` below) — additive, every
existing field unchanged.
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
    category: str
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
    "identity_recovery": "Identite recuperee (recovery)",
    "identity_reconciliation": "Identite reconciliee",
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


# Audit-event separation (P2, 2026-08-31): which category each `kind`
# belongs to, so a consumer that needs only security-relevant events (or
# only financial ones) can filter this timeline programmatically instead
# of re-deriving the mapping itself. Four categories, matching what this
# module's own sources actually are — not an invented taxonomy:
# - identity_security: identity lifecycle events (also independently
#   recorded, authoritatively, by backend/audit_trail/ via the Event Bus).
# - work_lifecycle: a cultural work's GENESIS->LEGACY stage progression —
#   business/domain, not security-sensitive.
# - operational_access: physical/terrain access control (badge scans).
# - financial: jeton/cashless transactions.
CATEGORIES = {
    "identity_emit": "identity_security",
    "revocation": "identity_security",
    "renewal": "identity_security",
    "transfer": "identity_security",
    "identity_recovery": "identity_security",
    "identity_reconciliation": "identity_security",
    "stage": "work_lifecycle",
    "stage_transition": "work_lifecycle",
    "scan": "operational_access",
    "access_scan": "operational_access",
    "transaction": "financial",
    "jeton_tx": "financial",
    "walkin_emit": "operational_access",
}


def _category(kind: str) -> str:
    return CATEGORIES.get(kind, "operational_access")


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
            "category": _category("stage"),
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
            "category": _category("scan"),
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
            "category": _category("transaction"),
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

    # 4. Notary blocks (revocation, renewal, transfer, walkin_emit, and —
    # added 2026-08-31 — identity_recovery/identity_reconciliation, the two
    # new payload_types this session's RECOVERY/MERGE work added to
    # notary.chain: this timeline was silently omitting them, a real,
    # concrete instance of the separation gap this pass was asked to
    # investigate, not a hypothetical one).
    blocks = await db.notary_blocks.find(
        {
            "payload_id": frek_id,
            "payload_type": {
                "$in": [
                    "revocation",
                    "renewal",
                    "transfer",
                    "walkin_emit",
                    "identity_recovery",
                    "identity_reconciliation",
                ]
            },
        },
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
            "category": _category(kind),
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
        "category": _category("identity_emit"),
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
            "category": _category("scan"),
            "label": f"Scan {sc.get('zone')} - {sc.get('badge_id')}",
            "actor": agent_id,
            "details": {"scan_id": sc.get("scan_id"), "frek_id": sc.get("frek_id"), "zone": sc.get("zone")},
        })
    txs = await db.transactions.find({"agent_id": agent_id}, {"_id": 0}).sort("timestamp", -1).to_list(2000)
    for tx in txs:
        events.append({
            "timestamp": tx.get("timestamp"),
            "kind": "transaction",
            "category": _category("transaction"),
            "label": f"{_label(tx.get('type', 'tx'))} {tx.get('montant_jetons', 0)}J",
            "actor": agent_id,
            "details": {"tx_id": tx.get("tx_id"), "badge_id": tx.get("badge_id"), "marchand_id": tx.get("marchand_id"), "montant_jetons": tx.get("montant_jetons")},
        })
    walkins = await db.badges.find({"agent_id": agent_id}, {"_id": 0}).sort("created_at", -1).to_list(2000)
    for w in walkins:
        events.append({
            "timestamp": w.get("created_at"),
            "kind": "walkin_emit",
            "category": _category("walkin_emit"),
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
            "category": _category("scan"),
            "label": f"Scan {sc.get('zone')} - {sc.get('prenom', '')} {sc.get('nom', '')}",
            "actor": sc.get("agent_id") or sc.get("client_id"),
            "details": {"frek_id": sc.get("frek_id"), "zone": sc.get("zone"), "badge_id": sc.get("badge_id")},
        })
    cursor = db.transactions.find({"frek_id": {"$in": frek_ids}, "type": {"$ne": "REMBOURSEMENT_MARCHAND"}}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    async for tx in cursor:
        events.append({
            "timestamp": tx.get("timestamp"),
            "kind": "transaction",
            "category": _category("transaction"),
            "label": f"{_label(tx.get('type', 'tx'))} {tx.get('montant_jetons', 0)}J",
            "actor": tx.get("agent_id") or tx.get("marchand_id"),
            "details": {"frek_id": tx.get("frek_id"), "tx_id": tx.get("tx_id"), "marchand_id": tx.get("marchand_id")},
        })
    events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
    return [TimelineEvent(**e) for e in events[:limit]]
