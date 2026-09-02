# 0006 — Founder Decision D3: Relationship / Provenance Graph (APPROVED, IMPLEMENTED)

Status: **DECIDED, IMPLEMENTED**. Records the founder's D3 decision from
`FREKCORE_EXECUTION_PROTOCOL_V1` §STATE_3 (2026-09-02) and how it was
carried out. Background: `reports/FREKCORE_HISTORICAL_CAPABILITY_
RECONCILIATION.md` §D "D3 — Relationship / Provenance Graph" (the
reconciliation pass that first surfaced D3 as one of 5 historical
capabilities requiring a founder decision, out of the 19 `backend/frek/`
routes).

## Founder decision, verbatim (paraphrased from the execution protocol)

**D3 = PRESERVE_MIGRATE.** The historical FREK Network
(`backend/frek/nodes/node06_reseau.py`) must be reconciled and
implemented as a modern, canonical relationship/provenance capability
without conflating:

    TRUST_PROVENANCE_GRAPH_EQUALS_CULTURAL_INFERENCE_GRAPH = FALSE
    VERIFIED_RELATION_EQUALS_INFERRED_RELATION = FALSE
    CLAIMED_RELATION_EQUALS_VERIFIED_RELATION = FALSE
    SIMILARITY_EQUALS_FACT = FALSE
    INFLUENCE_EQUALS_FACT = FALSE
    RESONANCE_EQUALS_FACT = FALSE
    PUBLIC_RELATION_EQUALS_TRUE_RELATION = FALSE
    TRUE_RELATION_EQUALS_PUBLIC_RELATION = FALSE

Two structurally distinct layers were required: **Layer A (Trust /
Provenance)** — verifiable, attestable relationships with known source
and authority — and **Layer B (Cultural / Inferred)** — similarity,
influence, resonance and other non-verified relationships, which "may
originate from human declaration, AI inference, statistical computation,
signal similarity, historical analysis, editorial assertion, external
dataset" and "are NOT automatically verified facts." D6 semantics were
mandatory throughout; D2's real lifecycle events had to be referenceable
(`D3_CONSUMES_D2=TRUE`, `D3_REIMPLEMENTS_D2=FALSE`); D1's own
verification status could not be silently upgraded
(`D1_VERIFIED` stays `PARTIAL`).

## Historical discovery (evidence, not the reconciliation report's own prior summary)

Read directly from `backend/frek/nodes/node06_reseau.py` and
`backend/frek/routes_advanced.py`:

