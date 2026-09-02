"""D3 -- Relationship / Provenance Graph API.

`backend/frek/routes_advanced.py`'s 7 réseau routes (`GET .../reseau`,
`.../reseau/stats`, `.../reseau/node/{id}`, `.../reseau/neighbors/{id}`,
`.../reseau/artiste/{id}`, `.../reseau/lieu/{id}`, `.../reseau/path`) are
UNTOUCHED by this module -- zero lines changed. They remain live exactly
as before (in-memory, unauthenticated) per the explicit instruction
against destructive route migration this state.

This module is the additive, canonical D3 implementation: durable,
authenticated, event-sourced, layer-separated (TRUST vs. CULTURAL),
bounded-traversal-only, and visibility-aware.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from permissions.models import Scope, ScopeType
from proof_engine.evidence_semantics import Claim, ClaimOrigin, Evidence, EvidenceKind
from security.policies import check_rate_limit

from .models import (
    HISTORICAL_NODE_TYPE_TAXONOMY,
    HISTORICAL_RELATION_TAXONOMY,
    Assertion,
    RelationLayer,
    Relationship,
)
from .service import (
    MAX_NEIGHBORS,
    MAX_PATH_DEPTH_HARD_CAP,
    UnknownPredicateError,
    bounded_neighbors,
    bounded_path,
    can_read,
    dedup_key,
    derive_status,
    resolve_layer,
)

logger = logging.getLogger("frek.relationship_graph.routes")

relationship_graph_router = APIRouter(
    prefix="/relationships", tags=["FREK Relationship Graph (D3)"]
)

db = None

# Only origins a human/holder caller may self-assert without admin --
# see routes.py module-level AUTHORITY note on each endpoint below.
_SELF_ASSERTABLE_ORIGINS = {ClaimOrigin.DECLARED}


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.relationships.create_index("relationship_id", unique=True)
    await db.relationships.create_index(
        [("subject_id", 1), ("predicate", 1), ("object_id", 1)]
    )
    await db.relationships.create_index("subject_id")
    await db.relationships.create_index("object_id")
    await db.relationships.create_index("layer")


# ---------- Authorization (same convention as content_binding/creative_lifecycle) ----------


def _admin_or_403(x_admin_key: str) -> None:
    expected = os.environ.get("SECRET_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="invalid_admin_key")


def _is_admin(x_admin_key: str) -> bool:
    expected = os.environ.get("SECRET_KEY")
    return bool(expected) and x_admin_key == expected


async def _session_actor(x_frek_session: Optional[str]) -> Optional[str]:
    if not x_frek_session:
        return None
    from identity_engine import service as identity_service

    return identity_service.verify_session_token(x_frek_session)


async def _require_submit_authority(
    origin: ClaimOrigin, x_frek_session: Optional[str], x_admin_key: str
) -> tuple[Optional[str], str]:
    """AUTHORITY split (mission): SUBMIT CLAIM vs. everything else.

    Any authenticated holder or admin may SUBMIT a self-attested CLAIM
    (origin=DECLARED) -- "I declare this relationship". OBSERVED/
    ATTESTED/COMPUTED/INFERRED origins represent a system or authority
    asserting something on its own account, not a human declaring their
    own intent -- admin-only this state, since no separate attester-role
    or service-identity infrastructure exists yet to authenticate those
    as anything other than admin (same conservative posture D2 already
    took on multi-contributor authorization: real-world plausible, out
    of this state's scope, not invented here)."""
    actor_id = await _session_actor(x_frek_session)
    if origin in _SELF_ASSERTABLE_ORIGINS and actor_id:
        return actor_id, "holder"
    _admin_or_403(x_admin_key)
    return actor_id, "admin"


async def _require_owner_or_admin(
    assertion_actor_id: Optional[str], x_frek_session: Optional[str], x_admin_key: str
) -> tuple[Optional[str], str]:
    """REVOKE authority: the assertion's own actor (self-match) or admin
    -- identical convention to D2's `_require_lifecycle_owner_or_admin`."""
    actor_id = await _session_actor(x_frek_session)
    if actor_id and assertion_actor_id and actor_id == assertion_actor_id:
        return actor_id, "holder"
    _admin_or_403(x_admin_key)
    return actor_id, "admin"


# ---------- Canonical entity reference resolution ----------
# ACTOR != SUBJECT, ACTOR != OBJECT OWNER automatically, and
# NODE_IDENTITY_EQUALS_FREK_ID_ALWAYS=FALSE -- subjects/objects may be any
# addressable registry entity. Recognized types are checked for real
# existence (closing the same "never mint/assume an identifier" gap D1/D2
# already closed for their own single entity kind); an unrecognized type is
# accepted as an opaque external reference, honestly UNCHECKED, not
# silently treated as verified-to-exist.
_RECOGNIZED_ENTITY_TYPES = {"fk_object", "creative_lifecycle", "identity"}


async def _entity_exists(entity_type: Optional[str], entity_id: str) -> Optional[bool]:
    """Returns True/False if `entity_type` is recognized and checkable,
    None if unrecognized (unchecked, not an error -- see module note)."""
    if entity_type == "fk_object":
        doc = await db.fk_objects.find_one(
            {"frek_id": entity_id}, {"_id": 0, "frek_id": 1}
        )
        return doc is not None
    if entity_type == "creative_lifecycle":
        doc = await db.creative_lifecycle_events.find_one(
            {"pre_id": entity_id}, {"_id": 0, "pre_id": 1}
        )
        return doc is not None
    if entity_type == "identity":
        doc = await db.frek_persons.find_one(
            {"frek_id": entity_id}, {"_id": 0, "frek_id": 1}
        )
        return doc is not None
    return None


# ---------- Persistence helpers ----------


async def _load(relationship_id: str) -> Optional[dict]:
    return await db.relationships.find_one(
        {"relationship_id": relationship_id}, {"_id": 0}
    )


async def _load_by_tuple(
    subject_id: str, predicate: str, object_id: str
) -> Optional[dict]:
    return await db.relationships.find_one(
        {"subject_id": subject_id, "predicate": predicate, "object_id": object_id},
        {"_id": 0},
    )


def _parties(doc: dict) -> List[Optional[str]]:
    parties = [doc.get("subject_id"), doc.get("object_id")]
    parties += [a.get("actor_id") for a in doc.get("assertions", [])]
    return parties


def _visible_or_404(doc: dict, actor_id: Optional[str], is_admin: bool) -> dict:
    visibility = Scope.model_validate(doc.get("visibility") or {"type": "global"})
    if not can_read(
        visibility, actor_id=actor_id, is_admin=is_admin, parties=_parties(doc)
    ):
        # 404, not 403: a private relationship's existence is not leaked.
        raise HTTPException(status_code=404, detail="relationship_introuvable")
    return doc


async def _notarize_and_store(relationship: Relationship, *, is_new: bool) -> dict:
    """Best-effort notarization (never blocks), then persists, then
    publishes -- same convention as content_binding/creative_lifecycle."""
    try:
        from notary.service import notarize_event as _notarize_event

        last_assertion = (
            relationship.assertions[-1] if relationship.assertions else None
        )
        await _notarize_event(
            payload_type="relationship",
            payload_id=relationship.relationship_id,
            payload_data={
                "relationship_id": relationship.relationship_id,
                "subject_id": relationship.subject_id,
                "predicate": relationship.predicate,
                "object_id": relationship.object_id,
                "layer": relationship.layer.value,
                "status": relationship.status.value,
            },
            metadata={
                "authority": last_assertion.authority if last_assertion else "admin"
            },
        )
    except Exception:
        logger.warning("relationship notarization failed (non-blocking)", exc_info=True)

    doc = relationship.to_public_dict()
    if is_new:
        await db.relationships.insert_one(dict(doc))
    else:
        await db.relationships.replace_one(
            {"relationship_id": relationship.relationship_id}, dict(doc)
        )

    try:
        from eventbus.bus import default_bus as _event_bus
        from eventbus.producers import build_relationship_event

        _event_bus.publish(build_relationship_event(doc))
    except Exception:
        logger.warning(
            "relationship.recorded event publish failed (non-blocking)", exc_info=True
        )

    return doc


# ---------- POST /relationships ----------


class CreateRelationshipRequest(BaseModel):
    subject_id: str
    subject_type: Optional[str] = None
    predicate: str
    object_id: str
    object_type: Optional[str] = None
    origin: ClaimOrigin
    statement: str
    data: Dict[str, Any] = Field(default_factory=dict)
    visibility: Optional[Scope] = None
    source_event_id: Optional[str] = None
    source_content_binding_id: Optional[str] = None


@relationship_graph_router.post("")
async def create_relationship(
    req: CreateRelationshipRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Creates (or adds an independent assertion to) the canonical
    (subject, predicate, object) relationship slot.

    Idempotent on (subject_id, predicate, object_id, actor_id, origin):
    the SAME actor retrying the SAME assertion returns the existing one
    (test #14). A DIFFERENT actor asserting the same tuple is a genuinely
    new, separately-provenanced Assertion under the same Relationship
    (test #15) -- SAME_SUBJECT_PREDICATE_OBJECT != SAME_ASSERTION."""
    try:
        layer = resolve_layer(req.predicate)
    except UnknownPredicateError as e:
        raise HTTPException(status_code=400, detail=str(e))

    actor_id, authority = await _require_submit_authority(
        req.origin, x_frek_session, x_admin_key
    )

    if not await check_rate_limit(
        scope=actor_id or "admin", action="relationship_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    if req.subject_id == req.object_id and req.subject_type == req.object_type:
        raise HTTPException(status_code=400, detail="subject et object identiques")

    subject_exists = await _entity_exists(req.subject_type, req.subject_id)
    if subject_exists is False:
        raise HTTPException(
            status_code=404, detail=f"subject {req.subject_id} introuvable"
        )
    object_exists = await _entity_exists(req.object_type, req.object_id)
    if object_exists is False:
        raise HTTPException(
            status_code=404, detail=f"object {req.object_id} introuvable"
        )

    if req.source_event_id is not None:
        ev = await db.creative_lifecycle_events.find_one(
            {"event_id": req.source_event_id}, {"_id": 0, "event_id": 1}
        )
        if not ev:
            raise HTTPException(
                status_code=404,
                detail=f"source_event_id {req.source_event_id} introuvable",
            )
    if req.source_content_binding_id is not None:
        cb = await db.content_bindings.find_one(
            {"binding_id": req.source_content_binding_id}, {"_id": 0, "binding_id": 1}
        )
        if not cb:
            raise HTTPException(
                status_code=404,
                detail=f"source_content_binding_id {req.source_content_binding_id} introuvable",
            )

    key = dedup_key(req.subject_id, req.predicate, req.object_id, actor_id, req.origin)
    existing = await _load_by_tuple(req.subject_id, req.predicate, req.object_id)
    if existing:
        for a in existing.get("assertions", []):
            if (
                dedup_key(
                    existing["subject_id"],
                    existing["predicate"],
                    existing["object_id"],
                    a.get("actor_id"),
                    ClaimOrigin(a["claim"]["origin"]),
                )
                == key
            ):
                return {**existing, "deduplicated": True}

    claim = Claim(
        subject_id=existing["relationship_id"] if existing else str(uuid.uuid4()),
        claimant_id=actor_id,
        origin=req.origin,
        statement=req.statement,
        data=req.data,
    )
    evidence_kind = {
        ClaimOrigin.DECLARED: None,
        ClaimOrigin.OBSERVED: EvidenceKind.OBSERVATION,
        ClaimOrigin.ATTESTED: EvidenceKind.ATTESTATION,
        ClaimOrigin.COMPUTED: EvidenceKind.COMPUTATION,
        ClaimOrigin.INFERRED: EvidenceKind.INFERENCE,
    }[req.origin]
    evidence = (
        [
            Evidence(
                subject_id=claim.subject_id,
                kind=evidence_kind,
                data=req.data,
                produced_by=actor_id or authority,
            )
        ]
        if evidence_kind
        else []
    )
    assertion = Assertion(
        assertion_id=str(uuid.uuid4()),
        claim=claim,
        evidence=evidence,
        actor_id=actor_id,
        authority=authority,
    )

    if existing:
        relationship = Relationship.model_validate(existing)
        relationship.assertions.append(assertion)
    else:
        relationship = Relationship(
            relationship_id=claim.subject_id,
            subject_id=req.subject_id,
            subject_type=req.subject_type,
            predicate=req.predicate,
            object_id=req.object_id,
            object_type=req.object_type,
            layer=layer,
            visibility=req.visibility or Scope(type=ScopeType.GLOBAL),
            assertions=[assertion],
            source_event_id=req.source_event_id,
            source_content_binding_id=req.source_content_binding_id,
        )
    relationship.status = derive_status(
        relationship.layer,
        relationship.assertions,
        verified=bool(relationship.verified_at),
    )

    doc = await _notarize_and_store(relationship, is_new=existing is None)
    return {**doc, "deduplicated": False}


# ---------- GET /relationships/{relationship_id} ----------


@relationship_graph_router.get("/historical-taxonomy")
async def get_historical_taxonomy():
    """Public, read-only record of the historical 5 node types / 17
    relation types and their disposition -- HISTORICAL_TAXONOMY_MAPPED."""
    return {
        "node_types": {
            k: {**v, "disposition": v["disposition"].value}
            for k, v in HISTORICAL_NODE_TYPE_TAXONOMY.items()
        },
        "relation_types": {
            k: {**v, "disposition": v["disposition"].value}
            for k, v in HISTORICAL_RELATION_TAXONOMY.items()
        },
    }


@relationship_graph_router.get("/{relationship_id}")
async def get_relationship(
    relationship_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    doc = await _load(relationship_id)
    if not doc:
        raise HTTPException(status_code=404, detail="relationship_introuvable")
    actor_id = await _session_actor(x_frek_session)
    return _visible_or_404(doc, actor_id, _is_admin(x_admin_key))


@relationship_graph_router.get("/{relationship_id}/history")
async def get_relationship_history(
    relationship_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Full assertion history, including revoked ones -- history is
    never destroyed (test #16)."""
    doc = await _load(relationship_id)
    if not doc:
        raise HTTPException(status_code=404, detail="relationship_introuvable")
    actor_id = await _session_actor(x_frek_session)
    doc = _visible_or_404(doc, actor_id, _is_admin(x_admin_key))
    return {"relationship_id": relationship_id, "assertions": doc.get("assertions", [])}


# ---------- neighbors / subject / object (bounded) ----------


async def _visible_edges(actor_id: Optional[str], is_admin: bool, cursor) -> List[dict]:
    out = []
    async for doc in cursor:
        doc.pop("_id", None)
        visibility = Scope.model_validate(doc.get("visibility") or {"type": "global"})
        if can_read(
            visibility, actor_id=actor_id, is_admin=is_admin, parties=_parties(doc)
        ):
            out.append(doc)
    return out


@relationship_graph_router.get("/entity/{entity_id}/neighbors")
async def get_neighbors(
    entity_id: str,
    direction: str = Query("both", enum=["outgoing", "incoming", "both"]),
    limit: int = Query(MAX_NEIGHBORS, ge=1, le=MAX_NEIGHBORS),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    actor_id = await _session_actor(x_frek_session)
    is_admin = _is_admin(x_admin_key)
    cursor = db.relationships.find(
        {"$or": [{"subject_id": entity_id}, {"object_id": entity_id}]}, {"_id": 0}
    ).limit(limit * 2)
    edges = await _visible_edges(actor_id, is_admin, cursor)
    neighbors = bounded_neighbors(edges, entity_id, direction=direction, limit=limit)
    return {
        "entity_id": entity_id,
        "direction": direction,
        "neighbors_count": len(neighbors),
        "neighbors": neighbors,
    }


@relationship_graph_router.get("/entity/{entity_id}/outgoing")
async def get_outgoing(
    entity_id: str,
    limit: int = Query(MAX_NEIGHBORS, ge=1, le=MAX_NEIGHBORS),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    actor_id = await _session_actor(x_frek_session)
    is_admin = _is_admin(x_admin_key)
    cursor = db.relationships.find({"subject_id": entity_id}, {"_id": 0}).limit(limit)
    edges = await _visible_edges(actor_id, is_admin, cursor)
    return {"entity_id": entity_id, "count": len(edges), "relationships": edges[:limit]}


@relationship_graph_router.get("/entity/{entity_id}/incoming")
async def get_incoming(
    entity_id: str,
    limit: int = Query(MAX_NEIGHBORS, ge=1, le=MAX_NEIGHBORS),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    actor_id = await _session_actor(x_frek_session)
    is_admin = _is_admin(x_admin_key)
    cursor = db.relationships.find({"object_id": entity_id}, {"_id": 0}).limit(limit)
    edges = await _visible_edges(actor_id, is_admin, cursor)
    return {"entity_id": entity_id, "count": len(edges), "relationships": edges[:limit]}


@relationship_graph_router.get("/traverse/path")
async def get_path(
    start_id: str = Query(...),
    end_id: str = Query(...),
    max_depth: int = Query(6, ge=1, le=MAX_PATH_DEPTH_HARD_CAP),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Bounded BFS path (UNBOUNDED_GRAPH_TRAVERSAL=FALSE) -- `max_depth`
    is hard-capped at MAX_PATH_DEPTH_HARD_CAP by FastAPI's own
    Query(..., le=...) validation, mirroring the historical route's
    identical 1-10 bound."""
    actor_id = await _session_actor(x_frek_session)
    is_admin = _is_admin(x_admin_key)
    cursor = db.relationships.find({}, {"_id": 0})
    edges = await _visible_edges(actor_id, is_admin, cursor)
    path = bounded_path(edges, start_id, end_id, max_depth=max_depth)
    if path is None:
        return {"start_id": start_id, "end_id": end_id, "path_found": False}
    return {"start_id": start_id, "end_id": end_id, "path_found": True, "path": path}


# ---------- verify / revoke ----------


class VerifyRequest(BaseModel):
    note: Optional[str] = None


@relationship_graph_router.post("/{relationship_id}/verify")
async def verify_relationship(
    relationship_id: str,
    req: VerifyRequest,
    x_admin_key: str = Header(default=""),
):
    """VERIFY action -- admin-only, TRUST-layer only
    (VERIFIED_RELATION_EQUALS_INFERRED_RELATION=FALSE structurally: a
    CULTURAL-layer relationship is rejected here with 409, not silently
    accepted and then hidden behind derive_status's own refusal)."""
    _admin_or_403(x_admin_key)
    doc = await _load(relationship_id)
    if not doc:
        raise HTTPException(status_code=404, detail="relationship_introuvable")
    if doc["layer"] != RelationLayer.TRUST.value:
        raise HTTPException(
            status_code=409, detail="seules les relations TRUST sont verifiables"
        )

    relationship = Relationship.model_validate(doc)
    relationship.verified_at = datetime.now(timezone.utc).isoformat()
    relationship.verified_by = "admin"
    relationship.status = derive_status(
        relationship.layer, relationship.assertions, verified=True
    )
    stored = await _notarize_and_store(relationship, is_new=False)
    return stored


class RevokeRequest(BaseModel):
    assertion_id: str
    reason: Optional[str] = None


@relationship_graph_router.post("/{relationship_id}/revoke")
async def revoke_assertion(
    relationship_id: str,
    req: RevokeRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Revokes one Assertion -- never deletes it, never deletes the
    Relationship. History is preserved (test #16): the revoked
    Assertion stays in `assertions` with `revoked_at` set."""
    doc = await _load(relationship_id)
    if not doc:
        raise HTTPException(status_code=404, detail="relationship_introuvable")

    target = next(
        (a for a in doc.get("assertions", []) if a["assertion_id"] == req.assertion_id),
        None,
    )
    if not target:
        raise HTTPException(status_code=404, detail="assertion_introuvable")

    await _require_owner_or_admin(target.get("actor_id"), x_frek_session, x_admin_key)

    relationship = Relationship.model_validate(doc)
    for a in relationship.assertions:
        if a.assertion_id == req.assertion_id:
            a.revoked_at = datetime.now(timezone.utc).isoformat()
            a.revoked_reason = req.reason
    relationship.status = derive_status(
        relationship.layer,
        relationship.assertions,
        verified=bool(relationship.verified_at),
    )
    stored = await _notarize_and_store(relationship, is_new=False)
    return stored
