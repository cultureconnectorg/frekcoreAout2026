"""D5 -- pure logic: section builders, report composition, disclosure
filtering. Kept free of FastAPI/Mongo/notary (same discipline as every
other D-state's own service.py) -- every builder here takes an
already-resolved plain dict (or None), never touches a database itself,
so the legal-hardening rules below are unit-testable in isolation.

D1/D2/D3/D4/D6 REUSE-WITHOUT-REIMPLEMENTATION rules this module encodes
(mission's own per-state list, applied here, not re-derived from
scratch):

- D1: `proof_state`/binding fields are rendered as-is; D1's own
  validation status stays PARTIAL (`reports/FREKCORE_D1_VALIDATION_
  EVIDENCE.md`) -- never silently upgraded to VERIFIED here.
- D2: GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY history is rendered
  as a factual timeline, always paired with an explicit
  LEGAL_CONCLUSION_NOT_MADE statement -- never rendered as legal
  authorship, ownership, or absolute priority.
- D3: `layer` decides the ceiling. A CULTURAL relationship's section
  `kind` is always INFERRED, regardless of its own `status` field
  (SIMILAR_TO/INFLUENCED_BY never rendered as verified fact) -- only a
  TRUST relationship's own `status` can reach `kind=VERIFIED`, and only
  when `status == "verified"`.
- D4: `sync_status == "synced"` reflects FINAL_RECONCILIATION at the
  *transport* layer only (signature valid, freshness fresh, no replay/
  ordering/conflict) -- rendered as `kind=VERIFIED` scoped explicitly to
  "envelope integrity and freshness", never as a claim about the
  underlying subject's ownership/authorship. `local_validation ==
  locally_acceptable` without `sync_status == synced` is rendered
  distinctly (OFFLINE_ACCEPTED != FINAL_RECONCILIATION).
- D6: every section's `kind` is chosen from the real `Claim.origin` /
  `Evidence.kind` / `AuthorityStatus` values already on the record --
  never a second, parallel classification invented here.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from permissions.models import Scope, ScopeType

from .canonical import compute_report_hash
from .models import (
    LEGAL_DISCLAIMER,
    ReportSection,
    ReportSubjectType,
    SectionKind,
    SourceReferences,
    TechnicalEvidenceReport,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Section builders. Each takes already-resolved data, returns exactly one
# ReportSection (or None when there is nothing to report -- callers append
# a NOT_VERIFIED/UNKNOWN placeholder themselves, see routes.py, so absence
# is never silently dropped from a combined report).
# ---------------------------------------------------------------------------


def build_identity_section(identity_doc: Optional[dict]) -> ReportSection:
    if not identity_doc:
        return ReportSection(
            kind=SectionKind.NOT_VERIFIED,
            title="FREKCORE Identity",
            statements=["No FREKCORE identity record was found for this reference."],
        )
    status = identity_doc.get("status", "unknown")
    return ReportSection(
        kind=SectionKind.OBSERVED,
        title="FREKCORE Identity",
        statements=[
            f"A FREKCORE identity record exists (frek_id={identity_doc.get('frek_id')}), "
            f"status={status}.",
            "This record describes a technical identity registration; it "
            "is not a legal determination of the holder's real-world "
            "identity or legal capacity.",
        ],
        data={
            "frek_id": identity_doc.get("frek_id"),
            "identity_type": identity_doc.get("identity_type"),
            "status": status,
            "created_at": identity_doc.get("created_at"),
            "credentials_count": len(identity_doc.get("credentials", [])),
            "linked_objects_count": len(identity_doc.get("linked_objects", [])),
        },
        visibility=Scope(type=ScopeType.OBJECT),
    )


def build_credential_section(identity_doc: Optional[dict]) -> ReportSection:
    """Counts only -- raw public keys / credential material are never
    placed in a report (privacy guidance: report-caching leakage)."""
    if not identity_doc:
        return ReportSection(
            kind=SectionKind.NOT_VERIFIED,
            title="Credentials",
            statements=["No identity record to report credentials for."],
        )
    creds = identity_doc.get("credentials", [])
    return ReportSection(
        kind=SectionKind.OBSERVED,
        title="Credentials",
        statements=[
            f"{len(creds)} WebAuthn credential(s) are registered to this identity."
        ],
        data={"credentials_count": len(creds)},
        visibility=Scope(type=ScopeType.OBJECT),
    )


def build_object_section(fk_doc: Optional[dict]) -> ReportSection:
    if not fk_doc:
        return ReportSection(
            kind=SectionKind.NOT_VERIFIED,
            title="FREK Object",
            statements=["No FREK Object (.fk) record was found for this reference."],
        )
    return ReportSection(
        kind=SectionKind.OBSERVED,
        title="FREK Object",
        statements=[
            f"A FREK Object (frek_id={fk_doc.get('frek_id')}, "
            f"object_type={fk_doc.get('object_type')}) was created at "
            f"{fk_doc.get('created_at')} and is recorded in canonical "
            "FREKCORE storage.",
            "This record describes the object's registration; it is not "
            "a legal determination of authorship, ownership, or rights "
            "in the underlying creative work.",
        ],
        data={
            "frek_id": fk_doc.get("frek_id"),
            "object_type": fk_doc.get("object_type"),
            "created_at": fk_doc.get("created_at"),
            "root_hash": fk_doc.get("root_hash"),
            "block_hash": fk_doc.get("block_hash"),
        },
    )


def build_content_binding_section(binding_doc: Optional[dict]) -> ReportSection:
    if not binding_doc:
        return ReportSection(
            kind=SectionKind.NOT_VERIFIED,
            title="Content Binding (D1)",
            statements=["No content binding record was found for this reference."],
        )
    fp = binding_doc.get("signal_fingerprint", {})
    return ReportSection(
        kind=SectionKind.COMPUTED,
        title="Content Binding (D1)",
        statements=[
            f"An exact_hash ({binding_doc.get('exact_hash_algorithm')}) and a "
            f"signal_fingerprint ({fp.get('algorithm')}/{fp.get('algorithm_version')}, "
            f"{fp.get('dimensions')} dimensions) were computed for this content on "
            f"{binding_doc.get('computed_at')}.",
            "D1 validation status is PARTIAL (see "
            "reports/FREKCORE_D1_VALIDATION_EVIDENCE.md): no robustness "
            "property (compression, noise, re-recording, collision "
            "resistance) has been independently demonstrated for the "
            "signal fingerprint. This is evidence of a computed binding, "
            "not proof that no other content could ever produce the "
            "same or a similar fingerprint.",
        ],
        data={
            "binding_id": binding_doc.get("binding_id"),
            "frek_id": binding_doc.get("frek_id"),
            "exact_hash_prefix": (binding_doc.get("exact_hash") or "")[:16],
            "exact_hash_algorithm": binding_doc.get("exact_hash_algorithm"),
            "signal_fingerprint_algorithm": fp.get("algorithm"),
            "signal_fingerprint_algorithm_version": fp.get("algorithm_version"),
            "proof_state": binding_doc.get("proof_state"),
        },
    )


def build_creative_lifecycle_section(events: Sequence[dict]) -> ReportSection:
    if not events:
        return ReportSection(
            kind=SectionKind.NOT_VERIFIED,
            title="Creative Lifecycle History (D2)",
            statements=["No creative lifecycle history was found for this reference."],
        )
    ordered = sorted(events, key=lambda e: e.get("sequence", 0))
    stages = [str(e.get("stage")) for e in ordered]
    statements = [
        f"Recorded creative-lifecycle stage sequence: {' -> '.join(stages)} "
        f"({len(ordered)} event(s), pre_id={ordered[0].get('pre_id')})."
    ]
    return ReportSection(
        kind=SectionKind.CLAIMED,
        title="Creative Lifecycle History (D2)",
        statements=statements
        + [
            "This history describes the recorded creative process "
            "(GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY); it is not "
            "a legal determination of authorship, ownership, or "
            "priority over any other work."
        ],
        data={
            "pre_id": ordered[0].get("pre_id"),
            "event_count": len(ordered),
            "stages": stages,
            "fk_frek_id": next(
                (e.get("fk_frek_id") for e in ordered if e.get("fk_frek_id")), None
            ),
        },
    )


def build_relationship_section(relationships: Sequence[dict]) -> ReportSection:
    if not relationships:
        return ReportSection(
            kind=SectionKind.NOT_VERIFIED,
            title="Relationship / Provenance Records (D3)",
            statements=["No relationship records were found for this reference."],
        )
    any_cultural = any(r.get("layer") == "cultural" for r in relationships)
    any_trust_verified = any(
        r.get("layer") == "trust" and r.get("status") == "verified"
        for r in relationships
    )
    if any_trust_verified and not any_cultural:
        kind = SectionKind.VERIFIED
    elif any_cultural:
        kind = SectionKind.INFERRED
    else:
        kind = SectionKind.CLAIMED
    statements = [f"{len(relationships)} relationship record(s) reference this entity."]
    if any_cultural:
        statements.append(
            "One or more of these relationships is CULTURAL-layer "
            "(e.g. similar_to, influenced_by) -- a computed or inferred "
            "signal, never a verified fact, regardless of its own status "
            "field."
        )
    return ReportSection(
        kind=kind,
        title="Relationship / Provenance Records (D3)",
        statements=statements,
        data={
            "relationship_count": len(relationships),
            "relationships": [
                {
                    "relationship_id": r.get("relationship_id"),
                    "predicate": r.get("predicate"),
                    "layer": r.get("layer"),
                    "status": r.get("status"),
                }
                for r in relationships
            ],
        },
    )


def build_offline_transport_section(envelopes: Sequence[dict]) -> ReportSection:
    if not envelopes:
        return ReportSection(
            kind=SectionKind.NOT_VERIFIED,
            title="Offline Transport Envelopes (D4)",
            statements=[
                "No offline transport envelopes were found for this reference."
            ],
        )
    synced = [e for e in envelopes if e.get("sync_status") == "synced"]
    locally_acceptable_only = [
        e
        for e in envelopes
        if e.get("sync_status") != "synced"
        and e.get("local_validation") == "locally_acceptable"
    ]
    if synced:
        kind = SectionKind.VERIFIED
        statements = [
            f"{len(synced)} of {len(envelopes)} offline transport envelope(s) "
            "reached FINAL_RECONCILIATION (sync_status=synced): signature "
            "verified, freshness confirmed, no replay/ordering/conflict "
            "detected at reconciliation time. This is evidence of "
            "transport-level integrity and authority freshness for the "
            "envelope itself -- it is not a claim about the underlying "
            "subject's ownership or authorship."
        ]
    elif locally_acceptable_only:
        kind = SectionKind.NOT_VERIFIED
        statements = [
            f"{len(locally_acceptable_only)} envelope(s) are LOCALLY_ACCEPTABLE "
            "(valid signature, fresh cached authority at receive time) but "
            "have not yet reached FINAL_RECONCILIATION (sync). "
            "OFFLINE_ACCEPTED is not FINAL_RECONCILIATION."
        ]
    else:
        kind = SectionKind.UNKNOWN
        statements = [
            f"{len(envelopes)} envelope(s) found; none has reached "
            "FINAL_RECONCILIATION or LOCALLY_ACCEPTABLE local validation."
        ]
    return ReportSection(
        kind=kind,
        title="Offline Transport Envelopes (D4)",
        statements=statements,
        data={
            "envelope_count": len(envelopes),
            "synced_count": len(synced),
            "envelopes": [
                {
                    "envelope_id": e.get("envelope_id"),
                    "sync_status": e.get("sync_status"),
                    "local_validation": e.get("local_validation"),
                }
                for e in envelopes
            ],
        },
    )


def build_proof_section(blocks: Sequence[dict]) -> ReportSection:
    """`blocks` are raw `db.notary_blocks` documents (BlockResponse-shaped)
    for one or more payload_ids -- reuses `proof_engine.notary_adapter.
    proof_state_from_notary_block` per block, never reimplements the
    proof-state ladder."""
    if not blocks:
        return ReportSection(
            kind=SectionKind.UNKNOWN,
            title="Proof (FREK-Chain / Notary)",
            statements=[
                "No notarization/proof-chain record was found for this reference."
            ],
        )
    from proof_engine.notary_adapter import proof_state_from_notary_block

    receipts = [
        proof_state_from_notary_block(
            b.get("payload_id", ""), b.get("payload_hash", ""), b
        )
        for b in blocks
    ]
    best = max(
        receipts,
        key=lambda r: [
            "fingerprint",
            "local_proof",
            "signed_proof",
            "timestamp_proof",
            "opentimestamps_proof",
            "external_anchor_proof",
        ].index(r.state.value),
    )
    statements = [
        f"Proof state: {best.state.value} (block_height={best.block_height}, "
        f"block_hash={best.block_hash})."
    ]
    if best.state.value == "external_anchor_proof":
        statements.append(
            "This anchor may provide evidence that the referenced data "
            "existed no later than the demonstrable Bitcoin block time "
            "given by the anchoring mechanism used. It is not a "
            "qualified electronic timestamp under eIDAS or any "
            "equivalent regulation, and it is not, by itself, legal "
            "proof of ownership or authorship."
        )
    return ReportSection(
        kind=SectionKind.PROOF,
        title="Proof (FREK-Chain / Notary)",
        statements=statements,
        data={
            "proof_state": best.state.value,
            "block_height": best.block_height,
            "block_hash": best.block_hash,
            "btc_block_height": best.btc_block_height,
            "btc_attestation_time": best.btc_attestation_time,
        },
    )


def overall_caveat_section() -> ReportSection:
    """Always appended last -- the mission's own required standing
    caveat, restated as a section so it survives any downstream renderer
    that only walks `sections` rather than the top-level
    `legal_disclaimer` field."""
    return ReportSection(
        kind=SectionKind.LEGAL_CONCLUSION_NOT_MADE,
        title="Legal Status",
        statements=[LEGAL_DISCLAIMER],
    )


def compose_report(
    *,
    report_id: Optional[str] = None,
    subject_type: ReportSubjectType,
    subject_id: str,
    source_refs: SourceReferences,
    sections: List[ReportSection],
    requested_by: Optional[str] = None,
    requested_authority: Optional[str] = None,
) -> TechnicalEvidenceReport:
    report = TechnicalEvidenceReport(
        report_id=report_id or str(uuid.uuid4()),
        subject_type=subject_type,
        subject_id=subject_id,
        source_refs=source_refs,
        sections=[*sections, overall_caveat_section()],
        requested_by=requested_by,
        requested_authority=requested_authority,
    )
    report.report_hash = compute_report_hash(report)
    return report


# ---------------------------------------------------------------------------
# Disclosure. can_read mirrors D3's own can_read (same disclosed tradeoff:
# permissions.engine.decide() is not wired, no RoleGrant persistence exists
# -- see models.py's module docstring), applied PER SECTION rather than
# per report.
# ---------------------------------------------------------------------------


def can_read(
    visibility: Scope,
    *,
    actor_id: Optional[str],
    is_admin: bool,
    owner_ids: Sequence[Optional[str]],
) -> bool:
    if is_admin:
        return True
    if visibility.type == ScopeType.GLOBAL:
        return True
    if actor_id is None:
        return False
    if visibility.type == ScopeType.OBJECT:
        return actor_id in {o for o in owner_ids if o}
    if visibility.type == ScopeType.ENTITY:
        return actor_id == visibility.id
    if visibility.type == ScopeType.ORGANIZATION:
        return False
    return False  # pragma: no cover - exhaustive over ScopeType


def redact_for_disclosure(
    report_dict: Dict[str, Any], *, actor_id: Optional[str], is_admin: bool
) -> Dict[str, Any]:
    """Filters `sections` to only those the caller may see -- an
    unauthorized section is dropped, not merely blanked, so its absence
    cannot be distinguished from "not applicable" (same 404-not-403
    privacy discipline D3 uses for whole relationships, applied here per
    section)."""
    owner_ids = [
        report_dict.get("subject_id"),
        report_dict.get("requested_by"),
        (report_dict.get("source_refs") or {}).get("identity_frek_id"),
        (report_dict.get("source_refs") or {}).get("fk_frek_id"),
    ]
    visible_sections = []
    for section in report_dict.get("sections", []):
        visibility = Scope.model_validate(
            section.get("visibility") or {"type": "global"}
        )
        if can_read(
            visibility, actor_id=actor_id, is_admin=is_admin, owner_ids=owner_ids
        ):
            visible_sections.append(section)
    return {**report_dict, "sections": visible_sections}


def public_verification_view(
    report_dict: Dict[str, Any], *, hash_matches: bool
) -> Dict[str, Any]:
    """The PUBLIC verification cut (VERIFICATION_MAY_BE_PUBLIC=TRUE):
    shape only -- section `kind`/`title`, never `statements`/`data`
    (which may carry private evidence/relationship/credential content).
    A public verifier learns THAT sections of certain kinds exist and
    whether report integrity checks out, never the underlying material."""
    return {
        "report_id": report_dict.get("report_id"),
        "report_schema_version": report_dict.get("report_schema_version"),
        "subject_type": report_dict.get("subject_type"),
        "subject_id": report_dict.get("subject_id"),
        "generated_at": report_dict.get("generated_at"),
        "verification_time": _now_iso(),
        "report_hash": report_dict.get("report_hash"),
        "integrity_verified": hash_matches,
        "sections_summary": [
            {"kind": s.get("kind"), "title": s.get("title")}
            for s in report_dict.get("sections", [])
        ],
        "legal_disclaimer": report_dict.get("legal_disclaimer"),
    }
