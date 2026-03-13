"""
CC2026 Jetons Digitaux — Wallet, Paiement, Packs
1 Jeton CC = 1.50 EUR · Packs 10/25/50/100
"""
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from frek_v1.auth import require_permission
from frek_v1.utils import now_iso

jetons_router = APIRouter(prefix="/jetons", tags=["CC2026 Jetons"])
logger = logging.getLogger("frek.jetons")

db = None
JETON_VALUE = 1.50  # EUR

PACKS = {
    "decouverte": {"jetons": 10, "prix": 13.50, "valeur": 15.00, "economie": 1.50},
    "culture": {"jetons": 25, "prix": 30.00, "valeur": 37.50, "economie": 7.50},
    "diaspora": {"jetons": 50, "prix": 55.00, "valeur": 75.00, "economie": 20.00},
    "vip": {"jetons": 100, "prix": 100.00, "valeur": 150.00, "economie": 50.00},
}


def set_db(database):
    global db
    db = database


class RechargeRequest(BaseModel):
    badge_id: str
    pack: str = Field(..., description="decouverte, culture, diaspora, vip")
    payment_method: str = Field("stripe", description="stripe, cash, cb_site")


class PaiementRequest(BaseModel):
    badge_id: str
    montant_jetons: int = Field(..., gt=0, description="Nombre de jetons a debiter")
    marchand_id: str
    description: Optional[str] = None


class RemboursementRequest(BaseModel):
    marchand_id: str
    montant_eur: float


@jetons_router.get("/packs")
async def list_packs():
    return {"packs": PACKS, "jeton_value_eur": JETON_VALUE}


@jetons_router.post("/recharge")
async def recharge_wallet(
    request: RechargeRequest,
    client: dict = Depends(require_permission("stage")),
):
    pack = PACKS.get(request.pack)
    if not pack:
        raise HTTPException(status_code=400, detail=f"Pack invalide. Choix: {list(PACKS.keys())}")

    badge = await db.badges.find_one({"badge_id": request.badge_id}, {"_id": 0})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {request.badge_id} introuvable")

    now = now_iso()
    tx_id = str(uuid.uuid4())[:12]

    # Credit wallet
    new_solde = badge.get("jetons_solde", 0) + pack["jetons"]
    await db.badges.update_one(
        {"badge_id": request.badge_id},
        {"$set": {"jetons_solde": new_solde}}
    )

    # Record transaction
    tx = {
        "tx_id": tx_id,
        "type": "RECHARGE",
        "badge_id": request.badge_id,
        "frek_id": badge.get("frek_id"),
        "montant_jetons": pack["jetons"],
        "montant_eur": pack["prix"],
        "pack": request.pack,
        "payment_method": request.payment_method,
        "marchand_id": None,
        "description": f"Recharge pack {request.pack}",
        "solde_apres": new_solde,
        "timestamp": now,
        "client_id": client["client_id"],
    }
    await db.transactions.insert_one(tx)

    # Record METAMORPHOSE stage
    seq_doc = await db.frek_stages.find_one(
        {"frek_id": badge["frek_id"]}, {"_id": 0, "sequence": 1},
        sort=[("sequence", -1)]
    )
    next_seq = (seq_doc["sequence"] + 1) if seq_doc else 1

    await db.frek_stages.insert_one({
        "frek_id": badge["frek_id"],
        "stage": "METAMORPHOSE",
        "fingerprint": tx_id,
        "metadata_hash": None,
        "timestamp": now,
        "source": "jeton_recharge",
        "sequence": next_seq,
        "client_id": client["client_id"],
    })

    # Update FREK identity stages
    await db.frek_identities.update_one(
        {"frek_id": badge["frek_id"]},
        {"$addToSet": {"stages_completed": "METAMORPHOSE"},
         "$set": {"current_stage": "METAMORPHOSE"}}
    )

    logger.info(f"Recharge {request.badge_id}: +{pack['jetons']}J ({request.pack})")
    tx.pop("_id", None)
    return {"transaction": tx, "new_solde": new_solde}


@jetons_router.post("/paiement")
async def paiement_marchand(
    request: PaiementRequest,
    client: dict = Depends(require_permission("stage")),
):
    badge = await db.badges.find_one({"badge_id": request.badge_id}, {"_id": 0})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {request.badge_id} introuvable")

    solde = badge.get("jetons_solde", 0)
    if solde < request.montant_jetons:
        raise HTTPException(status_code=400, detail=f"Solde insuffisant: {solde}J disponibles, {request.montant_jetons}J requis")

    # Verify marchand exists
    marchand = await db.marchands.find_one({"marchand_id": request.marchand_id}, {"_id": 0})
    if not marchand:
        raise HTTPException(status_code=404, detail=f"Marchand {request.marchand_id} introuvable")

    now = now_iso()
    tx_id = str(uuid.uuid4())[:12]
    new_solde = solde - request.montant_jetons
    montant_eur = request.montant_jetons * JETON_VALUE

    # Debit participant
    await db.badges.update_one(
        {"badge_id": request.badge_id},
        {"$set": {"jetons_solde": new_solde}}
    )

    # Credit marchand
    await db.marchands.update_one(
        {"marchand_id": request.marchand_id},
        {"$inc": {"solde_du": montant_eur}}
    )

    # Record transaction
    tx = {
        "tx_id": tx_id,
        "type": "PAIEMENT",
        "badge_id": request.badge_id,
        "frek_id": badge.get("frek_id"),
        "montant_jetons": request.montant_jetons,
        "montant_eur": montant_eur,
        "pack": None,
        "payment_method": "jeton",
        "marchand_id": request.marchand_id,
        "description": request.description or "Paiement marchand",
        "solde_apres": new_solde,
        "timestamp": now,
        "client_id": client["client_id"],
    }
    await db.transactions.insert_one(tx)
    tx.pop("_id", None)

    logger.info(f"Paiement {request.badge_id}: -{request.montant_jetons}J -> {request.marchand_id}")
    return {"transaction": tx, "new_solde": new_solde}


