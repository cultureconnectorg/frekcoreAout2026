"""D1 — Content Binding API (canonical, hardened successor concept to the
historical `backend/frek/` certify/verify routes).

`backend/frek/routes.py`'s `POST /certify`, `POST /certify/upload`, and
`GET /verify/{frek_id}` are UNTOUCHED by this module — zero lines of
`backend/frek/` changed. Per the state-1 mission's explicit instruction
("do not perform destructive route migration unless required for D1
acceptance"), they remain live exactly as they always were (unauthenticated,
in-memory, minting their own identifier) — a separate, later ecosystem-
consumer audit decides their fate, not this pass.

This module is the additive, canonical D1 implementation: it binds
computed exact-hash + signal-fingerprint evidence to an EXISTING FREK
Object (a `.fk` Cultural Object, `db.fk_objects`) rather than minting any
identifier of its own — the structural fix for the historical
FREK-ID/fingerprint conflation (see `models.py`'s module docstring).
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

from security.policies import check_rate_limit

from .extraction import (
    FingerprintExtractionError,
    compute_signal_fingerprint,
    exact_hash,
)
from .models import ContentBinding, build_claim_and_evidence

logger = logging.getLogger("frek.content_binding.routes")

content_binding_router = APIRouter(
    prefix="/content-binding", tags=["FREK Content Binding (D1)"]
)

db = None

# Historical /certify accepted up to 100MB with no floor beyond "not
# trivially empty" and no rate limit at all (reconciliation report point
# 27: "a real DoS surface even before considering the identity question").
# This endpoint is authenticated, which already closes the anonymous-
# abuse case, but the payload bound is tightened regardless — 25MB is
# generous for a single audio clip and bounds the FFT/MFCC compute cost
# per call.
MIN_AUDIO_BYTES = 1000
MAX_AUDIO_BYTES = 25 * 1024 * 1024


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.content_bindings.create_index("binding_id", unique=True)
    await db.content_bindings.create_index([("frek_id", 1), ("exact_hash", 1)])
    await db.content_bindings.create_index("frek_id")


# ---------- Authorization (same convention as fingerprint/routes.py and
# geo/routes.py: _admin_or_403 / _is_holder / _holder_or_admin, deliberately
# NOT re-imported from another module — each module keeps this small,
# independently auditable, per this session's established precedent) ----------


def _admin_or_403(x_admin_key: str):
    expected = os.environ.get("SECRET_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="invalid_admin_key")


async def _is_holder(frek_id: str, x_frek_session: Optional[str]) -> bool:
    """True if the session's identity_engine identity either IS `frek_id`
    or has it in `linked_objects` — the same cross-system pattern
    `fingerprint`/`geo` already use for a `frek_id` that is not itself an
    identity_engine person (here: a `.fk` Cultural Object)."""
    if not x_frek_session:
        return False
    from identity_engine import service as identity_service

    session_frek_id = identity_service.verify_session_token(x_frek_session)
    if not session_frek_id:
        return False
    if session_frek_id == frek_id:
        return True
    identity = await db.frek_persons.find_one(
        {"frek_id": session_frek_id}, {"_id": 0, "linked_objects": 1}
    )
    return bool(identity and frek_id in identity.get("linked_objects", []))


async def _holder_or_admin(
    frek_id: str, x_frek_session: Optional[str], x_admin_key: str
) -> str:
    """Returns 'holder' or 'admin' (the `produced_by` provenance value),
    or raises 403."""
    if await _is_holder(frek_id, x_frek_session):
        return "holder"
    _admin_or_403(x_admin_key)
    return "admin"


# ---------- Create ----------


@content_binding_router.post("/{frek_id}")
async def create_content_binding(
    frek_id: str,
    audio: UploadFile = File(..., description="Audio content to bind."),
    legacy_identifier: Optional[str] = Form(
        default=None,
        description="Compatibility reference to a historical backend/frek/ identifier, if any.",
    ),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Compute exact-hash + signal-fingerprint evidence for `audio` and
    bind it to the existing FREK Object `frek_id`.

    Never mints a FREK-ID (FREK_ID_SEPARATED_FROM_FINGERPRINT): `frek_id`
    must already exist as a real `.fk` Cultural Object — 404 otherwise.
    Idempotent on (`frek_id`, `exact_hash`): resubmitting the identical
    content returns the existing binding rather than creating a duplicate
    (closes the historical gap where the same audio submitted twice
    produced two different identifiers, reconciliation report point 24).
    """
    fk_doc = await db.fk_objects.find_one(
        {"frek_id": frek_id}, {"_id": 0, "frek_id": 1}
    )
    if not fk_doc:
        raise HTTPException(
            status_code=404, detail=f"FREK Object {frek_id} introuvable"
        )

    produced_by = await _holder_or_admin(frek_id, x_frek_session, x_admin_key)

    rate_scope = frek_id if produced_by == "holder" else "admin"
    if not await check_rate_limit(scope=rate_scope, action="content_binding_create"):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    audio_bytes = await audio.read()
    if len(audio_bytes) < MIN_AUDIO_BYTES:
        raise HTTPException(status_code=400, detail="Fichier audio trop petit")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=400, detail="Fichier audio trop grand (max 25MB)"
        )

    content_hash = exact_hash(audio_bytes)

    # Idempotency: identical content already bound to this object.
    existing = await db.content_bindings.find_one(
        {"frek_id": frek_id, "exact_hash": content_hash}, {"_id": 0}
    )
    if existing:
        return {**existing, "deduplicated": True}

    try:
        fingerprint = await compute_signal_fingerprint(audio_bytes)
    except FingerprintExtractionError as e:
        raise HTTPException(status_code=400, detail=f"Audio illisible: {e}")

    binding_id = f"CB-{uuid.uuid4().hex}"
    claim, evidence = build_claim_and_evidence(
        frek_id=frek_id,
        exact_hash=content_hash,
        fingerprint=fingerprint,
        produced_by_id=produced_by,
    )
    binding = ContentBinding(
        binding_id=binding_id,
        frek_id=frek_id,
        exact_hash=content_hash,
        signal_fingerprint=fingerprint,
        legacy_identifier=legacy_identifier,
        produced_by=produced_by,
        claim=claim,
        evidence=evidence,
    )

    # Notarize — real durable proof (proof_engine.ProofState.LOCAL_PROOF)
    # instead of an in-memory-only record. The 528-float vector itself is
    # NOT embedded in the notarized payload (large, and the chain hashes
    # payload_data as a whole regardless) — a hash of it is, so the exact
    # computed vector can later be proven to match without bloating every
    # block. Best-effort: notarization failure must never block the
    # binding's own creation (same convention as every other mutation in
    # this codebase — notary/service.py's own "never raises").
    try:
        from notary.service import notarize_event as _notarize_event
        import hashlib as _hashlib
        import json as _json

        vector_sha256 = _hashlib.sha256(
            _json.dumps(fingerprint.vector, sort_keys=False).encode("utf-8")
        ).hexdigest()
        blk = await _notarize_event(
            payload_type="content_binding",
            payload_id=binding_id,
            payload_data={
                "binding_id": binding_id,
                "frek_id": frek_id,
                "exact_hash": content_hash,
                "exact_hash_algorithm": binding.exact_hash_algorithm,
                "signal_algorithm": fingerprint.algorithm,
                "signal_algorithm_version": fingerprint.algorithm_version,
                "signal_dimensions": fingerprint.dimensions,
                "signal_vector_sha256": vector_sha256,
            },
            metadata={"produced_by": produced_by},
        )
        if blk:
            binding.proof_state = "local_proof"
            binding.block_height = blk.get("height")
            binding.block_hash = blk.get("block_hash")
    except Exception:
        logger.warning(
            "content_binding notarization failed (non-blocking, stays "
            "proof_state=fingerprint)",
            exc_info=True,
        )

    doc = binding.to_public_dict()
    await db.content_bindings.insert_one(dict(doc))

    try:
        from eventbus.bus import default_bus as _event_bus
        from eventbus.producers import build_content_binding_created_event

        _event_bus.publish(build_content_binding_created_event(doc))
    except Exception:
        logger.warning(
            "content_binding.created event publish failed (non-blocking)",
            exc_info=True,
        )

    return {**doc, "deduplicated": False}


# ---------- Read (public — same posture as historical /verify and .fk's
# own /detail) ----------
#
# Route-shadowing note (the exact class of bug this session already found
# and fixed once for identity_engine's /revocation rename): the static
# "/binding/{binding_id}" path MUST be registered before the dynamic
# "/{frek_id}" path below, or FastAPI would match "binding" itself as a
# frek_id value.


@content_binding_router.get("/binding/{binding_id}")
async def get_content_binding_by_id(binding_id: str):
    doc = await db.content_bindings.find_one({"binding_id": binding_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Binding {binding_id} introuvable")
    return doc


@content_binding_router.get("/{frek_id}")
async def list_content_bindings(frek_id: str):
    cursor = db.content_bindings.find({"frek_id": frek_id}, {"_id": 0}).sort(
        "computed_at", 1
    )
    bindings = await cursor.to_list(200)
    return {"frek_id": frek_id, "count": len(bindings), "bindings": bindings}
