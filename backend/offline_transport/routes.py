"""D4 -- Offline Proof Transport / Synchronization API.

`backend/frek/routes_advanced.py`'s 6 transmission routes (`GET
.../transmission`, `.../transmission/protocols`, `.../transmission/
protocol/{protocol}`, `POST .../transmission/packet`, `.../transmission/
watermark`, `.../transmission/sync`) are UNTOUCHED by this module --
zero lines changed. They remain live exactly as before (in-memory,
unauthenticated, no real signature) per the explicit instruction against
destructive route migration this state.

This module is the additive, canonical D4 implementation: a durable,
authenticated, cryptographically verifiable transport envelope +
sync/reconciliation service, transport-independent by construction.
"""

from __future__ import annotations

import base64
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from proof_engine.evidence_semantics import (
    AuthorityStatus,
    Claim,
    ClaimOrigin,
    Evidence,
    EvidenceKind,
)
from security.policies import check_rate_limit

from . import fap_adapter, watermark as watermark_mod
from .adapters import adapter_info, decode_envelope
from .canonical import compute_content_hash, signable_bytes
from .models import (
    DeviceAttestation,
    DeviceAttestationScheme,
    FreshnessInfo,
    LocalValidationStatus,
    SyncStatus,
    TransportEnvelope,
    TransportProtocol,
)
from .service import (
    compute_local_validation,
    detect_conflict,
    is_out_of_order,
    is_replay,
)

logger = logging.getLogger("frek.offline_transport.routes")

offline_transport_router = APIRouter(
    prefix="/offline", tags=["FREK Offline Transport (D4)"]
)

db = None

MAX_ENVELOPE_BYTES = 64 * 1024  # references/hashes preferred over inline artifacts
_SELF_ASSERTABLE_ORIGINS = {ClaimOrigin.DECLARED}
_SUPPORTED_SIGNATURE_ALGOS = {"ed25519"}


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.transport_envelopes.create_index("envelope_id", unique=True)
    await db.transport_envelopes.create_index([("issuer_id", 1), ("sequence", 1)])
    await db.offline_issuer_state.create_index("issuer_key", unique=True)
    await db.fap_devices.create_index("device_id_hex", unique=True)


# ---------- Authorization (same convention as D1-D3) ----------


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
    """Same split D3 uses: a holder may only self-assert DECLARED
    origin; OBSERVED/ATTESTED/COMPUTED/INFERRED are admin-only this
    state (no attester-role infrastructure exists yet)."""
    actor_id = await _session_actor(x_frek_session)
    if origin in _SELF_ASSERTABLE_ORIGINS and actor_id:
        return actor_id, "holder"
    _admin_or_403(x_admin_key)
    return actor_id, "admin"


async def _require_issuer_or_admin(
    issuer_id: Optional[str], x_frek_session: Optional[str], x_admin_key: str
) -> tuple[Optional[str], str]:
    actor_id = await _session_actor(x_frek_session)
    if actor_id and issuer_id and actor_id == issuer_id:
        return actor_id, "holder"
    _admin_or_403(x_admin_key)
    return actor_id, "admin"


# ---------- Persistence helpers ----------


def _issuer_key(issuer_id: Optional[str], authority: str) -> str:
    return issuer_id if (issuer_id and authority == "holder") else "admin"


async def _next_sequence(issuer_key: str) -> int:
    doc = await db.offline_issuer_state.find_one_and_update(
        {"issuer_key": issuer_key},
        {
            "$inc": {"last_sequence": 1},
            "$setOnInsert": {"last_reconciled_sequence": None},
        },
        upsert=True,
        return_document=True,
    )
    return doc["last_sequence"]


async def _load(envelope_id: str) -> Optional[dict]:
    return await db.transport_envelopes.find_one(
        {"envelope_id": envelope_id}, {"_id": 0}
    )


