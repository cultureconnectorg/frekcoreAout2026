"""
FREK v1 — Endpoints Stages (append-only)
"""
from fastapi import APIRouter, HTTPException, Depends

from .models import StageRequest, StageResponse, FrekStage, STAGE_ORDER
from .auth import require_permission, db as _auth_db
from .utils import now_iso

stages_router = APIRouter(tags=["FREK v1 Stages"])

db = None


def set_db(database):
    global db
    db = database


@stages_router.post("/identity/{frek_id}/stage", response_model=StageResponse)
async def record_stage(
    frek_id: str,
    request: StageRequest,
    client: dict = Depends(require_permission("stage")),
):
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]},
        {"_id": 0}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    # Get next sequence number
    last_stage = await db.frek_stages.find_one(
        {"frek_id": frek_id},
        {"_id": 0, "sequence": 1},
        sort=[("sequence", -1)]
    )
    next_seq = (last_stage["sequence"] + 1) if last_stage else 1

    now = now_iso()
    import uuid
    stage_id = str(uuid.uuid4())

    stage_doc = {
        "id": stage_id,
        "frek_id": frek_id,
        "stage": request.stage.value,
        "fingerprint": request.fingerprint,
        "metadata_hash": None,
        "timestamp": now,
        "source": request.source,
        "sequence": next_seq,
        "client_id": client["client_id"],
    }

    if request.metadata:
        import hashlib, json
        stage_doc["metadata_hash"] = hashlib.sha256(
            json.dumps(request.metadata, sort_keys=True).encode()
        ).hexdigest()

    await db.frek_stages.insert_one(stage_doc)

    # Update identity with new stage
    stages_completed = identity.get("stages_completed", [])
    if request.stage.value not in stages_completed:
        stages_completed.append(request.stage.value)

    # Current stage = highest stage reached
    current_stage = max(
        stages_completed,
        key=lambda s: STAGE_ORDER.get(FrekStage(s), 0)
    )

    await db.frek_identities.update_one(
        {"frek_id": frek_id},
        {"$set": {
            "current_stage": current_stage,
            "stages_completed": stages_completed,
        }}
    )

    return StageResponse(
        id=stage_id,
        frek_id=frek_id,
        stage=request.stage.value,
        fingerprint=request.fingerprint,
        sequence=next_seq,
        timestamp=now,
        source=request.source,
    )


@stages_router.get("/identity/{frek_id}/stages")
async def get_stages(
    frek_id: str,
    client: dict = Depends(require_permission("stage")),
):
    identity = await db.frek_identities.find_one(
        {"frek_id": frek_id, "client_id": client["client_id"]},
        {"_id": 0, "frek_id": 1}
    )
    if not identity:
        raise HTTPException(status_code=404, detail=f"FREK-ID {frek_id} introuvable")

    stages = await db.frek_stages.find(
        {"frek_id": frek_id}, {"_id": 0}
    ).sort("sequence", 1).to_list(1000)

    return {
        "frek_id": frek_id,
        "count": len(stages),
        "stages": stages,
    }
