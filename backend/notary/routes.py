"""FREK Notary — API endpoints"""
import base64
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query

from frek_v1.auth import get_current_client, require_permission

from .chain import FrekChain
from .anchor import OTSAnchor
from .source import get_manager as get_source_manager
from .models import (
    NotarizeRequest,
    BlockResponse,
    ProofResponse,
    ChainStatusResponse,
    VerifyResponse,
)

logger = logging.getLogger("frek.notary.routes")

notary_router = APIRouter(prefix="/notary", tags=["FREK Notary — Notaire Culturel Tech"])

_chain: Optional[FrekChain] = None
_anchor: Optional[OTSAnchor] = None


def set_db(database):
    global _chain, _anchor
    _chain = FrekChain(database)
    _anchor = OTSAnchor(database, _chain)


def get_chain() -> FrekChain:
    if _chain is None:
        raise RuntimeError("Notary chain not initialized")
    return _chain


def get_anchor() -> OTSAnchor:
    if _anchor is None:
        raise RuntimeError("Notary anchor not initialized")
    return _anchor


def _to_block_response(blk: dict) -> BlockResponse:
    return BlockResponse(
        height=blk["height"],
        prev_hash=blk["prev_hash"],
        payload_type=blk["payload_type"],
        payload_id=blk["payload_id"],
        payload_hash=blk["payload_hash"],
        block_hash=blk["block_hash"],
        timestamp=blk["timestamp"],
        metadata=blk.get("metadata") or {},
        event_id=blk.get("event_id"),
        spec_version=blk.get("spec_version", "1.0.0"),
        btc_anchored=blk.get("btc_anchored", False),
        btc_block_height=blk.get("btc_block_height"),
        btc_attestation_time=blk.get("btc_attestation_time"),
    )


@notary_router.post("/notarize", response_model=BlockResponse)
async def notarize(
    request: NotarizeRequest,
    background: BackgroundTasks,
    client: dict = Depends(require_permission("emit")),
):
    """Inscrit un evenement dans la FREK-Chain (temps reel, gratuit)."""
    chain = get_chain()
    anchor = get_anchor()
    blk = await chain.append_block(
        payload_type=request.payload_type,
        payload_id=request.payload_id,
        payload_data=request.payload_data,
        metadata={**(request.metadata or {}), "client_id": client["client_id"]},
    )
    background.add_task(anchor.submit_block, blk["height"])
    return _to_block_response(blk)


@notary_router.get("/block/{height}", response_model=BlockResponse)
async def get_block_by_height(height: int):
    blk = await get_chain().get_block(height)
    if not blk:
        raise HTTPException(status_code=404, detail=f"Block {height} introuvable")
    return _to_block_response(blk)


@notary_router.get("/source/health")
async def source_health():
    """Etat de la source d'ancrage primaire (nœud Bitcoin Core) avec fallback OTS.

    Public — destine au dashboard interne. Aucun secret n'est expose.
    Reponse :
        - source : "node" (nœud connecte) | "ots" (fallback)
        - configured : booleen, indique si BITCOIN_RPC_* est defini
        - tip_height / tip_hash / tip_time : si node connecte
        - reason : message court si non connecte
    """
    return await get_source_manager().get_health()


@notary_router.get("/blocks", response_model=list[BlockResponse])
async def list_blocks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_id: Optional[str] = Query(None, description="Filtre sur event_id"),
    payload_type: Optional[str] = Query(None, description="Filtre sur payload_type"),
):
    chain = get_chain()
    query = {}
    if event_id:
        query["event_id"] = event_id
    if payload_type:
        query["payload_type"] = payload_type
    cursor = (
        chain.blocks.find(query, {"_id": 0, "ots_proof": 0, "payload_data": 0})
        .sort("height", -1)
        .skip(offset)
        .limit(limit)
    )
    blocks = await cursor.to_list(limit)
    return [_to_block_response(b) for b in blocks]


@notary_router.get("/proof/{payload_id}", response_model=ProofResponse)
async def get_proof(payload_id: str):
    """Retourne la preuve cryptographique pour un FREK-ID (ou autre payload_id)."""
    chain = get_chain()
    anchor = get_anchor()
    blocks = await chain.get_blocks_for_payload(payload_id)
    if not blocks:
        raise HTTPException(status_code=404, detail=f"Aucun block pour payload_id={payload_id}")
    blk = blocks[0]
    proof = await chain.chain_proof(blk["height"])
    ots_data = await anchor.get_proof_b64(blk["height"])
    btc_block_height = ots_data.get("btc_block_height")
    verification_url = (
        f"https://mempool.space/block-height/{btc_block_height}"
        if btc_block_height else None
    )
    return ProofResponse(
        payload_id=payload_id,
        block=_to_block_response(blk),
        chain_proof=proof,
        ots_proof_b64=ots_data.get("ots_proof_b64"),
        btc_anchored=ots_data.get("btc_anchored", False),
        btc_attestation=(
            {
                "btc_block_height": btc_block_height,
                "calendars": ots_data.get("ots_calendars", []),
            }
            if ots_data.get("btc_anchored")
            else None
        ),
        verification_url=verification_url,
    )


