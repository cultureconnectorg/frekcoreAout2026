"""D3 — Relationship / Provenance Graph: data shapes.

Founder decision D3 (`docs/decisions/0006-d3-relationship-provenance-graph-
founder-decisions-implemented.md`; reconciliation record:
`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` §D "D3 —
Relationship / Provenance Graph"): PRESERVE_MIGRATE the historical FREK
Network (`backend/frek/nodes/node06_reseau.py`) as a modern, canonical
relationship capability, split structurally into two layers that must
never be conflated:

    TRUST_PROVENANCE_GRAPH_EQUALS_CULTURAL_INFERENCE_GRAPH = FALSE
    VERIFIED_RELATION_EQUALS_INFERRED_RELATION = FALSE
    CLAIMED_RELATION_EQUALS_VERIFIED_RELATION = FALSE
    SIMILARITY_EQUALS_FACT = FALSE
    INFLUENCE_EQUALS_FACT = FALSE
    RESONANCE_EQUALS_FACT = FALSE

Both layers live in one collection (`db.relationships`) and share one
schema -- this is a deliberate simplification, not an accidental
conflation: `layer` is *derived* from `predicate` via a fixed, closed
`PREDICATE_TAXONOMY` (never caller-supplied), and the sharpest structural
invariant this module enforces is that a CULTURAL-layer relationship can
never reach `RelationshipStatus.VERIFIED` (`service.py:derive_status` and
`routes.py`'s verify endpoint both check this; see
`test_cultural_relation_can_never_be_marked_verified`). A relationship
*record* is one canonical (subject, predicate, object) slot; independent
assertions about it (from different actors/sources) are preserved
individually as `Assertion`s underneath it -- see `Relationship.assertions`
docstring below for why this shape was chosen over either "one row per
assertion" or "last-write-wins".

HISTORICAL DISCOVERY (this pass, read directly from
`backend/frek/nodes/node06_reseau.py` and `backend/frek/routes_advanced.py`
-- not trusted from the reconciliation report's own prior summary, per
this state's explicit instruction):

- **5 node types**, exactly as the module docstring claims:
  OEUVRE, ARTISTE, LIEU, EPOQUE, FREQUENCE. Confirmed by reading
  `NodeType` directly.
- **17 relation types are DECLARED** in the `RelationType` enum, but only
  **5 are ever actually created** by the one and only code path that
  populates the graph (`register_emission`, called once from
  `frek/pipeline.py`'s `certify()`): `cree_par`, `emis_a`, `contient`,
  `dominante_de`, `similar_to`. The other 12 (`derive_de`, `cree`,
  `collabore_avec`, `influence`, `etudie_a`, `accueille`,
  `resonance_avec`, `periode`, `tendance`, `cluster_frequentiel`,
  `presente_dans`, `cluster`) are vocabulary that was never wired to any
  emitter -- aspirational, not merely undocumented. This is a real
  finding, not an assumption: confirmed by reading every call site of
  `add_edge`/`RelationType.*` in the file and finding none for those 12.
- **Storage**: pure Python-process memory (`self._nodes: Dict`,
  `self._edges: List`), despite the module docstring's own claim
  ("Technologie: PostgreSQL + pgvector (fallback mémoire)") --
  confirmed identical to every other `backend/frek/` node's storage
  story this session has already found (D1, D2): the fallback is the
  only path that has ever executed.
- **Source of edges**: `similar_to` is the only ever-emitted relation
  that is *computed* (via `node05_resonance.py`'s cosine-similarity
  search over D1's 528D vectors, injected into `register_emission` as
  `similar_frek_ids`) -- every other emitted edge (`cree_par`, `emis_a`,
  `contient`, `dominante_de`) is *structural/observed*, derived
  deterministically from the certification call's own inputs (artiste_id,
  gps, timestamp, dominant FFT band), not asserted by any external actor
  and not inferred statistically.
- **Authorization**: zero (`grep -n "Depends|Header|x_admin" frek/
  routes_advanced.py` inside the réseau section: no matches) -- all 7
  routes are unauthenticated public reads, consistent with D1/D2's own
  historical-route findings.
- **Traversal**: `find_path` is a real BFS with a `visited` set (cycles
  cannot loop it) and a caller-supplied `max_depth` (bounded 1-10 by the
  route's own `Query(6, ge=1, le=10)`) -- already the one query in this
  module with real bounds. `get_neighbors`, `get_artiste_graph`,
  `get_lieu_activity` have **no result cap** at all -- unbounded by
  design, safe only because the in-memory graph this state's own historical
  code has ever run against is tiny. This module's own canonical queries
  are bounded explicitly (see `MAX_NEIGHBORS`, `MAX_PATH_DEPTH`,
  `MAX_PATH_NODES_VISITED` below) precisely because a real, durable
  MongoDB-backed graph cannot rely on staying small.

Three of the five node types are not independently-managed registry
entities at all -- they are synthetic, *derived* grouping keys computed
from other data (`LIEU` = `f"GPS-{lat:.2f},{lon:.2f}"`, `EPOQUE` =
`f"{year}-Q{quarter}"`, `FREQUENCE` = `f"FREQ-{band}HZ"`), never created,
looked up, or owned anywhere else in the codebase. `OEUVRE` and `ARTISTE`
are the only two that correspond to something a modern system can resolve
against a real registry (`OEUVRE` -> a `.fk` Cultural Object or a
`creative_lifecycle` `pre_id`; `ARTISTE` -> an `identity_engine`
`frek_persons` identity, though historically `artiste_id` was never
itself validated against one). See `HISTORICAL_NODE_TYPE_TAXONOMY` below.

MODERN REUSE AUDIT (this pass): no existing "relationship" or graph-like
model exists anywhere in modern FREKCORE outside `backend/frek/`
(confirmed by grep across the repo, excluding `frek/`/tests) --
`identity_engine`'s `POST /{frek_id}/reconcile` (`docs/decisions/0003-...`)
is the closest real precedent: a narrow, domain-specific, non-destructive,
append-only relationship record between two identities, with a
holder-or-admin authority pattern this module's own authority checks
follow directly. `permissions/` (Role/Scope/Action/Decision) is real,
tested, pure, but has **zero live callers anywhere in the codebase**
(confirmed by grep) -- there is no established pattern for wiring a
persisted `RoleGrant` store into a live route to imitate. Rather than
invent that infrastructure as an unrequested side effect of D3, this
module reuses `permissions.models.Scope`/`ScopeType` **directly, as the
same type** for a relationship's `visibility` field (never a lookalike
enum) and interprets it with a small, relationship-domain-specific
`service.can_read()` rather than forcing a `RoleGrant`-backed
`permissions.engine.decide()` call this module does not have the
infrastructure to feed honestly yet -- a disclosed tradeoff, not an
oversight; see `service.py`'s `can_read` docstring.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from permissions.models import Scope, ScopeType
from proof_engine.evidence_semantics import Claim, Evidence


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RelationLayer(str, Enum):
    """The absolute semantic split this module exists to enforce
    structurally (TRUST_PROVENANCE_GRAPH_EQUALS_CULTURAL_INFERENCE_GRAPH
    = FALSE). Derived from `predicate` via `PREDICATE_TAXONOMY` --
    never caller-supplied, so a caller can never mislabel a cultural
    inference as a trust fact by simply picking the other layer value."""

    TRUST = "trust"
    CULTURAL = "cultural"


class RelationshipStatus(str, Enum):
    """The semantic-state vocabulary the mission asks for verbatim
    ("claim exists, evidence exists, attested, computed, inferred,
    verified, rejected, revoked, unknown, stale"), DERIVED from D6's real
    `Claim.origin`/`Evidence`/authority fields (`service.py:
    derive_status`) rather than a second, parallel truth model -- this
    enum names states D6's own `ClaimOrigin` does not (VERIFIED,
    REJECTED, REVOKED, STALE, UNKNOWN are about verification/lifecycle,
    not assertion origin), so it is a derived READ-MODEL projection of
    D6 primitives, never a replacement for them.

    CULTURAL-layer relationships can never reach VERIFIED -- enforced in
    `service.py:derive_status` and re-checked in `routes.py`'s verify
    endpoint (SIMILARITY_EQUALS_FACT / INFLUENCE_EQUALS_FACT /
    RESONANCE_EQUALS_FACT = FALSE, structurally, not just documented)."""

    CLAIMED = "claimed"
    ATTESTED = "attested"
    COMPUTED = "computed"
    INFERRED = "inferred"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REVOKED = "revoked"
    STALE = "stale"
    UNKNOWN = "unknown"


class RelationDisposition(str, Enum):
    """Per-historical-type classification, exactly the six values the
    mission's HISTORICAL TAXONOMY section names."""

    UNIVERSAL_TRUST_RELATION = "UNIVERSAL_TRUST_RELATION"
    CULTURAL_RELATION = "CULTURAL_RELATION"
    COMPUTED_RELATION = "COMPUTED_RELATION"
    DOMAIN_SPECIFIC_RELATION = "DOMAIN_SPECIFIC_RELATION"
    LEGACY_ALIAS = "LEGACY_ALIAS"
    NEEDS_MAPPING = "NEEDS_MAPPING"


