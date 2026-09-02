"""D5 -- Technical Evidence Report API.

`backend/frek/routes_advanced.py`'s `POST /api/frek/advanced/juridique/
attestation` (and `node09_juridique.py`) are UNTOUCHED by this module --
zero lines changed (`BACKEND_FREK_CHANGED=NO`). See models.py's module
docstring for the historical finding that route confirms from code.

This module is the additive, canonical D5 implementation: reports are
composed only from resource ID references (`GenerateReportRequest`
carries exactly `subject_type` + `subject_id`, nothing else), resolved
server-side from D1/D2/D3/D4/D6's own canonical storage -- never from
caller-supplied "facts". Generation is rate-limited and requires an
authenticated holder or admin; every response is redacted per the
caller's own authorization before being returned
(DISCLOSURE_IS_AUTHORIZATION_SCOPED=TRUE). A separate, public, more
tightly rate-limited verification endpoint exists
(VERIFICATION_MAY_BE_PUBLIC=TRUE) that returns shape-only integrity
confirmation, never section content.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from security.policies import check_rate_limit

from .models import ReportSubjectType, SourceReferences
from .service import (
    build_content_binding_section,
    build_creative_lifecycle_section,
    build_credential_section,
    build_identity_section,
    build_object_section,
    build_offline_transport_section,
    build_proof_section,
    build_relationship_section,
    compose_report,
    public_verification_view,
    redact_for_disclosure,
)
from .canonical import compute_report_hash
from .models import TechnicalEvidenceReport

logger = logging.getLogger("frek.technical_evidence_report.routes")

technical_evidence_report_router = APIRouter(
    prefix="/reports", tags=["FREK Technical Evidence Report (D5)"]
)

db = None


def set_db(database):
    global db
    db = database


async def ensure_indexes():
    await db.technical_evidence_reports.create_index("report_id", unique=True)
    await db.technical_evidence_reports.create_index("subject_id")


# ---------- Authorization (same convention as D1-D4) ----------


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


async def _require_holder_or_admin(
    x_frek_session: Optional[str], x_admin_key: str
) -> tuple[Optional[str], str]:
    actor_id = await _session_actor(x_frek_session)
    if actor_id:
        return actor_id, "holder"
    _admin_or_403(x_admin_key)
    return actor_id, "admin"


# ---------- Persistence + eventing ----------


async def _publish_and_notarize(report_doc: dict, *, transition: str) -> None:
    """Best-effort, never-blocking -- same convention as D1-D4. Never
    puts section content (statements/data) into the event payload; only
    identifying metadata (privacy: "never put sensitive evidence content
    directly into generic audit events")."""
    try:
        from notary.service import notarize_event as _notarize_event

        await _notarize_event(
            payload_type="technical_evidence_report",
            payload_id=report_doc["report_id"],
            payload_data={
                "report_id": report_doc["report_id"],
                "subject_type": report_doc.get("subject_type"),
                "subject_id": report_doc.get("subject_id"),
                "report_hash": report_doc.get("report_hash"),
                "transition": transition,
            },
            metadata={"authority": report_doc.get("requested_authority")},
        )
    except Exception:
        logger.warning(
            "technical_evidence_report notarization failed (non-blocking)",
            exc_info=True,
        )

    try:
        from eventbus.bus import default_bus as _event_bus
        from eventbus.producers import build_technical_evidence_report_event

        _event_bus.publish(
            build_technical_evidence_report_event(report_doc, transition=transition)
        )
    except Exception:
        logger.warning(
            "technical_evidence_report.recorded publish failed (non-blocking)",
            exc_info=True,
        )


# ---------- Canonical state resolution (DB I/O lives here, not service.py) ----------


async def _resolve_and_compose(
    subject_type: ReportSubjectType,
    subject_id: str,
    *,
    requested_by: Optional[str],
    requested_authority: str,
) -> Optional[TechnicalEvidenceReport]:
    """Resolves `subject_type`/`subject_id` against canonical FREKCORE
    storage and composes a report. Returns None if the reference does
    not resolve to anything at all (fail-closed -- routes.py turns this
    into 404, never a report describing nothing)."""
    sections = []
    refs = SourceReferences()

    if subject_type == ReportSubjectType.FREK_IDENTITY:
        identity = await db.frek_persons.find_one({"frek_id": subject_id}, {"_id": 0})
        if not identity:
            return None
        refs.identity_frek_id = subject_id
        sections = [build_identity_section(identity)]

    elif subject_type == ReportSubjectType.CREDENTIAL:
        identity = await db.frek_persons.find_one({"frek_id": subject_id}, {"_id": 0})
        if not identity:
            return None
        refs.identity_frek_id = subject_id
        sections = [build_credential_section(identity)]

    elif subject_type == ReportSubjectType.FREK_OBJECT:
        fk_doc = await db.fk_objects.find_one(
            {"frek_id": subject_id}, {"_id": 0, "storage_path": 0}
        )
        if not fk_doc:
            return None
        refs.fk_frek_id = subject_id
        blocks = await db.notary_blocks.find(
            {"payload_id": subject_id}, {"_id": 0}
        ).to_list(50)
        refs.notary_payload_ids = [subject_id] if blocks else []
        sections = [build_object_section(fk_doc), build_proof_section(blocks)]

    elif subject_type == ReportSubjectType.CONTENT_BINDING:
        binding = await db.content_bindings.find_one(
            {"binding_id": subject_id}, {"_id": 0}
        )
        if not binding:
            return None
        refs.content_binding_id = subject_id
        blocks = await db.notary_blocks.find(
            {"payload_id": subject_id}, {"_id": 0}
        ).to_list(50)
        sections = [build_content_binding_section(binding), build_proof_section(blocks)]

    elif subject_type == ReportSubjectType.CREATIVE_LIFECYCLE_HISTORY:
        events = await db.creative_lifecycle_events.find(
            {"pre_id": subject_id}, {"_id": 0}
        ).to_list(500)
        if not events:
            return None
        refs.creative_lifecycle_pre_id = subject_id
        refs.creative_lifecycle_event_ids = [e["event_id"] for e in events]
        sections = [build_creative_lifecycle_section(events)]

    elif subject_type == ReportSubjectType.RELATIONSHIP_RECORD:
        rel = await db.relationships.find_one(
            {"relationship_id": subject_id}, {"_id": 0}
        )
        if not rel:
            return None
        refs.relationship_ids = [subject_id]
        sections = [build_relationship_section([rel])]

    elif subject_type == ReportSubjectType.OFFLINE_TRANSPORT_ENVELOPE:
        envelope = await db.transport_envelopes.find_one(
            {"envelope_id": subject_id}, {"_id": 0}
        )
        if not envelope:
            return None
        refs.offline_transport_envelope_ids = [subject_id]
        sections = [build_offline_transport_section([envelope])]

    elif subject_type == ReportSubjectType.PROOF:
        blocks = await db.notary_blocks.find(
            {"payload_id": subject_id}, {"_id": 0}
        ).to_list(50)
        if not blocks:
            return None
        refs.notary_payload_ids = [subject_id]
        sections = [build_proof_section(blocks)]

    elif subject_type in (
        ReportSubjectType.EVIDENCE_RECORD,
        ReportSubjectType.COMBINED_EVIDENCE_PACKAGE,
    ):
        identity = await db.frek_persons.find_one({"frek_id": subject_id}, {"_id": 0})
        fk_doc = await db.fk_objects.find_one(
            {"frek_id": subject_id}, {"_id": 0, "storage_path": 0}
        )
        bindings = await db.content_bindings.find(
            {"frek_id": subject_id}, {"_id": 0}
        ).to_list(50)
        lifecycle_events = await db.creative_lifecycle_events.find(
            {"$or": [{"pre_id": subject_id}, {"fk_frek_id": subject_id}]}, {"_id": 0}
        ).to_list(500)
        relationships = await db.relationships.find(
            {"$or": [{"subject_id": subject_id}, {"object_id": subject_id}]},
            {"_id": 0},
        ).to_list(200)
        envelopes = await db.transport_envelopes.find(
            {"$or": [{"subject_ref": subject_id}, {"object_ref": subject_id}]},
            {"_id": 0},
        ).to_list(200)
        blocks = await db.notary_blocks.find(
            {"payload_id": subject_id}, {"_id": 0}
        ).to_list(50)

        if not any(
            [
                identity,
                fk_doc,
                bindings,
                lifecycle_events,
                relationships,
                envelopes,
                blocks,
            ]
        ):
            return None

        refs.identity_frek_id = subject_id if identity else None
        refs.fk_frek_id = subject_id if fk_doc else None
        refs.content_binding_id = bindings[0]["binding_id"] if bindings else None
        refs.creative_lifecycle_pre_id = (
            lifecycle_events[0]["pre_id"] if lifecycle_events else None
        )
        refs.creative_lifecycle_event_ids = [e["event_id"] for e in lifecycle_events]
        refs.relationship_ids = [r["relationship_id"] for r in relationships]
        refs.offline_transport_envelope_ids = [e["envelope_id"] for e in envelopes]
        refs.notary_payload_ids = [subject_id] if blocks else []

        sections = []
        if identity:
            sections.append(build_identity_section(identity))
        if fk_doc:
            sections.append(build_object_section(fk_doc))
        if bindings:
            sections.append(build_content_binding_section(bindings[0]))
        if lifecycle_events:
            sections.append(build_creative_lifecycle_section(lifecycle_events))
        if relationships:
            sections.append(build_relationship_section(relationships))
        if envelopes:
            sections.append(build_offline_transport_section(envelopes))
        if subject_type == ReportSubjectType.COMBINED_EVIDENCE_PACKAGE:
            sections.append(build_proof_section(blocks))

    else:  # pragma: no cover - exhaustive over ReportSubjectType
        return None

    return compose_report(
        subject_type=subject_type,
        subject_id=subject_id,
        source_refs=refs,
        sections=sections,
        requested_by=requested_by,
        requested_authority=requested_authority,
    )


# ---------- POST /reports/technical-evidence -- GENERATE ----------


class GenerateReportRequest(BaseModel):
    """Exactly a resource ID reference -- no caller-supplied facts
    (ARBITRARY_CALLER_SUPPLIED_FACTS_AS_CANONICAL_TRUTH=FALSE)."""

    subject_type: ReportSubjectType
    subject_id: str


@technical_evidence_report_router.post("/technical-evidence")
async def generate_report(
    req: GenerateReportRequest,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    actor_id, authority = await _require_holder_or_admin(x_frek_session, x_admin_key)

    if not await check_rate_limit(
        scope=actor_id or "admin", action="technical_evidence_report_generate"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    report = await _resolve_and_compose(
        req.subject_type,
        req.subject_id,
        requested_by=actor_id,
        requested_authority=authority,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="reference_introuvable")

    doc = report.to_public_dict()
    doc["is_snapshot"] = True
    await db.technical_evidence_reports.insert_one(dict(doc))
    await _publish_and_notarize(doc, transition="generated")

    return redact_for_disclosure(
        doc, actor_id=actor_id, is_admin=(authority == "admin")
    )


# ---------- GET /reports/technical-evidence/{report_id} -- RETRIEVE ----------


@technical_evidence_report_router.get("/technical-evidence/{report_id}")
async def get_report(
    report_id: str,
    x_frek_session: Optional[str] = Header(None),
    x_admin_key: str = Header(default=""),
):
    doc = await db.technical_evidence_reports.find_one(
        {"report_id": report_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="report_introuvable")

    actor_id = await _session_actor(x_frek_session)
    is_admin = _is_admin(x_admin_key)
    redacted = redact_for_disclosure(doc, actor_id=actor_id, is_admin=is_admin)
    if not redacted["sections"]:
        # No section is visible to this caller -- existence is not leaked
        # beyond the caveat section every report always carries, so a
        # fully-empty result (no caveat either) means this caller may not
        # even confirm the report exists.
        raise HTTPException(status_code=404, detail="report_introuvable")

    await _publish_and_notarize(doc, transition="accessed")
    return redacted


# ---------- GET /reports/technical-evidence/{report_id}/verify -- PUBLIC VERIFY ----------


@technical_evidence_report_router.get("/technical-evidence/{report_id}/verify")
async def verify_report(report_id: str):
    """Public verification endpoint (VERIFICATION_MAY_BE_PUBLIC=TRUE) --
    no session required, shape-only response, never section content.
    Separately, more tightly rate-limited than generation."""
    if not await check_rate_limit(
        scope=report_id, action="technical_evidence_report_verify"
    ):
        raise HTTPException(status_code=429, detail="Trop de requetes")

    doc = await db.technical_evidence_reports.find_one(
        {"report_id": report_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="report_introuvable")

    report = TechnicalEvidenceReport.model_validate(doc)
    recomputed = compute_report_hash(report)
    hash_matches = recomputed == doc.get("report_hash")

    await _publish_and_notarize(doc, transition="verification_performed")
    return public_verification_view(doc, hash_matches=hash_matches)
