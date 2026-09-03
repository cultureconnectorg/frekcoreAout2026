"""D5 -- canonical serialization + report integrity hash.

Same `sort_keys=True, separators=(",", ":")` formula independently kept
by `fk/packager.py:canonical_json`, `notary/chain.py:_canonical_json`,
and `offline_transport/canonical.py:canonical_json` -- this module keeps
its own local copy too, following the same established repo-wide
convention (each module owns its copy rather than importing a shared
one) rather than inventing a fourth serialization scheme.

REPORT INTEGRITY (mission's own requirement): a deterministic hash over
the report's *content* fields, never over `verification_time` (which
changes every time a report is re-verified without the underlying facts
changing) and never over `report_hash` itself. This is what lets a
public verifier confirm "this is exactly the report FREKCORE generated"
without re-trusting the transport that carried the JSON to them --
evidence of integrity, still never a legal signature/notarial act (see
models.py's `LEGAL_DISCLAIMER`)."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .models import TechnicalEvidenceReport

# Fields that make up the report's content identity. Deliberately excludes
# `report_hash` (circular) and `verification_time` (re-verification should
# not change the hash of unchanged content) and `is_snapshot` (a storage
# fact about the report, not part of what it says).
HASHABLE_FIELDS = (
    "report_id",
    "report_schema_version",
    "generator_version",
    "generated_at",
    "subject_type",
    "subject_id",
    "source_refs",
    "sections",
    "legal_disclaimer",
)


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def signable_core(report: "TechnicalEvidenceReport") -> Dict[str, Any]:
    full = report.model_dump(mode="json")
    return {k: full[k] for k in HASHABLE_FIELDS}


def compute_report_hash(report: "TechnicalEvidenceReport") -> str:
    payload = canonical_json(signable_core(report)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