async def _store(envelope: TransportEnvelope) -> dict:
    doc = envelope.to_public_dict()
    await db.transport_envelopes.replace_one(
        {"envelope_id": envelope.envelope_id}, dict(doc), upsert=True
    )
    return doc


async def _publish_and_notarize(envelope_doc: dict, *, transition: str) -> None:
    try:
        from notary.service import notarize_event as _notarize_event

        await _notarize_event(
            payload_type="offline_transport_envelope",
            payload_id=envelope_doc["envelope_id"],
            payload_data={
                "envelope_id": envelope_doc["envelope_id"],
                "sequence": envelope_doc.get("sequence"),
                "sync_status": envelope_doc.get("sync_status"),
                "transition": transition,
            },
            metadata={"authority": envelope_doc.get("authority")},
        )
    except Exception:
        logger.warning(
            "offline_transport notarization failed (non-blocking)", exc_info=True
        )

    try:
        from eventbus.bus import default_bus as _event_bus
        from eventbus.producers import build_offline_transport_event

        _event_bus.publish(
            build_offline_transport_event(envelope_doc, transition=transition)
        )
    except Exception:
        logger.warning(
            "offline_transport.envelope_recorded publish failed (non-blocking)",
            exc_info=True,
        )


async def _known_fap_devices() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    async for doc in db.fap_devices.find({}, {"_id": 0}):
        out[doc["device_id_hex"]] = doc
    return out


async def _entity_exists(entity_type: Optional[str], entity_id: str) -> Optional[bool]:
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


async def _verify_envelope_signature(envelope: TransportEnvelope) -> bool:
    if envelope.signature_algo not in _SUPPORTED_SIGNATURE_ALGOS:
        return False
    if not envelope.signature:
        return False
    from passport import keys as passport_keys

    try:
        sig_bytes = base64.b64decode(envelope.signature)
    except Exception:
        return False
    return passport_keys.verify(sig_bytes, signable_bytes(envelope))


# ---------- POST /offline/envelopes -- CREATE + SIGN ----------


class CreateEnvelopeRequest(BaseModel):
    subject_ref: str
    subject_type: Optional[str] = None
    object_ref: Optional[str] = None
    object_type: Optional[str] = None
    origin: ClaimOrigin
    statement: str
    data: Dict[str, Any] = Field(default_factory=dict)
    content_binding_id: Optional[str] = None
    creative_lifecycle_event_id: Optional[str] = None
    relationship_id: Optional[str] = None
    device_attestation: Optional[DeviceAttestation] = None
    expires_at: Optional[str] = None


