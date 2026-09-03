"""D2 — Creative Lifecycle: data shapes.

Founder decision D2 (`docs/decisions/0005-d2-creative-lifecycle-founder-
decisions-implemented.md`; reconciliation record:
`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` §D "D2 —
Creative Lifecycle"): PRESERVE + ABSORB the historical GENESIS/WORKSHOP/
METAMORPHOSE/EMISSION/LEGACY vocabulary as a canonical provenance
capability describing HOW a creative object became what it is — never
renamed, never confused with identity lifecycle.

Absolute invariant this module exists to enforce structurally:

    CREATIVE_LIFECYCLE_EQUALS_IDENTITY_LIFECYCLE = FALSE
    GENESIS_EQUALS_LEGAL_AUTHORSHIP = FALSE
    GENESIS_EQUALS_LEGAL_OWNERSHIP = FALSE
    GENESIS_EQUALS_ABSOLUTE_PRIORITY = FALSE

CRITICAL COLLISION, verified this pass (not assumed): `frek_v1` already
uses this exact vocabulary (`frek_v1/models.py:FrekStage`, `STAGE_ORDER`)
for a **participant/badge lifecycle** — `backend/badges/routes.py`
writes a badge's `current_stage: "GENESIS"` directly, and
`frek_v1/stages.py:POST /identity/{frek_id}/stage` records stage
transitions for `db.frek_identities` (event participants), notarized as
`payload_type="stage_transition"`. This module is a **structurally
separate system**: its own collection (`db.creative_lifecycle_events`,
not `db.frek_stages`), its own notarization `payload_type`
(`"creative_lifecycle"`, not `"stage_transition"`), its own authority
model (`identity_engine` holder sessions, not `frek_v1` OAuth2 clients).
Same 5-word vocabulary, deliberately not merged — a creative object's
GENESIS and a badge's GENESIS are different activities about different
kinds of subject, per this session's own entity-taxonomy work
(`docs/architecture/FREK_ID_ENTITY_TAXONOMY.md`).

Historical semantics (`backend/frek/nodes/node03_cycle.py`, the real
source this module preserves and hardens — evidence, not invention):

- GENESIS: an actor declares creative intent (`{concept, lieu,
  description}`), before any finished work exists. Gets a provisional
  `pre_id` — NOT a FREK Object identity (`frek_id`). "L'oeuvre existe
  dans FREK avant d'exister dans le monde."
- WORKSHOP: repeatable — private, timestamped intermediate versions.
  Historically guarded: only allowed while the lifecycle's current stage
  is GENESIS or WORKSHOP itself (`node03_cycle.py:150-151`).
- METAMORPHOSE: the final version is submitted; a coherence score is
  computed against the WORKSHOP versions. Historically **unguarded** —
  callable regardless of current stage, as long as the `pre_id` exists
  (confirmed by reading `submit_final()`: no stage check at all). This
  module preserves that permissiveness rather than inventing a stricter
  rule the historical code never had.
- EMISSION: the work receives its real FREK Object identity
  (`fk_frek_id`, this module's evolution of `cycle.frek_id_final`) and
  goes public. Historically **strictly guarded**: only allowed when the
  current stage is exactly METAMORPHOSE (`node03_cycle.py:262-263`).
- LEGACY: a derived/child work (sample, remix) is linked to this one as
  its parent. Historically requires the parent to already carry an
  assigned `frek_id_final` (i.e., to have reached EMISSION at some
  point) — no additional stage check beyond that.

**Real finding preserved deliberately, not "fixed" as a bug**: because
METAMORPHOSE has no stage guard and unconditionally sets the current
stage to METAMORPHOSE, and EMISSION's guard only checks the *current*
stage (not "ever reached"), the real historical state machine allows
GENESIS -> WORKSHOP -> METAMORPHOSE -> EMISSION -> METAMORPHOSE ->
EMISSION -> LEGACY: re-entering METAMORPHOSE after EMISSION makes a
second EMISSION callable again. This is the evidence behind
`LIFECYCLE_MODEL = HYBRID` (not `LINEAR`, not free-form `EVENT_BASED`) —
see `service.py`'s guard functions, which encode exactly this, not a
simplified one-way enum.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from proof_engine.evidence_semantics import Claim, Evidence


class LifecycleStage(str, Enum):
    """The historical vocabulary, verbatim — never renamed."""

    GENESIS = "GENESIS"
    WORKSHOP = "WORKSHOP"
    METAMORPHOSE = "METAMORPHOSE"
    EMISSION = "EMISSION"
    LEGACY = "LEGACY"


# Same ordering as frek_v1.models.STAGE_ORDER and node03_cycle.Stade —
# used only for the WORKSHOP-repeatability guard (service.py), never to
# imply the lifecycle is a strict one-way sequence (it is not — see the
# module docstring's finding on METAMORPHOSE/EMISSION re-entry).
STAGE_ORDER: Dict[LifecycleStage, int] = {
    LifecycleStage.GENESIS: 1,
    LifecycleStage.WORKSHOP: 2,
    LifecycleStage.METAMORPHOSE: 3,
    LifecycleStage.EMISSION: 4,
    LifecycleStage.LEGACY: 5,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContentBindingRef(BaseModel):
    """A lightweight, inline exact-hash + signal-fingerprint reference
    for lifecycle stages that predate a real FREK Object (GENESIS/
    WORKSHOP/METAMORPHOSE — before `fk_frek_id` exists, D1's own
    `ContentBinding` cannot apply, since it requires an existing `.fk`
    object per its own founder decision). Computed via
    `content_binding.extraction`'s real functions
    (D2_CONSUMES_D1=TRUE, D2_REIMPLEMENTS_D1=FALSE) — never recomputed
    once EMISSION creates the real `.fk`-linked `ContentBinding`."""

    exact_hash: str
    exact_hash_algorithm: str
    signal_fingerprint_algorithm: Optional[str] = None
    signal_fingerprint_algorithm_version: Optional[str] = None
    signal_fingerprint_dimensions: Optional[int] = None


class LifecycleEvent(BaseModel):
    """One append-only record of something happening to a creative
    lifecycle. History is never overwritten or destroyed — the current
    stage is always derived from the latest event (`service.py:
    latest_stage`), never stored as a separately-mutable field, per the
    Event-First Architecture requirement.

    Composed of D6's real `Claim`/`Evidence` primitives (reused, not
    reimplemented) exactly like D1's `ContentBinding` — every event
    literally carries a `Claim` describing what was asserted."""

    event_id: str
    pre_id: str = Field(
        ..., description="Provisional creative-lifecycle identity (never a FREK-ID)."
    )
    stage: LifecycleStage
    sequence: int = Field(
        ..., description="Monotonic per pre_id, mirrors frek_v1/stages.py."
    )
    actor_id: Optional[str] = Field(
        None,
        description="identity_engine holder frek_id, if the submitter authenticated as one.",
    )
    authority: str = Field(..., description="'holder' or 'admin'.")
    claim: Claim
    evidence: List[Evidence] = Field(default_factory=list)
    content_binding_ref: Optional[ContentBindingRef] = None
    fk_frek_id: Optional[str] = Field(
        None,
        description=(
            "The real FREK Object identity this creative lifecycle is bound to. "
            "Unset until EMISSION. Never minted by this module -- always an "
            "existing .fk object's frek_id (FREK_ID_SEPARATED semantics preserved)."
        ),
    )
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_now_iso)
    proof_state: str = Field(default="fingerprint")
    block_height: Optional[int] = None
    block_hash: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")


class LifecycleSummary(BaseModel):
    """Read-model: derived current state + full event history. Nothing
    here is a legal conclusion — see module docstring's invariants."""

    pre_id: str
    current_stage: LifecycleStage
    genesis_actor_id: Optional[str]
    fk_frek_id: Optional[str]
    workshop_version_count: int
    events: List[Dict[str, Any]]
