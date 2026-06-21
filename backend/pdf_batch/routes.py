"""FREK PDF Batch — routes /api/v1/pdf-batch/*."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from staff.routes import require_staff_perm
from . import service

logger = logging.getLogger("frek.pdf_batch.routes")

pdf_batch_router = APIRouter(prefix="/pdf-batch", tags=["FREK PDF Batch — generation self-service"])

db = None


def set_db(database):
    global db
    db = database


class TemplateOverride(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    footer: Optional[str] = None
    accent_hex: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    verify_base_url: Optional[str] = None


class BatchByEventRequest(BaseModel):
    event: str = Field(..., min_length=2, max_length=64)
    type_badge: Optional[str] = None
    limit: int = Field(200, ge=1, le=1000)
    template: Optional[TemplateOverride] = None


class BatchByIdsRequest(BaseModel):
    badge_ids: list[str] = Field(..., min_length=1, max_length=1000)
    template: Optional[TemplateOverride] = None


@pdf_batch_router.get("/template")
async def get_default_template():
    return service.DEFAULT_TEMPLATE


@pdf_batch_router.post(
    "/by-event",
    dependencies=[Depends(require_staff_perm("view_stats"))],
    responses={200: {"content": {"application/zip": {}}}},
)
async def generate_batch_by_event(req: BatchByEventRequest):
    """Genere un ZIP de PDFs pour tous les badges d'un evenement."""
    q = {"event": req.event}
    if req.type_badge:
        q["type_badge"] = req.type_badge
    cursor = db.badges.find(q, {"_id": 0}).limit(req.limit)
    badges = await cursor.to_list(length=req.limit)
    if not badges:
        raise HTTPException(status_code=404, detail="no_badges_for_event")
    template = req.template.model_dump(exclude_none=True) if req.template else None
    zip_bytes = service.render_batch_zip(badges, template=template)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=frek-badges-{req.event}.zip"},
    )


@pdf_batch_router.post(
    "/by-ids",
    dependencies=[Depends(require_staff_perm("view_stats"))],
    responses={200: {"content": {"application/zip": {}}}},
)
async def generate_batch_by_ids(req: BatchByIdsRequest):
    cursor = db.badges.find({"badge_id": {"$in": req.badge_ids}}, {"_id": 0})
    badges = await cursor.to_list(length=len(req.badge_ids))
    if not badges:
        raise HTTPException(status_code=404, detail="no_badges_found")
    template = req.template.model_dump(exclude_none=True) if req.template else None
    zip_bytes = service.render_batch_zip(badges, template=template)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=frek-badges-batch.zip"},
    )


@pdf_batch_router.get(
    "/events-with-counts",
    dependencies=[Depends(require_staff_perm("view_stats"))],
)
async def events_with_counts(limit: int = Query(50, ge=1, le=200)):
    """Liste les evenements distincts presents dans la collection badges, avec leur compte."""
    pipeline = [
        {"$group": {"_id": "$event", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    out = []
    async for doc in db.badges.aggregate(pipeline):
        out.append({"event": doc["_id"], "count": doc["count"]})
    return {"events": out}
