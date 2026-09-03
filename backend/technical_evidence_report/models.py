"""D5 — Technical Evidence Report: data shapes.

Founder decision D5 (reconciliation record: `reports/
FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` §D "D5 — Technical
Evidence Report / Juridical Framing"), `FOUNDER_DISPOSITION=D5=
PRESERVE_INTENT_ABSORB_LEGAL_HARDEN`: D5 does not create new truth. It is
a **pure consumer** of D1 (content binding), D2 (creative lifecycle), D3
(relationship/provenance graph), D4 (offline transport), and D6 (evidence
semantics) — it reads their canonical, already-persisted state and renders
it as a structured, legally-hardened report. Nothing in this module ever
writes to `db.content_bindings`, `db.creative_lifecycle_events`,
`db.relationships`, or `db.transport_envelopes`.

HISTORICAL DISCOVERY (this pass, read directly from `backend/frek/
routes_advanced.py`'s `POST /api/frek/advanced/juridique/attestation` and
its backing `backend/frek/nodes/node09_juridique.py` — not trusted from
any prior summary):

- `AttestationRequest` (routes_advanced.py) takes `sha256_signal`,
  `vector_dimensions`, `artiste_id`, `timestamp_ms`, `gps_lat`, `gps_lon`
  **directly from the HTTP request body** — confirmed by reading the
  route handler: no database read, no auth dependency, no lookup against
  any canonical FREKCORE state anywhere in `create_attestation`.
- `Node09Juridique.create_attestation` (node09_juridique.py) is a pure
  string-formatting function over exactly those caller-supplied values.
  It never independently retrieves or verifies anything.
- `TechnicalAttestation.to_legal_text()` renders, verbatim: *"Ce fait est
  mathematiquement certain et temporellement irrefutable."* — this is
  precisely the class of unqualified overclaim
  (IRREFUTABLE/MATHEMATICALLY-CERTAIN wording, produced from unverified
  caller input) this state's mission brief names as the exact defect to
  never repeat. Confirmed from code, not assumed.
- The module's own docstring is explicit about intent, though: FREK is
  meant to be a "notaire de fait" (a notary of *technical facts*), never
  a "juge de droit" — its own `NEVER_STATEMENTS`/`ALWAYS_STATEMENTS`
  lists are a real, pre-existing, and largely correct legal-neutrality
  framework (never claims authorship, ownership, originality, rights, or
  legal registration). The DEFECT is narrower than the intent: the
  *behavior* (blind trust of caller-supplied "facts", plus one
  overclaiming phrase) does not match the *stated* intent.

Founder verdict, per the mission's own framing, applied exactly as
specified: **PRESERVE_INTENT=TRUE, PRESERVE_BLIND_TRUST_BEHAVIOR=FALSE.**
`backend/frek/routes_advanced.py`'s `/juridique/attestation` route and
`node09_juridique.py` are left completely untouched this state
(`BACKEND_FREK_CHANGED=NO`) — no destructive rewrite, no deletion. This
module is the additive, canonical D5 replacement: it keeps node09's
"notary of fact, not judge of law" *principle*, but a report only ever
describes canonical FREKCORE state resolved server-side from a resource
ID reference — never arbitrary caller-supplied "facts" — and its wording
generator is guarded (`assert_no_forbidden_language`, below) against the
exact overclaim class node09's own `to_legal_text()` produces.

ABSOLUTE INVARIANTS this module exists to enforce structurally (the
founder's 11 FALSE-equations, verbatim):

    TECHNICAL_REPORT_EQUALS_NOTARIAL_ACT = FALSE
    TECHNICAL_REPORT_EQUALS_LEGAL_JUDGMENT = FALSE
    TECHNICAL_REPORT_EQUALS_COPYRIGHT_REGISTRATION = FALSE
    TECHNICAL_REPORT_EQUALS_LEGAL_AUTHORSHIP_PROOF = FALSE
    TECHNICAL_REPORT_EQUALS_LEGAL_OWNERSHIP_PROOF = FALSE
    TECHNICAL_REPORT_EQUALS_QUALIFIED_EIDAS_TIMESTAMP = FALSE
    TECHNICAL_VERIFICATION_EQUALS_REAL_WORLD_CLAIM_TRUE = FALSE
    CRYPTOGRAPHIC_VALIDITY_EQUALS_LEGAL_VALIDITY = FALSE
    ANCHOR_EQUALS_LEGAL_OWNERSHIP = FALSE
    SIGNATURE_VALID_EQUALS_CURRENT_AUTHORITY = FALSE
    CLAIM_EQUALS_PROOF = FALSE
    WATERMARK_EQUALS_PROOF = FALSE

How each is enforced, not just documented:

- `LEGAL_DISCLAIMER` is a single fixed constant, attached unmodified to
  every `TechnicalEvidenceReport` (`legal_disclaimer` field, effectively
  frozen by convention — see `service.compose_report`) — it can never
  drift per-report or be silently omitted.
- `ReportSection.statements` runs `assert_no_forbidden_language` in a
  pydantic field validator — a section literally cannot be constructed
  with an overclaiming sentence in it. This is what makes the "LEGAL
  WORDING REGRESSION TESTS" the mission asks for meaningful: the guard is
  load-bearing at construction time, not a decorative test-only check.
- `SectionKind` has no single collapsing "VERIFIED: bool" — CLAIMED,
  OBSERVED, ATTESTED, COMPUTED, INFERRED, EVIDENCE, PROOF, VERIFIED,
  UNKNOWN, NOT_VERIFIED, and LEGAL_CONCLUSION_NOT_MADE are named
  separately (this state's own D6 requirement) and `service.py`'s section
  builders assign exactly one honestly, per D1-D4's own already-typed
  origin/status fields — never inferred more optimistically than the
  underlying record supports (D1_VERIFIED stays PARTIAL, D2 GENESIS never
  renders as authorship, D3 CULTURAL never renders as VERIFIED, D4
  SYNCED never renders as anything beyond transport-level reconciliation
  — see `service.py`'s builder docstrings for exactly how each is kept
  honest).
- Every `TechnicalEvidenceReport` carries a fixed
  `LEGAL_CONCLUSION_NOT_MADE` caveat section
  (`service.overall_caveat_section`), always appended last, never
  optional.

REPORT SUBJECT TYPES (`ReportSubjectType`) are the founder's own bounded
list, reproduced exactly — no invented type is added:
FREK_IDENTITY, FREK_OBJECT, CONTENT_BINDING, CREATIVE_LIFECYCLE_HISTORY,
RELATIONSHIP_RECORD, CREDENTIAL, EVIDENCE_RECORD, PROOF,
OFFLINE_TRANSPORT_ENVELOPE, COMBINED_EVIDENCE_PACKAGE.

CANONICAL-INPUT RULE (ARBITRARY_CALLER_SUPPLIED_FACTS_AS_CANONICAL_TRUTH
=FALSE): `GenerateReportRequest` (routes.py) accepts exactly
`subject_type` + `subject_id` — a resource ID reference — and nothing
else. Every fact in the resulting report is resolved server-side from
`db.content_bindings` / `db.creative_lifecycle_events` / `db.relationships`
/ `db.transport_envelopes` / `db.fk_objects` / `db.frek_persons` /
`db.notary_blocks` (routes.py's `_resolve_and_compose`) — never taken
from the request body. An unresolvable reference fails closed (404), it
is never silently rendered as if it existed (see routes.py).

DISCLOSURE (`VERIFICATION_MAY_BE_PUBLIC=TRUE,
DISCLOSURE_IS_AUTHORIZATION_SCOPED=TRUE`): `ReportSection.visibility`
reuses `permissions.models.Scope`/`ScopeType` directly, **per section**
— not one report-level flag — precisely so `PROOF_VISIBILITY !=
EVIDENCE_VISIBILITY`, `RELATIONSHIP_VISIBILITY != SUBJECT_METADATA_
VISIBILITY`, and `OBJECT_PUBLIC != ALL_PROVENANCE_PUBLIC` are
structurally possible outcomes, not just policy prose. `CREATE_REPORT_
PERMISSION_SYSTEM=FALSE`: no new permission engine is invented — the
same disclosed D3 tradeoff applies here (see `service.can_read`'s
docstring): `Scope`/`ScopeType` are reused as the type, interpreted by a
small report-domain `can_read`, `permissions.engine.decide()` is not
wired (no `RoleGrant` persistence exists anywhere in this codebase, see
D3's own module docstring for the same finding, unchanged this state).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from permissions.models import Scope, ScopeType


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Report subject types — the founder's own bounded list (mission brief's
# "JUSTIFIED REPORT SUBJECT TYPES" section), reproduced exactly.
# ---------------------------------------------------------------------------
class ReportSubjectType(str, Enum):
    FREK_IDENTITY = "frek_identity"
    FREK_OBJECT = "frek_object"
    CONTENT_BINDING = "content_binding"
    CREATIVE_LIFECYCLE_HISTORY = "creative_lifecycle_history"
    RELATIONSHIP_RECORD = "relationship_record"
    CREDENTIAL = "credential"
    EVIDENCE_RECORD = "evidence_record"
    PROOF = "proof"
    OFFLINE_TRANSPORT_ENVELOPE = "offline_transport_envelope"
    COMBINED_EVIDENCE_PACKAGE = "combined_evidence_package"


# ---------------------------------------------------------------------------
# Section sectioning vocabulary — the mission's own explicit D6 requirement:
# never flatten to "verified". NOT_VERIFIED, UNKNOWN, PARTIAL-shaped results
# are valid, expected outcomes, not failures to be smoothed over.
# ---------------------------------------------------------------------------
class SectionKind(str, Enum):
    CLAIMED = "claimed"
    OBSERVED = "observed"
    ATTESTED = "attested"
    COMPUTED = "computed"
    INFERRED = "inferred"
    EVIDENCE = "evidence"
    PROOF = "proof"
    VERIFIED = "verified"
    UNKNOWN = "unknown"
    NOT_VERIFIED = "not_verified"
    LEGAL_CONCLUSION_NOT_MADE = "legal_conclusion_not_made"


# ---------------------------------------------------------------------------
# Legal wording guard. Case-insensitive substring match on a closed,
# explicit list — deliberately conservative (a false positive just means a
# section author has to phrase something more carefully; a false negative
# would let an overclaim through, which is the actual harm this guards
# against). Phrases are the founder's own named examples plus their direct
# French equivalents (FREKCORE's own historical wording, per node09's
# `to_legal_text`, is French).
# ---------------------------------------------------------------------------
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "irrefutable",
    "irréfutable",
    "proves ownership",
    "prouve la propriété",
    "proves authorship",
    "prouve la paternité",
    "proves originality",
    "official notarial act",
    "acte notarié officiel",
    "notarial act",
    "qualified eidas timestamp",
    "horodatage eidas qualifié",
    "guaranteed original",
    "guarantees originality",
    "garantit l'originalité",
    "cannot be forged",
    "unforgeable",
    "infalsifiable",
    "absolute proof",
    "preuve absolue",
    "mathematically proves ownership",
    "mathématiquement certain et temporellement irréfutable",
    "legally certified",
    "certifié légalement",
    "legal proof of ownership",
    "constitutes legal proof",
)


class LegalWordingViolation(ValueError):
    """Raised when generated report text contains a forbidden overclaim
    phrase. Load-bearing, not decorative: this is what the mission's
    "LEGAL WORDING REGRESSION TESTS" actually exercise (see
    `tests/test_technical_evidence_report_unit.py`'s
    `TestLegalWordingRegression`)."""


_FORBIDDEN_PATTERN = re.compile(
    "|".join(re.escape(p) for p in FORBIDDEN_PHRASES), re.IGNORECASE
)

# The guard must block a POSITIVE overclaim assertion ("this is
# irrefutable proof of ownership") while still allowing `LEGAL_DISCLAIMER`
# itself to say, in plain language, exactly which of these claims a
# report is NOT making ("It is NOT a notarial act... NOT a qualified
# electronic timestamp...") -- that negation is the entire point of the
# disclaimer, not a loophole in the guard. A forbidden phrase is only a
# violation when it is NOT immediately preceded by one of these negation
# markers within a short window.
_NEGATION_MARKERS = (
    "not a",
    "not an",
    "not the",
    "never a",
    "never an",
    "n'est pas",
    "n est pas",
    "ne constitue pas",
    "ne garantit pas",
    "ne peut pas",
)
_NEGATION_WINDOW = 40


def assert_no_forbidden_language(text: str) -> None:
    """Raises `LegalWordingViolation` if `text` contains any forbidden
    overclaim phrase used as a positive assertion (case-insensitive
    substring match, negation-aware -- see `_NEGATION_MARKERS` above).
    Called from `ReportSection`'s own field validator -- a section
    cannot be constructed with an overclaiming sentence in it, by
    construction."""
    lower = text.lower()
    for match in _FORBIDDEN_PATTERN.finditer(lower):
        window_start = max(0, match.start() - _NEGATION_WINDOW)
        window_end = match.start()
        window = lower[window_start:window_end]
        if any(marker in window for marker in _NEGATION_MARKERS):
            continue
        raise LegalWordingViolation(
            f"forbidden overclaim phrase {match.group(0)!r} in report text: {text!r}"
        )


# ---------------------------------------------------------------------------
# Fixed legal disclaimer -- attached unmodified to every report
# (service.compose_report). Never rephrased per-report, never omitted.
# ---------------------------------------------------------------------------
LEGAL_DISCLAIMER = (
    "This is a FREKCORE Technical Evidence Report: a machine-generated, "
    "structured description of what FREKCORE's own systems recorded, "
    "computed, or cryptographically verified about the referenced "
    "resource, as of the time stated above. It is NOT a notarial act, "
    "NOT a legal judgment, NOT a copyright or trademark registration, "
    "NOT legal proof of authorship or ownership, and NOT a qualified "
    "electronic timestamp under eIDAS or any equivalent regulation "
    "unless explicitly stated otherwise with a named qualified trust "
    "service provider. Cryptographic validity (a valid signature, a "
    "matching hash, a confirmed chain anchor) is evidence that specific "
    "technical facts held at a specific time -- it is not, by itself, a "
    "legal conclusion about rights, authorship, or ownership. Sections "
    "below are individually labeled CLAIMED, OBSERVED, ATTESTED, "
    "COMPUTED, INFERRED, EVIDENCE, PROOF, VERIFIED, UNKNOWN, or "
    "NOT_VERIFIED; none of these labels should be read as a substitute "
    "for the others, and UNKNOWN/NOT_VERIFIED/NOT_AVAILABLE results are "
    "valid, expected outcomes -- not a system failure."
)


class ReportSection(BaseModel):
    """One labeled section of a report. `kind` names exactly what class
    of statement this is (see module docstring) -- never flattened.
    `visibility` is per-section (reused `permissions.models.Scope`
    directly, PROOF_VISIBILITY != EVIDENCE_VISIBILITY etc. -- see module
    docstring)."""

    kind: SectionKind
    title: str
    statements: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    visibility: Scope = Field(default_factory=lambda: Scope(type=ScopeType.GLOBAL))

    @field_validator("statements")
    @classmethod
    def _no_forbidden_language(cls, value: List[str]) -> List[str]:
        for statement in value:
            assert_no_forbidden_language(statement)
        return value

    @field_validator("title")
    @classmethod
    def _title_no_forbidden_language(cls, value: str) -> str:
        assert_no_forbidden_language(value)
        return value


class SourceReferences(BaseModel):
    """The resource ID references a report was actually generated from --
    resolved server-side, never caller-supplied facts (see module
    docstring's CANONICAL-INPUT RULE). All optional: which fields are
    populated depends on `subject_type` and what was actually found."""

    identity_frek_id: Optional[str] = None
    fk_frek_id: Optional[str] = None
    content_binding_id: Optional[str] = None
    creative_lifecycle_pre_id: Optional[str] = None
    creative_lifecycle_event_ids: List[str] = Field(default_factory=list)
    relationship_ids: List[str] = Field(default_factory=list)
    offline_transport_envelope_ids: List[str] = Field(default_factory=list)
    notary_payload_ids: List[str] = Field(default_factory=list)


class TechnicalEvidenceReport(BaseModel):
    """The canonical, structured report model. JSON and human-text output
    are both derived from this same model (routes.py) -- neither is a
    second source of truth (OUTPUT_FORMAT guidance).

    `is_snapshot` distinguishes a live, on-demand composition (False) from
    an immutable, persisted historical snapshot (True, once stored in
    `db.technical_evidence_reports` -- see routes.py). `report_hash` is
    computed over the content fields only (never `verification_time`, so
    re-verifying identical content at a later time does not change the
    hash -- see canonical.py)."""

    report_id: str
    report_schema_version: str = "1.0.0"
    generator_version: str = "1.0.0"
    generated_at: str = Field(default_factory=_now_iso)
    verification_time: str = Field(default_factory=_now_iso)
    subject_type: ReportSubjectType
    subject_id: str
    source_refs: SourceReferences = Field(default_factory=SourceReferences)
    sections: List[ReportSection] = Field(default_factory=list)
    legal_disclaimer: str = LEGAL_DISCLAIMER
    report_hash: Optional[str] = None
    is_snapshot: bool = False
    requested_by: Optional[str] = Field(
        None,
        description="identity_engine holder frek_id, if requested by a holder session.",
    )
    requested_authority: Optional[str] = Field(
        None, description="'holder', 'admin', or 'public' (verification endpoint)."
    )

    def to_public_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")