@jetons_router.get("/solde/{badge_id}")
async def get_solde(badge_id: str):
    badge = await db.badges.find_one({"badge_id": badge_id}, {"_id": 0, "jetons_solde": 1, "badge_id": 1, "prenom": 1})
    if not badge:
        raise HTTPException(status_code=404, detail=f"Badge {badge_id} introuvable")
    return {"badge_id": badge_id, "solde": badge.get("jetons_solde", 0), "jeton_value_eur": JETON_VALUE}


@jetons_router.get("/historique/{badge_id}")
async def get_historique(badge_id: str, page: int = 1, size: int = 50):
    total = await db.transactions.count_documents({"badge_id": badge_id})
    skip = (page - 1) * size
    txs = await db.transactions.find(
        {"badge_id": badge_id}, {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(size).to_list(size)
    return {"badge_id": badge_id, "total": total, "transactions": txs}


@jetons_router.post("/remboursement")
async def remboursement_marchand(
    request: RemboursementRequest,
    client: dict = Depends(require_permission("emit")),
):
    marchand = await db.marchands.find_one({"marchand_id": request.marchand_id}, {"_id": 0})
    if not marchand:
        raise HTTPException(status_code=404, detail=f"Marchand {request.marchand_id} introuvable")

    now = now_iso()
    await db.marchands.update_one(
        {"marchand_id": request.marchand_id},
        {"$inc": {"solde_du": -request.montant_eur},
         "$set": {"dernier_remboursement": now}}
    )

    tx = {
        "tx_id": str(uuid.uuid4())[:12],
        "type": "REMBOURSEMENT_MARCHAND",
        "badge_id": None,
        "frek_id": None,
        "montant_jetons": 0,
        "montant_eur": request.montant_eur,
        "marchand_id": request.marchand_id,
        "description": f"Remboursement SEPA J+3",
        "timestamp": now,
        "client_id": client["client_id"],
    }
    await db.transactions.insert_one(tx)
    tx.pop("_id", None)
    return {"transaction": tx}


@jetons_router.get("/stats")
async def jetons_stats():
    pipeline_recharge = [
        {"$match": {"type": "RECHARGE"}},
        {"$group": {"_id": None, "total_jetons": {"$sum": "$montant_jetons"}, "total_eur": {"$sum": "$montant_eur"}, "count": {"$sum": 1}}},
    ]
    pipeline_paiement = [
        {"$match": {"type": "PAIEMENT"}},
        {"$group": {"_id": None, "total_jetons": {"$sum": "$montant_jetons"}, "total_eur": {"$sum": "$montant_eur"}, "count": {"$sum": 1}}},
    ]

    recharge_stats = await db.transactions.aggregate(pipeline_recharge).to_list(1)
    paiement_stats = await db.transactions.aggregate(pipeline_paiement).to_list(1)

    r = recharge_stats[0] if recharge_stats else {"total_jetons": 0, "total_eur": 0, "count": 0}
    p = paiement_stats[0] if paiement_stats else {"total_jetons": 0, "total_eur": 0, "count": 0}

    r.pop("_id", None)
    p.pop("_id", None)

    return {
        "jeton_value_eur": JETON_VALUE,
        "recharges": r,
        "paiements": p,
        "float_actif": r.get("total_eur", 0) - p.get("total_eur", 0),
        "jetons_en_circulation": r.get("total_jetons", 0) - p.get("total_jetons", 0),
    }


# --- Marchands ---
class MarchandCreate(BaseModel):
    marchand_id: str
    nom: str
    stand: Optional[str] = None
    type_stand: Optional[str] = None


@jetons_router.post("/marchands")
async def create_marchand(
    request: MarchandCreate,
    client: dict = Depends(require_permission("emit")),
):
    existing = await db.marchands.find_one({"marchand_id": request.marchand_id})
    if existing:
        raise HTTPException(status_code=409, detail="Marchand existe deja")

    doc = {
        "marchand_id": request.marchand_id,
        "nom": request.nom,
        "stand": request.stand,
        "type_stand": request.type_stand,
        "solde_du": 0.0,
        "dernier_remboursement": None,
        "created_at": now_iso(),
    }
    await db.marchands.insert_one(doc)
    doc.pop("_id", None)
    return doc


@jetons_router.get("/marchands")
async def list_marchands():
    marchands = await db.marchands.find({}, {"_id": 0}).to_list(200)
    return {"marchands": marchands}