# ---------------------------------------------------------------------------
# Canonical (modern) predicate taxonomy. This is the CLOSED vocabulary
# `POST /relationships` actually accepts -- `layer` is looked up here, never
# supplied by the caller. Intentionally NOT the mission's illustrative list
# verbatim: inspected first (per REUSE_BEFORE_BUILD=TRUE), trimmed to what
# this state's own acceptance tests and the historical mapping below
# actually need, extensible later without a breaking change (adding a new
# predicate here is additive).
# ---------------------------------------------------------------------------
PREDICATE_TAXONOMY: Dict[str, RelationLayer] = {
    # Layer A -- Trust / Provenance
    "created_by": RelationLayer.TRUST,
    "derived_from": RelationLayer.TRUST,
    "issued_by": RelationLayer.TRUST,
    "certified_by": RelationLayer.TRUST,
    "attested_by": RelationLayer.TRUST,
    "belongs_to": RelationLayer.TRUST,
    "references": RelationLayer.TRUST,
    "produced_by": RelationLayer.TRUST,
    "participated_in": RelationLayer.TRUST,
    "emitted_at": RelationLayer.TRUST,
    "contains": RelationLayer.TRUST,
    # Layer B -- Cultural / Inferred
    "similar_to": RelationLayer.CULTURAL,
    "influenced_by": RelationLayer.CULTURAL,
    "resonates_with": RelationLayer.CULTURAL,
    "co_present_with": RelationLayer.CULTURAL,
    "culturally_related_to": RelationLayer.CULTURAL,
}


