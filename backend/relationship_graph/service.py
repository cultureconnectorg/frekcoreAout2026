"""D3 -- pure logic: layer resolution, derived status, visibility,
bounded traversal. Kept free of FastAPI/Mongo/notary (same discipline as
`content_binding/extraction.py` and `creative_lifecycle/service.py`) so
this state's sharpest invariants -- a cultural relation can never be
VERIFIED, traversal is always bounded -- are unit-testable in isolation.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional, Sequence

from proof_engine.evidence_semantics import ClaimOrigin
from permissions.models import Scope, ScopeType

from .models import (
    HISTORICAL_RELATION_TAXONOMY,
    PREDICATE_TAXONOMY,
    Assertion,
    RelationLayer,
    RelationshipStatus,
)

# ---------------------------------------------------------------------------
# Bounded traversal limits (UNBOUNDED_GRAPH_TRAVERSAL=FALSE). The historical
# find_path already bounded depth (1-10); this module additionally bounds
# per-node fan-out and total nodes visited, since a real MongoDB-backed
# graph -- unlike node06's tiny in-memory one -- cannot rely on staying
# small.
# ---------------------------------------------------------------------------
MAX_NEIGHBORS = 200
MAX_PATH_DEPTH = 6
MAX_PATH_DEPTH_HARD_CAP = 10
MAX_PATH_NODES_VISITED = 2000


class UnknownPredicateError(ValueError):
    """Raised when a caller submits a predicate outside PREDICATE_TAXONOMY
    -- the closed vocabulary is enforced here, once, not scattered across
    call sites."""


def resolve_layer(predicate: str) -> RelationLayer:
    """TRUST_PROVENANCE_GRAPH_EQUALS_CULTURAL_INFERENCE_GRAPH=FALSE,
    enforced structurally: layer is looked up from the closed
    PREDICATE_TAXONOMY, never accepted as a caller-supplied field, so a
    caller cannot mislabel a cultural inference as a trust fact."""
    layer = PREDICATE_TAXONOMY.get(predicate)
    if layer is None:
        raise UnknownPredicateError(
            f"unknown predicate {predicate!r}; not in PREDICATE_TAXONOMY"
        )
    return layer


def map_historical_predicate(historical_relation_type: str) -> Optional[Dict[str, Any]]:
    """Looks up a historical (node06_reseau.py) relation type's recorded
    disposition -- pure data lookup, preserves vocabulary without
    resurrecting it as a live predicate (HISTORICAL_TAXONOMY_MAPPED)."""
    return HISTORICAL_RELATION_TAXONOMY.get(historical_relation_type)


_ORIGIN_TO_STATUS = {
    ClaimOrigin.DECLARED: RelationshipStatus.CLAIMED,
    ClaimOrigin.OBSERVED: RelationshipStatus.CLAIMED,
    ClaimOrigin.ATTESTED: RelationshipStatus.ATTESTED,
    ClaimOrigin.COMPUTED: RelationshipStatus.COMPUTED,
    ClaimOrigin.INFERRED: RelationshipStatus.INFERRED,
}

_STATUS_RANK = {
    RelationshipStatus.UNKNOWN: 0,
    RelationshipStatus.CLAIMED: 1,
    RelationshipStatus.COMPUTED: 2,
    RelationshipStatus.INFERRED: 2,
    RelationshipStatus.ATTESTED: 3,
    RelationshipStatus.VERIFIED: 4,
}


def derive_status(
    layer: RelationLayer,
    assertions: Sequence[Assertion],
    *,
    verified: bool = False,
) -> RelationshipStatus:
    """Derives the relationship-level status from its assertions --
    a READ-MODEL projection of D6's real Claim.origin, never a second
    truth model (see models.py's module docstring).

    The one hard, structurally-enforced rule
    (SIMILARITY_EQUALS_FACT=FALSE / INFLUENCE_EQUALS_FACT=FALSE /
    RESONANCE_EQUALS_FACT=FALSE): a CULTURAL-layer relationship can
    NEVER derive to VERIFIED, regardless of what `verified` is passed --
    only TRUST-layer relationships can. Revocation of every assertion
    takes precedence over everything else: a fully-revoked relationship
    reads REVOKED, never a stale non-revoked status."""
    live = [a for a in assertions if not a.revoked_at]
    if assertions and not live:
        return RelationshipStatus.REVOKED
    if not live:
        return RelationshipStatus.UNKNOWN

    if verified and layer == RelationLayer.TRUST:
        return RelationshipStatus.VERIFIED

    best = RelationshipStatus.UNKNOWN
    for a in live:
        candidate = _ORIGIN_TO_STATUS.get(a.claim.origin, RelationshipStatus.UNKNOWN)
        if _STATUS_RANK[candidate] > _STATUS_RANK[best]:
            best = candidate
    return best


def dedup_key(
    subject_id: str,
    predicate: str,
    object_id: str,
    actor_id: Optional[str],
    origin: ClaimOrigin,
) -> tuple:
    """Same actor asserting the identical (subject, predicate, object)
    tuple with the identical origin again is a retry, not a new
    assertion (test #14). A DIFFERENT actor asserting the same tuple is
    NOT collapsed -- distinct provenance is preserved (test #15):
    SAME_SUBJECT_PREDICATE_OBJECT != SAME_ASSERTION, enforced by keying
    on actor_id too."""
    return (subject_id, predicate, object_id, actor_id, origin.value)


def can_read(
    visibility: Scope,
    *,
    actor_id: Optional[str],
    is_admin: bool,
    parties: Sequence[Optional[str]],
) -> bool:
    """Interprets `permissions.models.Scope` directly for relationship
    read-visibility (CREATE_SECOND_VISIBILITY_SYSTEM=FALSE) --
    VERIFIABILITY != DISCLOSURE, so this governs READ only, never whether
    a relationship *can* reach VERIFIED.

    Deliberately does NOT call `permissions.engine.decide()`: that engine
    resolves a `Subject.roles: List[RoleGrant]`, and no RoleGrant
    persistence exists anywhere in this codebase yet (confirmed: zero
    live callers of permissions/ at all) -- wiring a RoleGrant store
    would be inventing unrequested new infrastructure, not reuse. Reusing
    the `Scope`/`ScopeType` TYPE directly (never a lookalike enum) while
    interpreting it with this small, honest, relationship-domain-specific
    function is the disclosed tradeoff (see models.py's module docstring).

    - GLOBAL: always visible.
    - OBJECT: visible only to a "party" -- the relationship's own
      subject_id/object_id, or any assertion's actor_id -- or admin.
    - ENTITY: visible if actor_id == scope.id, or admin.
    - ORGANIZATION: admin-only this state -- no org-membership resolver
      exists anywhere reachable in scope to check it honestly otherwise;
      a real gap, disclosed here rather than silently defaulting to
      "visible".
    """
    if is_admin:
        return True
    if visibility.type == ScopeType.GLOBAL:
        return True
    if actor_id is None:
        return False
    if visibility.type == ScopeType.OBJECT:
        return actor_id in {p for p in parties if p}
    if visibility.type == ScopeType.ENTITY:
        return actor_id == visibility.id
    if visibility.type == ScopeType.ORGANIZATION:
        return False
    return False  # pragma: no cover - exhaustive over ScopeType


def bounded_neighbors(
    edges: Sequence[dict],
    node_id: str,
    *,
    direction: str = "both",
    limit: int = MAX_NEIGHBORS,
) -> List[dict]:
    """Adjacency-query-shaped neighbor lookup, bounded at `limit`
    (UNBOUNDED_GRAPH_TRAVERSAL=FALSE) -- unlike node06_reseau.py's
    get_neighbors, which returns every match with no cap."""
    out: List[dict] = []
    for e in edges:
        if len(out) >= limit:
            break
        if direction in ("outgoing", "both") and e["subject_id"] == node_id:
            out.append({**e, "direction": "outgoing"})
        elif direction in ("incoming", "both") and e["object_id"] == node_id:
            out.append({**e, "direction": "incoming"})
    return out[:limit]


def bounded_path(
    edges: Sequence[dict],
    start_id: str,
    end_id: str,
    *,
    max_depth: int = MAX_PATH_DEPTH,
    max_nodes_visited: int = MAX_PATH_NODES_VISITED,
) -> Optional[List[dict]]:
    """BFS shortest path, same algorithm shape as node06_reseau.py's
    find_path (a `visited` set already makes it cycle-safe -- confirmed
    by reading it), with one addition: a hard cap on total nodes visited
    (`max_nodes_visited`), not just depth, since a real durable graph's
    per-level fan-out is not guaranteed small the way the historical
    in-memory graph's always was."""
    if max_depth > MAX_PATH_DEPTH_HARD_CAP:
        raise ValueError(
            f"max_depth {max_depth} exceeds hard cap {MAX_PATH_DEPTH_HARD_CAP}"
        )
    if start_id == end_id:
        return [{"node_id": start_id, "depth": 0}]

    adjacency: Dict[str, List[dict]] = {}
    for e in edges:
        adjacency.setdefault(e["subject_id"], []).append(
            {"node_id": e["object_id"], "predicate": e["predicate"]}
        )
        adjacency.setdefault(e["object_id"], []).append(
            {"node_id": e["subject_id"], "predicate": e["predicate"]}
        )

    visited = {start_id}
    queue = deque([(start_id, [{"node_id": start_id, "depth": 0}])])
    nodes_visited = 1

    while queue:
        current_id, path = queue.popleft()
        if len(path) > max_depth:
            continue
        for neighbor in adjacency.get(current_id, []):
            neighbor_id = neighbor["node_id"]
            if neighbor_id == end_id:
                return path + [
                    {
                        "node_id": neighbor_id,
                        "depth": len(path),
                        "via_predicate": neighbor["predicate"],
                    }
                ]
            if neighbor_id in visited:
                continue
            if nodes_visited >= max_nodes_visited:
                return None
            visited.add(neighbor_id)
            nodes_visited += 1
            queue.append(
                (
                    neighbor_id,
                    path
                    + [
                        {
                            "node_id": neighbor_id,
                            "depth": len(path),
                            "via_predicate": neighbor["predicate"],
                        }
                    ],
                )
            )

    return None