@notary_router.get("/proof/{payload_id}/ots")
async def download_ots_proof(payload_id: str):
    """Telecharge la preuve OpenTimestamps brute (binaire .ots verifiable)."""
    from fastapi.responses import Response
    chain = get_chain()
    anchor = get_anchor()
    blocks = await chain.get_blocks_for_payload(payload_id)
    if not blocks:
        raise HTTPException(status_code=404, detail="Payload introuvable")
    blk = blocks[0]
    data = await anchor.get_proof_b64(blk["height"])
    b64 = data.get("ots_proof_b64")
    if not b64:
        raise HTTPException(status_code=404, detail="Preuve OTS pas encore disponible")
    raw = base64.b64decode(b64)
    return Response(
        content=raw,
        media_type="application/vnd.opentimestamps.ots",
        headers={
            "Content-Disposition": f'attachment; filename="frek-{payload_id}.ots"'
        },
    )


@notary_router.post("/anchor/sweep")
async def anchor_sweep(
    max_blocks: int = Query(50, ge=1, le=500),
    client: dict = Depends(require_permission("emit")),
):
    """Sweep manuel : soumet tous les blocks non ancres."""
    return await get_anchor().submit_pending_blocks(max_blocks=max_blocks)


@notary_router.post("/anchor/upgrade")
async def anchor_upgrade(
    max_blocks: int = Query(50, ge=1, le=500),
    client: dict = Depends(require_permission("emit")),
):
    """Tente l'upgrade Bitcoin pour les blocks ancres en attente."""
    return await get_anchor().upgrade_pending(max_blocks=max_blocks)


@notary_router.post("/anchor/{height}")
async def anchor_block_now(
    height: int,
    client: dict = Depends(require_permission("emit")),
):
    """Force la soumission OTS d'un block specifique."""
    res = await get_anchor().submit_block(height)
    if not res.get("ok"):
        raise HTTPException(status_code=502, detail=res)
    return res


@notary_router.get("/chain/status", response_model=ChainStatusResponse)
async def chain_status():
    chain = get_chain()
    state = await chain._get_state()
    pending = await chain.blocks.count_documents(
        {"ots_submitted": True, "btc_anchored": False}
    )
    integrity = await chain.verify_chain(limit=200)
    events = await chain.blocks.distinct("event_id")
    events = [e for e in events if e]
    from .chain import FREK_SPEC_VERSION
    return ChainStatusResponse(
        height=state.get("height", 0),
        spec_version=FREK_SPEC_VERSION,
        genesis_at=state.get("genesis_at"),
        last_block_at=state.get("last_block_at"),
        last_block_hash=state.get("last_block_hash", "0" * 64),
        total_anchored=state.get("total_anchored", 0),
        total_btc_confirmed=state.get("total_btc_confirmed", 0),
        pending_anchors=pending,
        last_anchor_at=state.get("last_anchor_at"),
        integrity_ok=bool(integrity.get("valid")),
        calendars=get_anchor().calendars,
        events=sorted(events),
    )


@notary_router.get("/chain/events")
async def chain_events_summary():
    """Resume par event_id : nombre de blocs, types, derniers blocks."""
    chain = get_chain()
    pipeline = [
        {"$match": {"event_id": {"$ne": None}}},
        {"$group": {
            "_id": "$event_id",
            "blocks": {"$sum": 1},
            "btc_anchored": {"$sum": {"$cond": ["$btc_anchored", 1, 0]}},
            "first_block_at": {"$min": "$timestamp"},
            "last_block_at": {"$max": "$timestamp"},
            "payload_types": {"$addToSet": "$payload_type"},
        }},
        {"$sort": {"last_block_at": -1}},
    ]
    rows = await chain.blocks.aggregate(pipeline).to_list(500)
    return {
        "events": [
            {
                "event_id": r["_id"],
                "blocks": r["blocks"],
                "btc_anchored": r["btc_anchored"],
                "first_block_at": r["first_block_at"],
                "last_block_at": r["last_block_at"],
                "payload_types": sorted(r["payload_types"]),
            }
            for r in rows
        ],
    }


@notary_router.get("/chain/verify", response_model=VerifyResponse)
async def chain_verify(limit: Optional[int] = Query(None, ge=1, le=10000)):
    res = await get_chain().verify_chain(limit=limit)
    chain = get_chain()
    state = await chain._get_state()
    return VerifyResponse(
        valid=res["valid"],
        height=state.get("height", 0),
        blocks_checked=res["blocks_checked"],
        first_invalid_height=res.get("first_invalid_height"),
        message=(
            "Chaine FREK integre et inviolable."
            if res["valid"]
            else f"INTEGRITE COMPROMISE - block #{res.get('first_invalid_height')}"
        ),
    )


@notary_router.get("/health")
async def notary_health():
    chain = get_chain()
    state = await chain._get_state()
    return {
        "status": "ok",
        "module": "FREK Notary — Notaire Culturel Tech",
        "chain_height": state.get("height", 0),
        "calendars": len(get_anchor().calendars),
    }