# ---------------------------------------------------------------------------
# Historical taxonomy record (5 node types, 17 relation types) -- pure data,
# not wired into route logic beyond `service.map_historical_predicate` and
# the read-only `GET /relationships/historical-taxonomy` endpoint. Preserves
# vocabulary per the mission's explicit "do not delete vocabulary" /
# "do not automatically make all 17 historical relation types canonical
# kernel predicates" instructions. `emitted` records whether
# `register_emission` (the only historical writer) was ever actually
# observed to create an edge of that type -- confirmed by reading the file,
# not assumed from the docstring's "17 types" claim.
# ---------------------------------------------------------------------------
HISTORICAL_NODE_TYPE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "OEUVRE": {
        "disposition": RelationDisposition.UNIVERSAL_TRUST_RELATION,
        "canonical_entity_type": "fk_object_or_creative_lifecycle",
        "note": (
            "The only node type that maps to a real, independently-"
            "resolvable canonical registry entity today (a .fk object "
            "once EMISSION happens, or a creative_lifecycle pre_id "
            "before it)."
        ),
    },
    "ARTISTE": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_entity_type": "identity",
        "note": (
            "Historically a caller-supplied artiste_id, never validated "
            "against identity_engine's frek_persons or any other "
            "registry. Maps conceptually to an identity but was never "
            "actually resolved as one."
        ),
    },
    "LIEU": {
        "disposition": RelationDisposition.DOMAIN_SPECIFIC_RELATION,
        "canonical_entity_type": None,
        "note": (
            "A synthetic, derived grouping key (rounded GPS string), "
            "never an independently created/managed entity anywhere."
        ),
    },
    "EPOQUE": {
        "disposition": RelationDisposition.DOMAIN_SPECIFIC_RELATION,
        "canonical_entity_type": None,
        "note": "A synthetic, derived grouping key (YYYY-QX), same as LIEU.",
    },
    "FREQUENCE": {
        "disposition": RelationDisposition.COMPUTED_RELATION,
        "canonical_entity_type": None,
        "note": (
            "A synthetic, derived grouping key (dominant FFT band), "
            "computed from D1-shaped signal data, never an "
            "independently managed entity."
        ),
    },
}

