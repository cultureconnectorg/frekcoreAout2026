"""D2 — Creative Lifecycle API.

`backend/frek/routes.py`'s `POST /genesis`, `POST /workshop` are
UNTOUCHED by this module — zero lines changed. They remain live exactly
as before (in-memory, unauthenticated, minting their own `pre_id`
counter) per the explicit instruction against destructive route
migration this state.

This module is the additive, canonical D2 implementation: durable,
authenticated, event-sourced (history never destroyed), and structurally
separate from `frek_v1`'s participant/badge lifecycle that happens to
share the same 5-word vocabulary (see `models.py`'s module docstring for
the verified collision).
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from proof_engine.evidence_semantics import Claim, ClaimOrigin, Evidence, EvidenceKind
from security.policies import check_rate_limit

from .models import ContentBindingRef, LifecycleEvent, LifecycleStage
from .service import (
    can_declare_legacy,
    can_emit,
    can_metamorphose,
    can_start_workshop,
    coherence_score,
    latest_stage,
)

logger = logging.getLogger("frek.creative_lifecycle.routes")

creative_lifecycle_router = APIRouter(
    prefix="/creative-lifecycle", tags=["FREK Creative Lifecycle (D2)"]
)

db = None

MIN_CONTENT_BYTES = 1000
MAX_CONTENT_BYTES = 25 * 1024 * 1024


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.creative_lifecycle_events.create_index("event_id", unique=True)
    await db.creative_lifecycle_events.create_index([("pre_id", 1), ("sequence", 1)])
    await db.creative_lifecycle_events.create_index(
        [("pre_id", 1), ("stage", 1), ("content_binding_ref.exact_hash", 1)]
    )


# ---------- Authorization (same convention as content_binding/routes.py:
# _admin_or_403 / _is_holder / _holder_or_admin — deliberately not shared
# code, each module keeps this small and independently auditable) ----------


def _admin_or_403(x_admin_key: str):
    expected = os.environ.get("SECRET_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="invalid_admin_key")


async def _session_actor(x_frek_session: Optional[str]) -> Optional[str]:
    if not x_frek_session:
        return None
    from identity_engine import service as identity_service

    return identity_service.verify_session_token(x_frek_session)


async def _require_actor_or_admin(
    x_frek_session: Optional[str], x_admin_key: str
) -> tuple[Optional[str], str]:
    """GENESIS's own authority requirement: any authenticated
    identity_engine holder may declare their own intent (self-attested,
    matches the historical 'l'artiste declare' framing directly), or
    admin. Returns (actor_id, authority)."""
    actor_id = await _session_actor(x_frek_session)
    if actor_id:
        return actor_id, "holder"
    _admin_or_403(x_admin_key)
    return None, "admin"


async def _require_lifecycle_owner_or_admin(
    genesis_actor_id: Optional[str],
    x_frek_session: Optional[str],
    x_admin_key: str,
) -> tuple[Optional[str], str]:
    """Authority to progress an EXISTING lifecycle: the GENESIS actor
    (self-match — the same convention D1 uses for a session that IS the
    subject) or admin. Broader multi-contributor authorization
    (someone other than the GENESIS actor legitimately contributing to
    WORKSHOP) is real-world plausible but out of this state's scope —
    that is provenance-graph territory (D3's CREATED_BY/CONTRIBUTED_BY
    relations), not invented here. CONTRIBUTION != OWNERSHIP either way:
    this check is about who may RECORD an event, never about rights."""
    actor_id = await _session_actor(x_frek_session)
    if actor_id and genesis_actor_id and actor_id == genesis_actor_id:
        return actor_id, "holder"
    # Either no session, or the session doesn't match the GENESIS actor
    # (including when GENESIS was admin-authored, genesis_actor_id is
    # None, and no holder session can ever self-match it) -- only admin
    # may progress the lifecycle in that case.
    _admin_or_403(x_admin_key)
    return actor_id, "admin"


# ---------- Shared persistence helpers ----------


async def _load_events(pre_id: str) -> list:
    cursor = db.creative_lifecycle_events.find({"pre_id": pre_id}, {"_id": 0}).sort(
        "sequence", 1
    )
    return await cursor.to_list(2000)


def _resolve_fk_frek_id(events: list) -> Optional[str]:
    """The most recently assigned fk_frek_id, scanning from latest to
    earliest — NOT just the latest event's own field, since a later
    METAMORPHOSE re-entry (see models.py's module docstring finding)
    leaves fk_frek_id unset on that event while the object's real FREK
    Object identity, once assigned at an earlier EMISSION, is never
    revoked by re-entering METAMORPHOSE."""
    for ev in reversed(events):
        if ev.get("fk_frek_id"):
            return ev["fk_frek_id"]
    return None


async def _next_sequence(pre_id: str) -> int:
    last = await db.creative_lifecycle_events.find_one(
        {"pre_id": pre_id}, {"_id": 0, "sequence": 1}, sort=[("sequence", -1)]
    )
    return (last["sequence"] + 1) if last else 1


async def _notarize_and_store(event: LifecycleEvent) -> dict:
    """Best-effort notarization (never blocks the event's own creation —
    same convention as content_binding/routes.py and every other
    mutation in this codebase), then persists. Returns the stored dict."""
    try:
        from notary.service import notarize_event as _notarize_event

        blk = await _notarize_event(
            payload_type="creative_lifecycle",
            payload_id=event.event_id,
            payload_data={
                "event_id": event.event_id,
                "pre_id": event.pre_id,
                "stage": event.stage.value,
                "sequence": event.sequence,
                "fk_frek_id": event.fk_frek_id,
            },
            metadata={"authority": event.authority},
        )
        if blk:
            event.proof_state = "local_proof"
            event.block_height = blk.get("height")
            event.block_hash = blk.get("block_hash")
    except Exception:
        logger.warning(
            "creative_lifecycle notarization failed (non-blocking, stays "
            "proof_state=fingerprint)",
            exc_info=True,
        )

    doc = event.to_public_dict()
    await db.creative_lifecycle_events.insert_one(dict(doc))

    try:
        from eventbus.bus import default_bus as _event_bus
        from eventbus.producers import build_creative_lifecycle_event

        _event_bus.publish(build_creative_lifecycle_event(doc))
    except Exception:
        logger.warning(
            "creative_lifecycle.recorded event publish failed (non-blocking)",
            exc_info=True,
        )

    return doc


async def _compute_binding_ref(content_bytes: bytes) -> tuple[ContentBindingRef, list]:
    """Reuses D1's real extraction functions verbatim
    (D2_CONSUMES_D1=TRUE, D2_REIMPLEMENTS_D1=FALSE) — never recomputes
    the DSP pipeline itself."""
    from content_binding.extraction import (
        FingerprintExtractionError,
        compute_signal_fingerprint,
        exact_hash,
    )
    from content_binding.models import EXACT_HASH_ALGORITHM_ID

    content_hash = exact_hash(content_bytes)
    try:
        fingerprint = await compute_signal_fingerprint(content_bytes)
    except FingerprintExtractionError as e:
        raise HTTPException(status_code=400, detail=f"Contenu illisible: {e}")

    ref = ContentBindingRef(
        exact_hash=content_hash,
        exact_hash_algorithm=EXACT_HASH_ALGORITHM_ID,
        signal_fingerprint_algorithm=fingerprint.algorithm,
        signal_fingerprint_algorithm_version=fingerprint.algorithm_version,
        signal_fingerprint_dimensions=fingerprint.dimensions,
    )
    return ref, fingerprint.vector


# ---------- GENESIS ----------


class GenesisRequest(BaseModel):
    concept: Optional[str] = None
    lieu: Optional[str] = None
    description: Optional[str] = None


@creative_lifecycle_router.post("/genesis")
async def start_genesis(
    request: GenesisRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """STADE 1 — GENESIS. Declares creative intent before any finished
    work exists. Mints a provisional `pre_id` — NEVER a FREK-ID.

    Never claims legal authorship, ownership, or absolute priority
    (D6/D2 invariant) — the resulting Claim's `statement` says exactly
    what happened and nothing more.
    """
    actor_id, authority = await _require_actor_or_admin(x_frek_session, x_admin_key)

    if not await check_rate_limit(
        scope=actor_id or "admin", action="creative_lifecycle_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    pre_id = f"PRE-{uuid.uuid4().hex}"
    intention = request.model_dump(exclude_none=True)

    claim = Claim(
        subject_id=pre_id,
        claimant_id=actor_id,
        origin=ClaimOrigin.DECLARED,
        statement=(
            f"Actor declared creative intent for {pre_id}"
            + (f": {intention}" if intention else ".")
        ),
        data={"intention": intention},
    )

    event = LifecycleEvent(
        event_id=str(uuid.uuid4()),
        pre_id=pre_id,
        stage=LifecycleStage.GENESIS,
        sequence=1,
        actor_id=actor_id,
        authority=authority,
        claim=claim,
        evidence=[],
        data={"intention": intention},
    )
    doc = await _notarize_and_store(event)
    return doc


# ---------- WORKSHOP ----------


@creative_lifecycle_router.post("/{pre_id}/workshop")
async def add_workshop_version(
    pre_id: str,
    content: UploadFile = File(...),
    notes: Optional[str] = Form(default=None),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """STADE 2 — WORKSHOP. Repeatable. Rejected once the lifecycle has
    moved strictly past WORKSHOP (`service.can_start_workshop`)."""
    events = await _load_events(pre_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"{pre_id} introuvable")
    genesis_actor_id = events[0].get("actor_id")

    current = latest_stage(events)
    if not can_start_workshop(current):
        raise HTTPException(
            status_code=409,
            detail=f"WORKSHOP non autorise depuis le stade actuel ({current})",
        )

    actor_id, authority = await _require_lifecycle_owner_or_admin(
        genesis_actor_id, x_frek_session, x_admin_key
    )
    if not await check_rate_limit(
        scope=actor_id or "admin", action="creative_lifecycle_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    content_bytes = await content.read()
    if len(content_bytes) < MIN_CONTENT_BYTES:
        raise HTTPException(status_code=400, detail="Contenu trop petit")
    if len(content_bytes) > MAX_CONTENT_BYTES:
        raise HTTPException(status_code=400, detail="Contenu trop grand (max 25MB)")

    binding_ref, vector = await _compute_binding_ref(content_bytes)

    # Idempotency: identical content already submitted at this stage for
    # this pre_id -> return the existing event.
    existing = next(
        (
            e
            for e in events
            if e["stage"] == LifecycleStage.WORKSHOP.value
            and (e.get("content_binding_ref") or {}).get("exact_hash")
            == binding_ref.exact_hash
        ),
        None,
    )
    if existing:
        return {**existing, "deduplicated": True}

    workshop_count = sum(
        1 for e in events if e["stage"] == LifecycleStage.WORKSHOP.value
    )
    evidence = [
        Evidence(
            subject_id=pre_id,
            kind=EvidenceKind.COMPUTATION,
            data={
                "algorithm": binding_ref.exact_hash_algorithm,
                "value": binding_ref.exact_hash,
            },
            produced_by=actor_id or authority,
        )
    ]
    claim = Claim(
        subject_id=pre_id,
        claimant_id=actor_id,
        origin=ClaimOrigin.COMPUTED,
        statement=f"WORKSHOP version {workshop_count + 1} submitted for {pre_id}.",
        data={"notes": notes, "exact_hash": binding_ref.exact_hash},
    )
    event = LifecycleEvent(
        event_id=str(uuid.uuid4()),
        pre_id=pre_id,
        stage=LifecycleStage.WORKSHOP,
        sequence=await _next_sequence(pre_id),
        actor_id=actor_id,
        authority=authority,
        claim=claim,
        evidence=evidence,
        content_binding_ref=binding_ref,
        data={"notes": notes, "signal_vector": vector},
    )
    doc = await _notarize_and_store(event)
    return {**doc, "deduplicated": False}


# ---------- METAMORPHOSE ----------


@creative_lifecycle_router.post("/{pre_id}/metamorphose")
async def submit_metamorphose(
    pre_id: str,
    content: UploadFile = File(...),
    notes: Optional[str] = Form(default=None),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """STADE 3 — METAMORPHOSE. Historically unguarded beyond the pre_id
    existing (`service.can_metamorphose`) — preserved, not tightened.
    Computes a coherence score against prior WORKSHOP versions."""
    events = await _load_events(pre_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"{pre_id} introuvable")
    genesis_actor_id = events[0].get("actor_id")

    current = latest_stage(events)
    if not can_metamorphose(current):
        raise HTTPException(status_code=409, detail="METAMORPHOSE non autorise")

    actor_id, authority = await _require_lifecycle_owner_or_admin(
        genesis_actor_id, x_frek_session, x_admin_key
    )
    if not await check_rate_limit(
        scope=actor_id or "admin", action="creative_lifecycle_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    content_bytes = await content.read()
    if len(content_bytes) < MIN_CONTENT_BYTES:
        raise HTTPException(status_code=400, detail="Contenu trop petit")
    if len(content_bytes) > MAX_CONTENT_BYTES:
        raise HTTPException(status_code=400, detail="Contenu trop grand (max 25MB)")

    binding_ref, vector = await _compute_binding_ref(content_bytes)

    workshop_vectors = [
        e["data"]["signal_vector"]
        for e in events
        if e["stage"] == LifecycleStage.WORKSHOP.value
        and e.get("data", {}).get("signal_vector")
    ]
    score = coherence_score(workshop_vectors, vector)

    evidence = [
        Evidence(
            subject_id=pre_id,
            kind=EvidenceKind.COMPUTATION,
            data={
                "algorithm": binding_ref.exact_hash_algorithm,
                "value": binding_ref.exact_hash,
            },
            produced_by=actor_id or authority,
        ),
        Evidence(
            subject_id=pre_id,
            kind=EvidenceKind.COMPUTATION,
            data={
                "computation": "coherence_score",
                "workshop_versions_compared": len(workshop_vectors),
                "score": score,
            },
            produced_by=actor_id or authority,
        ),
    ]
    claim = Claim(
        subject_id=pre_id,
        claimant_id=actor_id,
        origin=ClaimOrigin.COMPUTED,
        statement=f"Final version submitted for {pre_id}, coherence_score={score}.",
        data={
            "notes": notes,
            "exact_hash": binding_ref.exact_hash,
            "coherence_score": score,
        },
    )
    event = LifecycleEvent(
        event_id=str(uuid.uuid4()),
        pre_id=pre_id,
        stage=LifecycleStage.METAMORPHOSE,
        sequence=await _next_sequence(pre_id),
        actor_id=actor_id,
        authority=authority,
        claim=claim,
        evidence=evidence,
        content_binding_ref=binding_ref,
        data={"notes": notes, "signal_vector": vector, "coherence_score": score},
    )
    doc = await _notarize_and_store(event)
    return doc


# ---------- EMISSION ----------


class EmissionRequest(BaseModel):
    fk_frek_id: str = Field(
        ..., description="An existing .fk Cultural Object's frek_id."
    )


@creative_lifecycle_router.post("/{pre_id}/emission")
async def emit(
    pre_id: str,
    request: EmissionRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """STADE 4 — EMISSION. The work receives its real FREK Object
    identity. Strictly guarded: only allowed when the *current* stage is
    exactly METAMORPHOSE (`service.can_emit`)."""
    events = await _load_events(pre_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"{pre_id} introuvable")
    genesis_actor_id = events[0].get("actor_id")

    current = latest_stage(events)
    if not can_emit(current):
        raise HTTPException(
            status_code=409,
            detail=f"EMISSION requiert le stade METAMORPHOSE (actuel: {current})",
        )

    actor_id, authority = await _require_lifecycle_owner_or_admin(
        genesis_actor_id, x_frek_session, x_admin_key
    )
    if not await check_rate_limit(
        scope=actor_id or "admin", action="creative_lifecycle_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    fk_doc = await db.fk_objects.find_one(
        {"frek_id": request.fk_frek_id}, {"_id": 0, "frek_id": 1}
    )
    if not fk_doc:
        raise HTTPException(
            status_code=404, detail=f"FREK Object {request.fk_frek_id} introuvable"
        )

    # No history-wide idempotency check here, deliberately: the
    # `can_emit` guard above already requires the *current* stage to be
    # exactly METAMORPHOSE, which structurally rules out two EMISSION
    # events back-to-back without an intervening METAMORPHOSE (a second,
    # immediate resubmission would already have current == EMISSION and
    # 409 there). Scanning the *full* event history for a prior EMISSION
    # with the same fk_frek_id -- an earlier draft of this endpoint did
    # exactly that -- silently defeated the documented HYBRID re-entry
    # flow (models.py's module docstring: METAMORPHOSE -> EMISSION ->
    # METAMORPHOSE -> EMISSION is a real, supported second emission of
    # the same object, not a duplicate of the first): found via this
    # state's own test suite
    # (test_full_re_entry_cycle_allows_second_emission), not assumed.
    # A genuinely concurrent double-POST race is a pre-existing class of
    # risk shared with every other mutating endpoint in this codebase
    # (no distributed lock anywhere), not unique to D2.

    claim = Claim(
        subject_id=pre_id,
        claimant_id=actor_id,
        origin=ClaimOrigin.DECLARED,
        statement=f"{pre_id} emitted, bound to FREK Object {request.fk_frek_id}.",
        data={"fk_frek_id": request.fk_frek_id},
    )
    event = LifecycleEvent(
        event_id=str(uuid.uuid4()),
        pre_id=pre_id,
        stage=LifecycleStage.EMISSION,
        sequence=await _next_sequence(pre_id),
        actor_id=actor_id,
        authority=authority,
        claim=claim,
        evidence=[],
        fk_frek_id=request.fk_frek_id,
        data={},
    )
    doc = await _notarize_and_store(event)
    return {**doc, "deduplicated": False}


# ---------- LEGACY ----------


class LegacyRequest(BaseModel):
    child_pre_id: Optional[str] = None
    child_fk_frek_id: Optional[str] = None
    note: Optional[str] = None


@creative_lifecycle_router.post("/{pre_id}/legacy")
async def declare_legacy(
    pre_id: str,
    request: LegacyRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """STADE 5 — LEGACY. A derived/child work is linked to this one as
    its parent. Requires the parent to already carry an assigned
    `fk_frek_id` (i.e., to have reached EMISSION at some point) —
    `service.can_declare_legacy`. Deliberately NOT a D3 relationship
    graph — only a reference D3 can later consume (IMPLEMENT_TRUST_
    GRAPH=FALSE, IMPLEMENT_CULTURAL_GRAPH=FALSE this state)."""
    events = await _load_events(pre_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"{pre_id} introuvable")
    genesis_actor_id = events[0].get("actor_id")

    fk_frek_id = _resolve_fk_frek_id(events)
    if not can_declare_legacy(fk_frek_id):
        raise HTTPException(
            status_code=409,
            detail=f"{pre_id} n'a jamais atteint EMISSION -- LEGACY impossible",
        )

    if not request.child_pre_id and not request.child_fk_frek_id:
        raise HTTPException(
            status_code=400, detail="child_pre_id ou child_fk_frek_id requis"
        )

    actor_id, authority = await _require_lifecycle_owner_or_admin(
        genesis_actor_id, x_frek_session, x_admin_key
    )
    if not await check_rate_limit(
        scope=actor_id or "admin", action="creative_lifecycle_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    claim = Claim(
        subject_id=pre_id,
        claimant_id=actor_id,
        origin=ClaimOrigin.DECLARED,
        statement=(
            f"{pre_id} (FREK Object {fk_frek_id}) declared as parent of "
            f"{request.child_pre_id or request.child_fk_frek_id}."
        ),
        data={
            "child_pre_id": request.child_pre_id,
            "child_fk_frek_id": request.child_fk_frek_id,
            "note": request.note,
        },
    )
    event = LifecycleEvent(
        event_id=str(uuid.uuid4()),
        pre_id=pre_id,
        stage=LifecycleStage.LEGACY,
        sequence=await _next_sequence(pre_id),
        actor_id=actor_id,
        authority=authority,
        claim=claim,
        evidence=[],
        fk_frek_id=fk_frek_id,
        data={
            "child_pre_id": request.child_pre_id,
            "child_fk_frek_id": request.child_fk_frek_id,
            "note": request.note,
        },
    )
    doc = await _notarize_and_store(event)
    return doc


# ---------- Read (public) ----------


@creative_lifecycle_router.get("/{pre_id}")
async def get_lifecycle(pre_id: str):
    events = await _load_events(pre_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"{pre_id} introuvable")
    current = latest_stage(events)
    return {
        "pre_id": pre_id,
        "current_stage": current.value if current else None,
        "genesis_actor_id": events[0].get("actor_id"),
        "fk_frek_id": _resolve_fk_frek_id(events),
        "workshop_version_count": sum(
            1 for e in events if e["stage"] == LifecycleStage.WORKSHOP.value
        ),
        "events": events,
    }