@offline_transport_router.post("/envelopes")
async def create_envelope(
    req: CreateEnvelopeRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """CREATE + SIGN. Signs the envelope's signable core with FREKCORE's
    own institutional Ed25519 key (`passport.keys`, the same signer
    behind `.fk`'s own `ProofLayer.signature` -- not a second signer).
    An optional `device_attestation` (a real FAP L2 proof) may be
    attached as an independent, stackable layer -- it is verified, not
    trusted blindly, on RECEIVE/SYNC."""
    actor_id, authority = await _require_submit_authority(
        req.origin, x_frek_session, x_admin_key
    )

    if not await check_rate_limit(
        scope=actor_id or "admin", action="offline_transport_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    for entity_type, entity_id, label in (
        (req.subject_type, req.subject_ref, "subject_ref"),
        (req.object_type, req.object_ref, "object_ref"),
    ):
        if entity_id is None:
            continue
        exists = await _entity_exists(entity_type, entity_id)
        if exists is False:
            raise HTTPException(
                status_code=404, detail=f"{label} {entity_id} introuvable"
            )

    if req.content_binding_id is not None:
        cb = await db.content_bindings.find_one(
            {"binding_id": req.content_binding_id}, {"_id": 0, "binding_id": 1}
        )
        if not cb:
            raise HTTPException(
                status_code=404,
                detail=f"content_binding_id {req.content_binding_id} introuvable",
            )
    if req.creative_lifecycle_event_id is not None:
        ev = await db.creative_lifecycle_events.find_one(
            {"event_id": req.creative_lifecycle_event_id}, {"_id": 0, "event_id": 1}
        )
        if not ev:
            raise HTTPException(
                status_code=404,
                detail=f"creative_lifecycle_event_id {req.creative_lifecycle_event_id} introuvable",
            )
    if req.relationship_id is not None:
        rel = await db.relationships.find_one(
            {"relationship_id": req.relationship_id}, {"_id": 0, "relationship_id": 1}
        )
        if not rel:
            raise HTTPException(
                status_code=404,
                detail=f"relationship_id {req.relationship_id} introuvable",
            )

    envelope_id = str(uuid.uuid4())
    issuer_key = _issuer_key(actor_id, authority)
    sequence = await _next_sequence(issuer_key)

    claim = Claim(
        subject_id=envelope_id,
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
                subject_id=envelope_id,
                kind=evidence_kind,
                data=req.data,
                produced_by=actor_id or authority,
            )
        ]
        if evidence_kind
        else []
    )

    envelope = TransportEnvelope(
        envelope_id=envelope_id,
        issuer_id=actor_id,
        authority=authority,
        subject_ref=req.subject_ref,
        subject_type=req.subject_type,
        object_ref=req.object_ref,
        object_type=req.object_type,
        claim=claim,
        evidence=evidence,
        content_binding_id=req.content_binding_id,
        creative_lifecycle_event_id=req.creative_lifecycle_event_id,
        relationship_id=req.relationship_id,
        device_attestation=req.device_attestation or DeviceAttestation(),
        content_hash="",
        sequence=sequence,
        nonce=secrets.token_hex(16),
        expires_at=req.expires_at,
    )
    envelope.content_hash = compute_content_hash(envelope)

    from passport import keys as passport_keys

    signature_bytes = passport_keys.sign(signable_bytes(envelope))
    envelope.signature = base64.b64encode(signature_bytes).decode("ascii")

    doc = await _store(envelope)
    await _publish_and_notarize(doc, transition="created")
    return doc


# ---------- protocols / historical taxonomy ----------


@offline_transport_router.get("/protocols")
async def get_protocols():
    return {"protocols": adapter_info()}