- **5 node types**: OEUVRE, ARTISTE, LIEU, EPOQUE, FREQUENCE — confirmed.
- **17 relation types are declared**, but only **5 are ever actually
  emitted** by the one code path that populates the graph
  (`register_emission`, called from `frek/pipeline.py`'s `certify()`):
  `cree_par`, `emis_a`, `contient`, `dominante_de`, `similar_to`. The
  other 12 are vocabulary that was never wired to any emitter —
  confirmed by reading every call site of `add_edge`, not assumed from
  the module's own "17 types" docstring claim.
- **Storage**: pure Python-process memory, despite the module's own
  docstring claiming "PostgreSQL + pgvector (fallback mémoire)" —
  the fallback is the only path that has ever executed, identical to
  every other `backend/frek/` node's storage story (D1, D2).
- **`similar_to` is the only computed/inferred emitted edge** (via
  `node05_resonance.py`'s cosine-similarity search over D1's 528D
  vectors); every other emitted edge is structural/observed, derived
  deterministically from the certification call's own inputs.
- **Authorization**: zero — all 7 routes are unauthenticated public
  reads (confirmed by grep), consistent with D1/D2's historical-route
  findings.
- **Traversal**: `find_path` is a real, cycle-safe BFS with a bounded
  `max_depth` (1-10) — already this module's one bounded query.
  `get_neighbors`/`get_artiste_graph`/`get_lieu_activity` have **no
  result cap at all**.
- **Three of the five node types are not independently-managed registry
  entities** — LIEU/EPOQUE/FREQUENCE are synthetic, derived grouping
  keys, never created or owned anywhere else. Only OEUVRE and ARTISTE
  correspond to something resolvable against a real registry today.

Full per-type disposition record: `backend/relationship_graph/models.py`'s
`HISTORICAL_NODE_TYPE_TAXONOMY` and `HISTORICAL_RELATION_TAXONOMY` (also
exposed read-only at `GET /api/v1/relationships/historical-taxonomy`).

## Modern reuse audit

No existing "relationship" or graph-like model exists anywhere in modern
FREKCORE outside `backend/frek/` (confirmed by grep across the repo).
`identity_engine`'s `POST /{frek_id}/reconcile` is the closest real
precedent — a narrow, non-destructive, append-only relationship record
between two identities — and its holder-or-admin authority pattern is
followed directly here. `permissions/` (Role/Scope/Action/Decision) is
real and tested but has **zero live callers anywhere in the codebase**
(confirmed by grep) — there is no established pattern for wiring a
persisted `RoleGrant` store into a live route. Rather than invent that
infrastructure as an unrequested side effect of D3, this module reuses
`permissions.models.Scope`/`ScopeType` **directly, as the same type**,
for a relationship's `visibility` field, interpreted by a small,
domain-specific `relationship_graph.service.can_read()` rather than a
full `permissions.engine.decide()` call this module has no `RoleGrant`
store to feed honestly — a disclosed tradeoff, not an oversight.

## What was implemented

**`backend/relationship_graph/`** (new module):

- `models.py` — `RelationLayer` (TRUST/CULTURAL, *derived* from
  predicate via a closed `PREDICATE_TAXONOMY`, never caller-supplied),
  `RelationshipStatus` (CLAIMED/ATTESTED/COMPUTED/INFERRED/VERIFIED/
  REJECTED/REVOKED/STALE/UNKNOWN — a read-model projection of D6's real
  `Claim.origin`, not a second truth model), `Assertion` (composed of
  D6's real `Claim`/`Evidence` directly), `Relationship` (one canonical
  (subject, predicate, object) slot holding a list of independently-
  provenanced `Assertion`s, plus `visibility: Scope`,
  `source_event_id`/`source_content_binding_id` for D2/D1 references).
- `service.py` — pure functions: `resolve_layer` (the structural
  TRUST/CULTURAL enforcement point), `derive_status` (the structural
  point where a CULTURAL relationship can **never** reach VERIFIED,
  regardless of what is asked for), `can_read` (the `Scope`
  interpretation), `dedup_key`, `bounded_neighbors`/`bounded_path`
  (BFS, cycle-safe like the historical `find_path`, with an added
  total-nodes-visited cap the historical code never needed for its tiny
  in-memory graph).
- `routes.py` — `POST /api/v1/relationships` (create/assert, idempotent
  per (subject, predicate, object, actor, origin)), `GET .../{id}`,
  `GET .../{id}/history`, `GET .../entity/{id}/neighbors|outgoing|
  incoming` (all bounded), `GET .../traverse/path` (bounded BFS, hard-
  capped `max_depth`), `POST .../{id}/verify` (admin-only, TRUST-layer
  only — 409 on CULTURAL), `POST .../{id}/revoke` (owner-or-admin,
  never deletes), `GET .../historical-taxonomy` (public record of the
  5 node types / 17 relation types and their disposition).

**A real defect an earlier draft of this endpoint would have had**,
caught before it was ever written by reasoning through the "RELATIONSHIP
IDENTITY" requirement directly: an EMISSION-idempotency-style history-
wide scan for "has this exact tuple ever been asserted" would have
silently collapsed two independent actors' assertions of the same fact
into one — the design instead keys idempotency on
`(subject, predicate, object, actor_id, origin)`, so the SAME actor
retrying is a dedup, but a DIFFERENT actor asserting the same tuple adds
a new, separately-provenanced `Assertion` under the same canonical
`Relationship` (verified by test:
`test_different_actors_preserve_distinct_assertions`).

**Canonical entity references**: `subject_type`/`object_type` are
free-form (matching `permissions.models.ResourceRef.resource_type`'s own
convention), with three recognized types checked for real existence
(`fk_object` against `db.fk_objects`, `creative_lifecycle` against
`db.creative_lifecycle_events`, `identity` against `db.frek_persons`);
an unrecognized type is accepted as an opaque external reference,
honestly unchecked, not silently treated as verified-to-exist.

**Authority**: SUBMIT CLAIM (origin=DECLARED) is available to any
authenticated holder self-asserting, or admin. OBSERVED/ATTESTED/
COMPUTED/INFERRED origins are admin-only this state — no separate
attester-role or service-identity infrastructure exists yet to
authenticate those as anything other than admin, the same conservative
posture D2 already took on multi-contributor authorization. VERIFY is
admin-only and TRUST-layer-only. REVOKE is the asserting actor
(self-match) or admin.

**Visibility**: reuses `permissions.models.Scope`/`ScopeType` directly.
GLOBAL is public; OBJECT restricts to the relationship's own parties
(subject_id/object_id/any assertion's actor_id); ENTITY restricts to a
named id; ORGANIZATION is admin-only this state (no org-membership
resolver exists anywhere reachable in scope — a disclosed gap, not a
silent "visible" default). A relationship hidden by visibility policy
returns **404, not 403** — its existence is not leaked.

**Persistence**: plain MongoDB (`db.relationships`), one collection for
both layers — `layer` is *derived*, never caller-supplied, which is what
makes one collection a real structural separation rather than an
accidental conflation. Indexed on `relationship_id` (unique),
`(subject_id, predicate, object_id)`, `subject_id`, `object_id`,
`layer`. `DO_NOT_FORCE_NEO4J`/`DO_NOT_FORCE_POSTGRES`/
`DO_NOT_FORCE_PGVECTOR` all honored — bounded adjacency queries + an
application-level BFS (one of the mission's own listed acceptable
approaches) satisfy this state's real traversal needs.

**Bounded traversal**: `MAX_NEIGHBORS=200`, `MAX_PATH_DEPTH_HARD_CAP=10`
(FastAPI `Query(..., le=10)`, matching the historical route's own 1-10
bound), `MAX_PATH_NODES_VISITED=2000` — a cap the historical in-memory
graph never needed since it was always small, but a durable MongoDB-
backed graph cannot rely on staying small.

**D2 reuse**: a relationship can carry `source_event_id`, validated to
reference a real `db.creative_lifecycle_events` document — D2's own
lifecycle logic is never re-executed, only referenced
(`D3_CONSUMES_D2=TRUE`, `D3_REIMPLEMENTS_D2=FALSE`).

**D1 reuse / non-reimplementation**: a `similar_to` relationship can be
recorded as `origin=COMPUTED` with a caller-supplied similarity score —
this state does **not** build a live similarity-computation pipeline
(`IMPLEMENT_CULTURAL_FINGERPRINT=FALSE`, `IMPLEMENT_RECOMMENDER=FALSE`
explicitly prohibit that); the relationship's shape and semantics
support D1-derived evidence without D3 invoking D1's extraction itself.
`D1_VERIFIED` stays `PARTIAL`, unchanged.

**Notarization/events/audit**: best-effort notarization via
`notary.service.notarize_event(payload_type="relationship", ...)`; one
unified event `relationship.recorded` (`eventbus/producers.py:
build_relationship_event`, `payload.status` distinguishes create/verify/
revoke), registered in `registry/events/event_registry.json`, subscribed
into the Audit Trail (`server.py`'s `_AUDIT_TRAIL_EVENT_TYPES`) alongside
every other real producer (now nine, up from eight after D2).

## What was explicitly NOT done (per the founder's own prohibitions)

- **`backend/frek/routes_advanced.py`'s 7 réseau routes were not
  touched.** Zero lines changed — confirmed by a static-import test and
  by re-counting the 7 `@advanced_router.get("/reseau...")` decorators
  in the file. They remain live exactly as before.
- No route deletion, no deprecation, no migration of historical data
  (none exists durably to migrate).
- No cultural-fingerprint pipeline, no recommender, no reputation engine,
  no AI influence engine — the relationship *shape* supports these as
  future consumers; none is built this state
  (`IMPLEMENT_CULTURAL_FINGERPRINT/RECOMMENDER/REPUTATION_ENGINE/
  AI_INFLUENCE_ENGINE = FALSE`).
- D4 (Offline Proof Transport), D5 (Technical Evidence Attestation) were
  not started.
- No Production Readiness, Red/Blue/Purple, UI/UX, CVLN wiring, merge, or
  deploy.
- D1's own verification status is **not** silently upgraded
  (`D1_VERIFIED` stays `PARTIAL`).

## Verification

- `backend/tests/test_relationship_graph_unit.py` (41 tests) — mongomock,
  no live server/Mongo/notary needed. Covers: trust≠cultural layer split,
  inferred/computed never auto-verified (structural, not just asserted),
  cultural relations rejected from `/verify` with 409, canonical-entity
  existence checks, actor/authority preservation, unauthorized rejection
  (missing creds, holder attempting COMPUTED/INFERRED/ATTESTED/OBSERVED
  origins), visibility enforcement + 404-not-403 non-leak, provenance
  retained in history, D6 round-trip through real `Claim`/`Evidence`
  types, D2 event/content-binding references (existing and unknown-404),
  D1-shaped computed relationship staying non-verified, idempotent retry,
  independent-actor distinct-assertion preservation, revoke-preserves-
  history + owner-or-admin authority, neighbors/outgoing/incoming,
  bounded path + hard-cap rejection (422) + cycle-safety, neighbor-limit
  enforcement + over-limit rejection, full historical taxonomy record,
  historical-route-count regression guard.
- `backend/tests/test_eventbus.py` and `test_audit_trail.py` extended
  with the new producer's contract and audit-trail wiring (now nine real
  producers, up from eight after D2).
- Full unit suite: 315 passed (was 272 after D2), 0 failed. Coverage gate
  (registry/eventbus/permissions/audit_trail/proof_engine/storage/
  observability) re-verified: 96.68% against 90%.
- flake8/black on `relationship_graph/` and its tests: clean. mypy's
  `Optional[db]`/pydantic-signature findings there match the exact
  pre-existing pattern already present in `content_binding/` and
  `creative_lifecycle/` (confirmed via diff), not a regression, and
  `relationship_graph/` is outside CI's blocking mypy `MODULES` scope.

## What this ADR does not do

It does not build any real similarity/recommendation/reputation/
influence pipeline — those stay explicitly future work, consuming this
state's relationship shape once separately authorized. It does not
resolve `ORGANIZATION`-scoped visibility (no membership resolver exists
yet — disclosed, not silently defaulted to "visible"). It does not decide
the historical 7 réseau routes' eventual fate (compatibility adapter vs.
eventual deprecation) — that is a future, separately-authorized
ecosystem-consumer audit. It does not start D4–D5.
