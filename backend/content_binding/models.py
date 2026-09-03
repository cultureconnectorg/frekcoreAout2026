"""D1 — Signal Fingerprint / Content Binding: data shapes.

Founder decision D1 (docs/decisions/0004-d1-signal-fingerprint-founder-
decisions-implemented.md; reconciliation record:
reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md section D "D1 —
Signal / Audio Fingerprint"): PRESERVE the historical audio-fingerprint
capability (`backend/frek/nodes/node01_extraction.py`'s real 6-algorithm
528-dimension extraction pipeline), but stop conflating it with FREK-ID.

The absolute invariant this module exists to enforce structurally, not
just in prose:

    FREK_ID_EQUALS_SIGNAL_FINGERPRINT = FALSE
    CRYPTOGRAPHIC_HASH_EQUALS_SIGNAL_FINGERPRINT = FALSE

A `ContentBinding` is evidence ABOUT an already-existing FREK Object
(a `.fk` Cultural Object, identified by its own `frek_id` minted by
`backend/fk/routes.py:create_fk_endpoint` — the real, durable, signed
identity mechanism). This module never mints an identity of its own.

Two distinct binding types, never merged into one value:

- `exact_hash`      — SHA-256 over the raw content bytes. Answers "is
                        this exactly the same binary content?" Reuses the
                        identical hashing convention already used by
                        `.fk`'s own `MediaItem.sha256` and `notary`'s
                        block hashing — not a new hash scheme.
- `signal_fingerprint` — the 528-dimension perceptual/signal vector
                        (512 FFT bands + RMS + ZCR + 12 MFCC + centroid +
                        flux — `node01_extraction.py`'s real algorithm,
                        reused verbatim, not reimplemented). Answers "does
                        this signal correspond to the same underlying
                        sound, per this specific algorithm/version?" —
                        a computed similarity artifact, never a verified
                        identity claim (D6 evidence semantics).

No property of the signal fingerprint (compression robustness, noise
robustness, re-recording robustness, collision resistance) is asserted
here. See reports/FREKCORE_D1_VALIDATION_EVIDENCE.md for exactly what was
and was not demonstrated, and with what result.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from proof_engine.evidence_semantics import Claim, ClaimOrigin, Evidence, EvidenceKind

# Algorithm identity — versioned per D1's explicit requirement
# (FINGERPRINT_WITHOUT_ALGORITHM_VERSION = INVALID_CANONICAL_DESIGN). A
# future algorithm change ships as a NEW algorithm_id/version pair, never
# a silent redefinition of this one — old bindings stay valid and
# comparable to what they actually were computed with.
SIGNAL_ALGORITHM_ID = "frek_signal_v1"
SIGNAL_ALGORITHM_VERSION = "1.0.0"

# Exact-hash side is just SHA-256 — no versioning needed, it is not an
# evolving algorithm, it is a fixed cryptographic primitive already used
# identically everywhere else in this codebase (.fk, notary, passport).
EXACT_HASH_ALGORITHM_ID = "sha256"

BindingType = Literal["exact_hash", "signal_fingerprint"]

# Historical/legacy identifier compatibility (per the state-1 mission's
# explicit rule): the pre-existing `backend/frek/` module derives its own
# "FREK-ID" from a fingerprint+hash chain
# (`node02_identity.py:generate_identity`). That identifier is NEITHER
# deleted NOR promoted to canonical FREK-ID status here — evidence does
# not support that (no live caller found referencing it, see the
# reconciliation report's point 12). It is recorded, when supplied, as an
# explicit `legacy_identifier` compatibility field — never silently
# dropped, never silently treated as this module's own `frek_id`.


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SignalFingerprintData(BaseModel):
    """The computed perceptual/signal vector plus everything needed to
    know exactly what produced it (D1's ALGORITHM_ID/ALGORITHM_VERSION/
    INPUT_FORMAT_ASSUMPTIONS/OUTPUT_SHAPE requirement)."""

    algorithm: str = SIGNAL_ALGORITHM_ID
    algorithm_version: str = SIGNAL_ALGORITHM_VERSION
    dimensions: int = 528
    vector: List[float]
    sample_rate: int
    duration_seconds: float


class ContentBinding(BaseModel):
    """One computed binding between raw content and an existing FREK
    Object. Persisted as-is in `db.content_bindings` (Mongo, the existing
    project-wide storage convention — no new database technology
    introduced, per the founder's explicit
    DO_NOT_FORCE_POSTGRES/DO_NOT_FORCE_PGVECTOR/DO_NOT_FORCE_NEW_DATABASE
    instruction: these 3 routes only ever need exact lookup by frek_id or
    binding_id, never similarity search, so plain Mongo already satisfies
    D1's actual requirement)."""

    binding_id: str
    frek_id: str = Field(
        ..., description="The .fk Cultural Object this binding is evidence about."
    )
    exact_hash: str
    exact_hash_algorithm: str = EXACT_HASH_ALGORITHM_ID
    signal_fingerprint: SignalFingerprintData
    legacy_identifier: Optional[str] = Field(
        default=None,
        description=(
            "Compatibility reference only — the historical backend/frek/ "
            "module's own generated identifier, when the caller supplies "
            "one. Never treated as this binding's or the object's "
            "canonical frek_id."
        ),
    )
    computed_at: str = Field(default_factory=_now_iso)
    produced_by: str = Field(
        ..., description="'holder' (self-attested via X-FREK-Session) or 'admin'."
    )
    claim: Claim = Field(
        description=(
            "D6's Claim primitive (proof_engine/evidence_semantics.py), "
            "reused unmodified: 'this content is bound to this FREK "
            "Object' is an assertion, origin=COMPUTED (its content is a "
            "deterministic algorithm's output, not a bare human "
            "statement) -- never itself evidence, proof, or a verified "
            "fact (D6_INVARIANTS_MUST_REMAIN_TRUE)."
        )
    )
    evidence: List[Evidence] = Field(
        description=(
            "D6's Evidence primitive, one record per binding_type "
            "(exact_hash, signal_fingerprint) -- material supporting the "
            "claim above, still not proof by itself. "
            "Evidence.to_proof_state_hint() returns None for both (kind="
            "COMPUTATION has no unambiguous proof-engine equivalent by "
            "design), which is exactly why `proof_state` below is only "
            "ever set from real notarization, never inferred from the "
            "evidence's mere existence."
        )
    )
    proof_state: str = Field(
        default="fingerprint",
        description=(
            "proof_engine.ProofState value — 'fingerprint' (hash/vector "
            "computed, nothing else) until notarized into notary's real "
            "hash chain, then 'local_proof'. Reused unmodified from "
            "proof_engine/models.py, not a new proof-state vocabulary."
        ),
    )
    block_height: Optional[int] = None
    block_hash: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        """What a GET response returns, and what is stored in
        `db.content_bindings` — everything, this is evidence data meant
        to be inspectable, not a secret. `mode="json"` so nested `Claim`/
        `Evidence` datetimes and enums serialize to plain strings, the
        same convention every other timestamp in this codebase already
        uses (ISO 8601 strings, not native datetime objects)."""
        return self.model_dump(mode="json")


def build_claim_and_evidence(
    *,
    frek_id: str,
    exact_hash: str,
    fingerprint: SignalFingerprintData,
    produced_by_id: str,
) -> tuple[Claim, List[Evidence]]:
    """Construct the D6 `Claim` + `Evidence` records a content binding is
    actually made of — real reuse of `proof_engine.evidence_semantics`,
    not a parallel model that merely resembles it. Called once per
    binding creation (`content_binding/routes.py:create_content_binding`).

    origin=ClaimOrigin.COMPUTED, not DECLARED: the claim's substance (the
    hash/fingerprint values) is a deterministic algorithm's output, not a
    bare human assertion — matching ClaimOrigin's own docstring example
    ("Derived by a deterministic algorithm (e.g. a hash)").
    """
    claim = Claim(
        subject_id=frek_id,
        claimant_id=produced_by_id,
        origin=ClaimOrigin.COMPUTED,
        statement=(
            f"Content bound to FREK Object {frek_id}: exact_hash={exact_hash[:16]}..., "
            f"signal_fingerprint via {fingerprint.algorithm}/{fingerprint.algorithm_version}."
        ),
        data={"frek_id": frek_id, "exact_hash": exact_hash},
    )
    evidence = [
        Evidence(
            subject_id=frek_id,
            kind=EvidenceKind.COMPUTATION,
            data={"algorithm": EXACT_HASH_ALGORITHM_ID, "value": exact_hash},
            produced_by=produced_by_id,
        ),
        Evidence(
            subject_id=frek_id,
            kind=EvidenceKind.COMPUTATION,
            data={
                "algorithm": fingerprint.algorithm,
                "algorithm_version": fingerprint.algorithm_version,
                "dimensions": fingerprint.dimensions,
            },
            produced_by=produced_by_id,
        ),
    ]
    return claim, evidence