@offline_transport_router.post("/watermark")
async def create_watermark(
    frek_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """Preserves the historical ultrasonic watermark intent (reuses the
    real historical generator directly). WATERMARK_EQUALS_PROOF=FALSE --
    see watermark.py's module docstring for how this is enforced
    structurally, not just documented."""
    actor_id = await _session_actor(x_frek_session)
    if not actor_id:
        _admin_or_403(x_admin_key)
    return watermark_mod.create_watermark_reference(frek_id)


# ---------- devices (FAP) ----------


class RegisterDeviceRequest(BaseModel):
    device_id_hex: str
    ak_pub_hex: str
    firmware_hash_hex: Optional[str] = None


@offline_transport_router.post("/devices")
async def register_device(
    req: RegisterDeviceRequest, x_admin_key: str = Header(default="")
):
    _admin_or_403(x_admin_key)
    doc = {
        "device_id_hex": req.device_id_hex,
        "ak_pub_hex": req.ak_pub_hex,
        "status": "ACTIVE",
        "last_counter": 0,
        "trusted_firmware_hashes_hex": (
            [req.firmware_hash_hex] if req.firmware_hash_hex else None
        ),
    }
    await db.fap_devices.replace_one(
        {"device_id_hex": req.device_id_hex}, doc, upsert=True
    )
    return doc


@offline_transport_router.post("/devices/{device_id_hex}/revoke")
async def revoke_device(device_id_hex: str, x_admin_key: str = Header(default="")):
    _admin_or_403(x_admin_key)
    result = await db.fap_devices.update_one(
        {"device_id_hex": device_id_hex}, {"$set": {"status": "REVOKED"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="device_introuvable")
    return {"device_id_hex": device_id_hex, "status": "REVOKED"}


# ---------- GET /offline/envelopes/{id} + queue ----------


@offline_transport_router.get("/envelopes/queue")
async def get_queue(
    issuer_id: Optional[str] = Query(None),
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    actor_id = await _session_actor(x_frek_session)
    is_admin = _is_admin(x_admin_key)
    if not is_admin:
        if not actor_id:
            raise HTTPException(status_code=403, detail="invalid_admin_key")
        issuer_id = actor_id
    query: Dict[str, Any] = {
        "sync_status": {
            "$in": [SyncStatus.PENDING.value, SyncStatus.NEEDS_REVALIDATION.value]
        }
    }
    if issuer_id is not None:
        query["issuer_id"] = issuer_id
    cursor = db.transport_envelopes.find(query, {"_id": 0}).sort("sequence", 1)
    items = await cursor.to_list(500)
    return {"count": len(items), "envelopes": items}


@offline_transport_router.get("/envelopes/{envelope_id}")
async def get_envelope(
    envelope_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    doc = await _load(envelope_id)
    if not doc:
        raise HTTPException(status_code=404, detail="envelope_introuvable")
    actor_id, _ = await _require_issuer_or_admin(
        doc.get("issuer_id"), x_frek_session, x_admin_key
    )
    return doc


# ---------- POST /offline/envelopes/{id}/receive -- RECEIVE + LOCAL_VALIDATION ----------


class ReceiveRequest(BaseModel):
    protocol: TransportProtocol
    envelope_bytes_b64: Optional[str] = None
    freshness: Optional[FreshnessInfo] = None


@offline_transport_router.post("/envelopes/{envelope_id}/receive")
async def receive_envelope(
    envelope_id: str,
    req: ReceiveRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """RECEIVE + LOCAL_VALIDATION. Recomputes integrity and signature
    validity independently of whatever the transport claims. Freshness
    defaults to UNKNOWN/expired (OFFLINE_VERIFIED_EQUALS_ONLINE_STATUS_
    FRESH=FALSE) unless the caller explicitly supplies a recent cached
    snapshot -- receive-time validation can reach LOCALLY_ACCEPTABLE
    only then; otherwise it caps at CRYPTO_VALID_BUT_STATUS_STALE."""
    doc = await _load(envelope_id)
    if not doc:
        raise HTTPException(status_code=404, detail="envelope_introuvable")

    await _require_issuer_or_admin(doc.get("issuer_id"), x_frek_session, x_admin_key)

    if req.envelope_bytes_b64 is not None:
        try:
            raw = base64.b64decode(req.envelope_bytes_b64)
        except Exception:
            raise HTTPException(status_code=400, detail="envelope_bytes_b64 invalide")
        if len(raw) > MAX_ENVELOPE_BYTES:
            raise HTTPException(status_code=413, detail="envelope trop volumineux")
        try:
            received = decode_envelope(raw)
        except Exception:
            raise HTTPException(status_code=400, detail="envelope malformee")
        if received.envelope_id != envelope_id:
            raise HTTPException(status_code=400, detail="envelope_id incoherent")
        envelope = received
    else:
        envelope = TransportEnvelope.model_validate(doc)

    signature_valid = await _verify_envelope_signature(envelope)

    device_attestation_result = None
    if envelope.device_attestation.scheme == DeviceAttestationScheme.FAP_L2:
        if not envelope.device_attestation.proof_hex:
            device_attestation_result = {
                "accepted": False,
                "code": "MALFORMED",
                "message": "proof_hex missing",
            }
        else:
            known = await _known_fap_devices()
            device_attestation_result = fap_adapter.verify_fap_proof(
                envelope.device_attestation.proof_hex, known
            )

    freshness = req.freshness or FreshnessInfo()
    local_validation = compute_local_validation(
        signature_valid=signature_valid, freshness=freshness
    )

    envelope.freshness = freshness
    envelope.local_validation = local_validation
    envelope.transport_metadata = {
        **envelope.transport_metadata,
        "protocol": req.protocol.value,
    }
    if local_validation == LocalValidationStatus.INVALID:
        envelope.sync_status = SyncStatus.REJECTED
        envelope.rejection_reason = "signature_invalid"
    elif local_validation == LocalValidationStatus.CRYPTO_VALID_BUT_STATUS_STALE:
        envelope.sync_status = SyncStatus.NEEDS_REVALIDATION
    else:
        envelope.sync_status = SyncStatus.PENDING

    stored = await _store(envelope)
    await _publish_and_notarize(stored, transition="received")
    return {**stored, "device_attestation_result": device_attestation_result}


# ---------- POST /offline/envelopes/{id}/sync -- SYNC + FINAL_RECONCILIATION ----------


@offline_transport_router.post("/envelopes/{envelope_id}/sync")
async def sync_envelope(
    envelope_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    """SYNC + STATUS_REFRESH + AUTHORITY_CHECK + REPLAY/ORDERING/
    CONFLICT CHECK + FINAL_RECONCILIATION, per the mission's own
    11-step reconnect flow. RECEIVED_EQUALS_ACCEPTED=FALSE and
    ACCEPTED_OFFLINE_EQUALS_FINAL_RECONCILIATION=FALSE: only this step
    can move an envelope to SYNCED."""
    doc = await _load(envelope_id)
    if not doc:
        raise HTTPException(status_code=404, detail="envelope_introuvable")

    await _require_issuer_or_admin(doc.get("issuer_id"), x_frek_session, x_admin_key)

    # Idempotent: already-synced retry returns the existing outcome,
    # never re-runs side effects (test #23: sync retry safe).
    if doc["sync_status"] == SyncStatus.SYNCED.value:
        return doc
    if doc["sync_status"] == SyncStatus.REJECTED.value:
        return doc

    if not await check_rate_limit(
        scope=doc.get("issuer_id") or "admin", action="offline_transport_write"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    envelope = TransportEnvelope.model_validate(doc)
    envelope.sync_status = SyncStatus.SYNCING

    # 1-2. Integrity + signature, recomputed fresh.
    signature_valid = await _verify_envelope_signature(envelope)

    # 3-5. Resolve issuer / refresh authority / revocation check (device
    # attestation re-verified against CURRENT device state -- a device
    # revoked after RECEIVE but before SYNC is caught here, not before).
    device_attestation_result = None
    device_attestation_ok = True
    if envelope.device_attestation.scheme == DeviceAttestationScheme.FAP_L2:
        known = await _known_fap_devices()
        device_attestation_result = fap_adapter.verify_fap_proof(
            envelope.device_attestation.proof_hex or "", known
        )
        device_attestation_ok = bool(device_attestation_result.get("accepted"))
        if device_attestation_ok:
            device_id_hex = device_attestation_result["device_id_hex"]
            await db.fap_devices.update_one(
                {"device_id_hex": device_id_hex},
                {"$set": {"last_counter": device_attestation_result["counter"]}},
            )

    envelope.freshness = FreshnessInfo(
        status=(
            AuthorityStatus.CURRENT
            if device_attestation_ok
            else AuthorityStatus.REVOKED
        ),
        checked_at=datetime.now(timezone.utc).isoformat(),
        source="sync_authority_check",
        ttl_seconds=300,
    )

    issuer_key = _issuer_key(envelope.issuer_id, envelope.authority)
    issuer_state = await db.offline_issuer_state.find_one(
        {"issuer_key": issuer_key}, {"_id": 0}
    )
    last_reconciled = (issuer_state or {}).get("last_reconciled_sequence")

    # 6. Replay check.
    if is_replay(sequence=envelope.sequence, last_known_sequence=last_reconciled):
        envelope.sync_status = SyncStatus.REJECTED
        envelope.rejection_reason = "replay"
        stored = await _store(envelope)
        await _publish_and_notarize(stored, transition="rejected")
        return {**stored, "device_attestation_result": device_attestation_result}

    if not device_attestation_ok:
        envelope.sync_status = SyncStatus.REJECTED
        envelope.rejection_reason = "device_attestation_failed"
        stored = await _store(envelope)
        await _publish_and_notarize(stored, transition="rejected")
        return {**stored, "device_attestation_result": device_attestation_result}

    if not signature_valid:
        envelope.sync_status = SyncStatus.REJECTED
        envelope.rejection_reason = "signature_invalid"
        stored = await _store(envelope)
        await _publish_and_notarize(stored, transition="rejected")
        return {**stored, "device_attestation_result": device_attestation_result}

    # 7. Ordering check -- a gap means this envelope waits, it is never
    # reconciled ahead of its predecessor.
    if is_out_of_order(
        sequence=envelope.sequence, last_reconciled_sequence=last_reconciled
    ):
        envelope.sync_status = SyncStatus.NEEDS_REVALIDATION
        envelope.rejection_reason = "waiting_for_predecessor_sequence"
        stored = await _store(envelope)
        await _publish_and_notarize(stored, transition="queued")
        return {**stored, "device_attestation_result": device_attestation_result}

    # 8. Conflict check -- same (issuer, sequence), different payload.
    conflicting = await db.transport_envelopes.find_one(
        {
            "issuer_id": envelope.issuer_id,
            "sequence": envelope.sequence,
            "envelope_id": {"$ne": envelope.envelope_id},
        },
        {"_id": 0, "content_hash": 1},
    )
    if conflicting and detect_conflict(
        existing_content_hash=conflicting["content_hash"],
        incoming_content_hash=envelope.content_hash,
    ):
        envelope.sync_status = SyncStatus.CONFLICT
        envelope.rejection_reason = "conflicting_envelope_at_same_sequence"
        stored = await _store(envelope)
        await _publish_and_notarize(stored, transition="conflict")
        return {**stored, "device_attestation_result": device_attestation_result}

    # 9. Validate referenced D1/D2/D3 objects still exist.
    for coll, field, value in (
        ("content_bindings", "binding_id", envelope.content_binding_id),
        ("creative_lifecycle_events", "event_id", envelope.creative_lifecycle_event_id),
        ("relationships", "relationship_id", envelope.relationship_id),
    ):
        if value is not None:
            found = await db[coll].find_one({field: value}, {"_id": 0, field: 1})
            if not found:
                envelope.sync_status = SyncStatus.REJECTED
                envelope.rejection_reason = f"referenced_{field}_no_longer_found"
                stored = await _store(envelope)
                await _publish_and_notarize(stored, transition="rejected")
                return {
                    **stored,
                    "device_attestation_result": device_attestation_result,
                }

    # 10-11. Evaluate local validation with fresh authority, then
    # reconcile into canonical state, preserving audit history.
    envelope.local_validation = compute_local_validation(
        signature_valid=signature_valid, freshness=envelope.freshness
    )
    if envelope.local_validation != LocalValidationStatus.LOCALLY_ACCEPTABLE:
        envelope.sync_status = SyncStatus.NEEDS_REVALIDATION
        stored = await _store(envelope)
        await _publish_and_notarize(stored, transition="queued")
        return {**stored, "device_attestation_result": device_attestation_result}

    envelope.sync_status = SyncStatus.SYNCED
    envelope.reconciled_at = datetime.now(timezone.utc).isoformat()
    stored = await _store(envelope)
    await db.offline_issuer_state.update_one(
        {"issuer_key": issuer_key},
        {"$set": {"last_reconciled_sequence": envelope.sequence}},
        upsert=True,
    )
    await _publish_and_notarize(stored, transition="synced")
    return {**stored, "device_attestation_result": device_attestation_result}