HISTORICAL_RELATION_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "cree_par": {
        "disposition": RelationDisposition.UNIVERSAL_TRUST_RELATION,
        "canonical_predicate": "created_by",
        "emitted": True,
    },
    "emis_a": {
        "disposition": RelationDisposition.UNIVERSAL_TRUST_RELATION,
        "canonical_predicate": "emitted_at",
        "emitted": True,
    },
    "contient": {
        "disposition": RelationDisposition.UNIVERSAL_TRUST_RELATION,
        "canonical_predicate": "contains",
        "emitted": True,
    },
    "dominante_de": {
        "disposition": RelationDisposition.COMPUTED_RELATION,
        "canonical_predicate": None,
        "emitted": True,
        "note": (
            "Derived from D1-shaped FFT dominant-band computation, never "
            "mapped to a canonical predicate this state -- kept as "
            "historical-only."
        ),
    },
    "similar_to": {
        "disposition": RelationDisposition.COMPUTED_RELATION,
        "canonical_predicate": "similar_to",
        "emitted": True,
    },
    "derive_de": {
        "disposition": RelationDisposition.UNIVERSAL_TRUST_RELATION,
        "canonical_predicate": "derived_from",
        "emitted": False,
    },
    "cree": {
        "disposition": RelationDisposition.LEGACY_ALIAS,
        "canonical_predicate": "created_by",
        "emitted": False,
        "note": (
            "Inverse direction of cree_par -- same fact, opposite edge "
            "direction, never emitted historically."
        ),
    },
    "collabore_avec": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
    "influence": {
        "disposition": RelationDisposition.CULTURAL_RELATION,
        "canonical_predicate": "influenced_by",
        "emitted": False,
    },
    "etudie_a": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
    "accueille": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
    "resonance_avec": {
        "disposition": RelationDisposition.CULTURAL_RELATION,
        "canonical_predicate": "resonates_with",
        "emitted": False,
    },
    "periode": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
    "tendance": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
    "cluster_frequentiel": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
    "presente_dans": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
    "cluster": {
        "disposition": RelationDisposition.NEEDS_MAPPING,
        "canonical_predicate": None,
        "emitted": False,
    },
}


class Assertion(BaseModel):
    """One independent assertion about a canonical Relationship's
    (subject, predicate, object) slot. `A asserts X CREATED_BY Y` and
    `B independently attests X CREATED_BY Y` are TWO Assertions under ONE
    Relationship -- this is the model chosen for "RELATIONSHIP IDENTITY"
    (mission): one canonical slot, multiple provenance-preserving
    assertions, rather than either collapsing them into one row
    (destroying B's independent provenance) or minting two unrelated
    Relationship rows for the same real-world fact (duplicating truth
    semantics the mission explicitly warns against).

    Composed of D6's real `Claim`/`Evidence` primitives directly, exactly
    like D1's `ContentBinding` and D2's `LifecycleEvent`."""

    assertion_id: str
    claim: Claim
    evidence: List[Evidence] = Field(default_factory=list)
    actor_id: Optional[str] = None
    authority: str = Field(..., description="'holder' or 'admin'.")
    created_at: str = Field(default_factory=_now_iso)
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None


class Relationship(BaseModel):
    """One canonical (subject, predicate, object) slot in the graph.

    `subject_id`/`object_id` reference canonical FREKCORE entities where
    resolvable (NODE_IDENTITY_EQUALS_FREK_ID_ALWAYS=FALSE -- see
    `service.resolve_entity_ref`: subjects may be a `.fk` object, a
    `creative_lifecycle` pre_id, an `identity_engine` identity, or an
    unrecognized-but-still-recorded external reference, matching
    `permissions.models.ResourceRef.resource_type`'s own "intentionally
    free-form string" convention).

    `visibility` reuses `permissions.models.Scope`/`ScopeType` directly --
    GLOBAL means public, OBJECT means "restricted to the relationship's
    own parties" (subject_id/object_id/any assertion's actor_id),
    ORGANIZATION/ENTITY restrict to a named id. See `service.can_read`.

    History is never destroyed: revoking or superseding an assertion sets
    `revoked_at`/`revoked_reason` on that Assertion (`routes.py`'s revoke
    endpoint) -- it is never removed from `assertions`, and the
    Relationship document itself is never deleted."""

    relationship_id: str
    subject_id: str
    subject_type: Optional[str] = None
    predicate: str
    object_id: str
    object_type: Optional[str] = None
    layer: RelationLayer
    visibility: Scope = Field(default_factory=lambda: Scope(type=ScopeType.GLOBAL))
    assertions: List[Assertion] = Field(default_factory=list)
    status: RelationshipStatus = RelationshipStatus.UNKNOWN
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    source_event_id: Optional[str] = Field(
        None,
        description=(
            "A creative_lifecycle event_id this relationship is derived "
            "from (D2 reuse -- D3_CONSUMES_D2=TRUE, D3_REIMPLEMENTS_D2="
            "FALSE: this is a reference, D2's own lifecycle logic is "
            "never re-executed here)."
        ),
    )
    source_content_binding_id: Optional[str] = Field(
        None,
        description="A content_binding binding_id this relationship is derived from (D1 reuse).",
    )
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)

    def to_public_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")
