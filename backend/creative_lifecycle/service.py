"""D2 — pure logic: transition guards + coherence scoring.

Kept free of FastAPI/Mongo/notary so the guard rules (the actual
evidence-derived answer to "is this lifecycle linear, event-based, or
hybrid" — see `models.py`'s module docstring) are unit-testable in
isolation, the same discipline `content_binding/extraction.py` (D1)
established.

Coherence scoring is ported from `frek/nodes/node03_cycle.py:
Node03Cycle._calculate_coherence` (cosine similarity between a WORKSHOP
version's signal fingerprint and the METAMORPHOSE submission's) — the
same algorithm, not a duplicate concept: `node03_cycle.py`'s own version
compares vectors it received directly; this one compares
`ContentBindingRef`s built from D1's real extraction output, so no
signal-processing logic is reimplemented here, only the comparison
FREK's own D2 stage always owned.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence

from .models import STAGE_ORDER, LifecycleStage


def latest_stage(events: Sequence[dict]) -> Optional[LifecycleStage]:
    """The lifecycle's current stage is always the most recent event's
    stage -- never a separately-mutated field, and never "the highest
    stage ever reached" (that would silently turn the real, evidenced
    hybrid state machine into a one-way ratchet it historically never
    was -- see models.py's module docstring finding)."""
    if not events:
        return None
    return LifecycleStage(events[-1]["stage"])


def can_start_workshop(current: Optional[LifecycleStage]) -> bool:
    """Historical guard (node03_cycle.py:150-151): WORKSHOP requires
    GENESIS to have happened, and is rejected once the lifecycle has
    moved strictly past WORKSHOP."""
    if current is None:
        return False
    return STAGE_ORDER[current] <= STAGE_ORDER[LifecycleStage.WORKSHOP]


def can_metamorphose(current: Optional[LifecycleStage]) -> bool:
    """Historical finding: `submit_final()` has NO stage guard at all --
    only existence of the pre_id (i.e., GENESIS having happened) is
    required. Preserved deliberately, not tightened, per the explicit
    'DO NOT INVENT THIS ANSWER' instruction."""
    return current is not None


def can_emit(current: Optional[LifecycleStage]) -> bool:
    """Historical guard (node03_cycle.py:262-263): EMISSION requires the
    *current* stage to be exactly METAMORPHOSE -- strict, and re-checked
    fresh each time (not "was METAMORPHOSE reached at some point"),
    which is exactly what makes METAMORPHOSE -> EMISSION -> METAMORPHOSE
    -> EMISSION a real, evidenced possibility rather than a bug."""
    return current == LifecycleStage.METAMORPHOSE


def can_declare_legacy(parent_fk_frek_id: Optional[str]) -> bool:
    """Historical guard (node03_cycle.py:add_child): LEGACY requires the
    parent to already carry an assigned frek_id_final (this module's
    fk_frek_id) -- i.e., to have reached EMISSION at some point. No
    additional current-stage check beyond that, matching the evidence."""
    return parent_fk_frek_id is not None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Same algorithm as node03_cycle.py:_calculate_coherence's inner
    loop, generalized to one pair. Returns 0.0 for degenerate (zero-norm)
    vectors rather than raising -- matches the historical function's own
    `if norm_a > 0 and norm_b > 0` guard."""
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    a2, b2 = a[:n], b[:n]
    dot = sum(x * y for x, y in zip(a2, b2))
    norm_a = math.sqrt(sum(x * x for x in a2))
    norm_b = math.sqrt(sum(y * y for y in b2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, dot / (norm_a * norm_b))


def coherence_score(
    workshop_vectors: List[List[float]], final_vector: List[float]
) -> float:
    """Mean cosine similarity (as a 0-100 percentage) between the final
    METAMORPHOSE vector and each WORKSHOP version's vector. No workshop
    versions -> 100.0 (perfect coherence by definition, matching
    node03_cycle.py's own `if not workshop_versions: return 100.0`)."""
    if not workshop_vectors:
        return 100.0
    similarities = [cosine_similarity(final_vector, v) for v in workshop_vectors]
    return round(sum(similarities) / len(similarities) * 100, 2)
