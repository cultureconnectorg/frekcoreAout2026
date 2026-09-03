# FREK Historical Compatibility Matrix — STATE_6

Founder authorization: `FREKCORE_EXECUTION_PROTOCOL_V1` §STATE_6, "Historical
Compatibility Reconciliation" (2026-09-02). Reconciles the 19 historical
`backend/frek/` routes (identified in `docs/architecture/
FREK_LEGACY_ROUTE_AUDIT.md` and resolved into founder decisions D1–D5 in
`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md`) against the
now fully-implemented canonical services (`content_binding`,
`creative_lifecycle`, `relationship_graph`, `offline_transport`,
`technical_evidence_report`, all built on `proof_engine.evidence_semantics`
— D6).

**Rules this document is written under**: `PRESERVE_BACKWARD_COMPATIBILITY_
UNTIL_ECOSYSTEM_WIDE_CONSUMER_AUDIT=TRUE`, `DELETE_BACKEND_FREK=FALSE`,
`PHYSICAL_DELETION_ALLOWED=FALSE`, `DESTRUCTIVE_API_MIGRATION_ALLOWED=FALSE`.
No route below was deleted, renamed, or given a breaking response-shape
change. `backend/frek/` was changed only for explicit compatibility
adapters/hardening (rate limiting, audit visibility, additive canonical
cross-references, and — for D5's one route — removing an unqualified legal
overclaim from its own output text). Full diff: commit implementing this
document.

## Route-count guard

**HISTORICAL_ROUTE_COUNT = 19** (re-verified by reading
`backend/frek/routes.py` and `backend/frek/routes_advanced.py` directly
this pass, not assumed from any prior document): D1 = 3, D2 = 2, D3 = 7,
D4 = 6, D5 = 1. **EXPECTED_ROUTE_COUNT_MATCH = YES.** A static regression
test (`backend/tests/test_legacy_compatibility.py::TestRouteCountGuard`)
locks this in — it reports the real count rather than forcing it to 19 if
a future change ever disagrees.

## Consumer discovery (this pass, whole-repository search)

Searched: `backend/` (all packages), `frontend/`, `scripts/`, `sdk/`,
`frek_v1/`, `frek_v3/` (FAP), `tests/`, `docs/`, `memory/`.

**Direct local callers found — real, live-mounted, not dead code:**

- `frontend/src/pages/Certify.jsx` → `POST /api/frek/certify` (mounted at
  frontend route `/certify`, `frontend/src/App.jsx:78`).
- `frontend/src/pages/Verify.jsx` → `GET /api/frek/verify/{frekId}` and
  `GET /api/frek/verify/{frekId}/certificat.pdf` (mounted at frontend
  route `/verify/:frekId`, `frontend/src/App.jsx:99`).

This is the single most consequential finding of this pass: **D1's 2
verified-consumer routes (`/certify`, `/verify/{frek_id}`) have a real,
live frontend dependency on their exact historical response shape.**
`ABSENCE_OF_LOCAL_CALLER_EQUALS_NO_CONSUMER=FALSE` is not a hypothetical
here — it is exactly what would have been violated by a destructive
response-shape rewrite. This finding is why D1's disposition below is
HARDEN (additive-only response changes), never MIGRATE/SUPERSEDE.

No other historical route (D2's 2, D3's 7, D4's 6, D5's 1) has a frontend,
SDK, or script caller found anywhere in this repository — every other
reference outside `backend/frek/` itself is a test file or a documentation
file. Per the founder's own explicit rule, this is recorded as
`NONE_FOUND_LOCALLY`, **never** as "no consumer exists":
`ECOSYSTEM_WIDE_CONSUMER_AUDIT = INCOMPLETE` for all 19 routes (no other
CVLN repository is present in this workspace to search) — backward
compatibility remains mandatory regardless.

## Canonical target architecture (applied)

```
LEGACY ROUTE (backend/frek/routes.py, routes_advanced.py)
    |
    v
COMPATIBILITY LAYER (backend/frek/legacy_compat.py: rate limiting via
    security.policies.check_rate_limit; audit visibility via a single
    shared legacy_route.invoked event) + per-route additive canonical
    cross-reference reads (never writes)
    |
    v
CANONICAL FREKCORE SERVICE (content_binding / creative_lifecycle /
    relationship_graph / offline_transport / technical_evidence_report),
    read-only from the legacy side this state
```

No parallel write path was introduced: `frek/routes.py` and
`frek/routes_advanced.py` never call `.insert_one`/`.replace_one`/
`.update_one` on any canonical D1–D5 collection — confirmed by a static
test (`test_no_parallel_truth_engine_introduced`). Where a genuine
architecture decision would be required to safely route a legacy WRITE
into a canonical service (D1 certify, D2 genesis/workshop, D4 packet, D5
attestation), that decision is recorded below as a disclosed gap, not
silently made.

---

## D1 — Signal Fingerprint / Content Binding

| | |
|---|---|
| Canonical target | `backend/content_binding/` + `.fk` (FREK Object) + D6 evidence semantics |
| Known local callers | **`POST /certify`, `GET /verify/{frek_id}`: DIRECT_CALLER** (`frontend/src/pages/Certify.jsx`, `frontend/src/pages/Verify.jsx`, real live frontend routes). `POST /certify/upload`: NONE_FOUND_LOCALLY (test/doc only) |
| Ecosystem-wide audit | INCOMPLETE (no other CVLN repo present) |

| Route | Method | Disposition | Adapter status | Auth | Response compat. | Identifier compat. | Test evidence |
|---|---|---|---|---|---|---|---|
| `/api/frek/certify` | POST | **HARDEN** | Rate-limited (`legacy_frek_write`) + audit-visible (`legacy_route.invoked`, `canonical_target=content_binding`). Response gains one additive `canonical_note` field. No canonical write performed (see gap below) | Unchanged (historically zero-auth UNSAFE WRITE; adding mandatory auth would break the confirmed frontend caller — safety/compat wins over hardening auth here, rate limiting is the safety control instead) | **FULL** (every historical field unchanged; one field added) | Legacy `frek_id` (node02_identity's own triple-SHA-256 chain) preserved exactly as minted, never destroyed or replaced | `TestD1Compatibility` (unit) |
| `/api/frek/certify/upload` | POST | **HARDEN** | Same as above | Unchanged | **FULL** | Same as above | `TestD1Compatibility` (unit, via shared logic) |
| `/api/frek/verify/{frek_id}` | GET | **HARDEN + ADAPTER (read cross-reference)** | Rate-limited (`legacy_frek_read`) + audit-visible. Additively reads canonical `db.content_bindings` for a record whose own `legacy_identifier` field matches this legacy id, and attaches it as `canonical_binding` when found | Unchanged (PUBLIC VERIFY, historically zero-auth, stays that way) | **FULL** | Same legacy identifier, plus an explicit cross-reference to the canonical D1 `binding_id` when one has been separately created and linked | `TestD1Compatibility::test_verify_surfaces_canonical_binding_when_legacy_identifier_matches`, `::test_verify_without_canonical_binding_omits_the_field` |

**Disclosed semantic gap (why this is HARDEN, not ADAPTER/MIGRATE, for the
write side)**: legacy `/certify` **mints** its own identity
(`node02_identity.py`'s triple-SHA-256 chain over audio+vector+metadata+
prior-hash) — it does not reference an existing `.fk` object. Canonical
`content_binding.create` requires the opposite: an *already-existing*
`.fk` Cultural Object (`frek_id` minted only by `POST /api/v1/fk/create`)
to bind evidence to. Routing legacy `/certify` into canonical
`content_binding` safely would require this route to *also* silently
mint a new `.fk` object from unverified legacy input on every call — a
real architecture decision (does every legacy certification become a
canonical Cultural Object? under what authority? with what rights
metadata, which `.fk/create` requires and this route's request body does
not carry?) that this state declines to make unilaterally, per
`NEEDS_FOUNDER_DECISION`'s own definition ("semantic contradiction cannot
be safely resolved from evidence"). The identifier itself is never
destroyed (per the founder's explicit instruction) and `GET /verify`
already surfaces a canonical cross-reference additively when one exists
via the `legacy_identifier` alias field `content_binding/models.py`
already reserves for exactly this purpose. **Flagged for a future
founder decision**: should `/certify` be changed to auto-create a `.fk`
object as part of its own compatibility adapter? Not decided here.

`FINGERPRINT != FREK_ID`, `SIGNAL_FINGERPRINT != CRYPTOGRAPHIC_HASH`,
`MATCH != VERIFIED_FACT` — unchanged, not reopened this state (D1's own
architecture was validated in `reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`
and is out of this bounded reconciliation's scope). `D1_VERIFIED` stays
`PARTIAL`.

---

## D2 — Creative Lifecycle

| | |
|---|---|
| Canonical target | `backend/creative_lifecycle/` |
| Known local callers | NONE_FOUND_LOCALLY (test/doc only) |
| Ecosystem-wide audit | INCOMPLETE |

| Route | Method | Disposition | Adapter status | Auth | Response compat. | Identifier compat. | Test evidence |
|---|---|---|---|---|---|---|---|
| `/api/frek/genesis` | POST | **HARDEN** | Rate-limited (`legacy_frek_write`) + audit-visible. Response gains one additive `canonical_note` field. No canonical write performed (see gap below) | Unchanged (historically zero-auth; not weakened, not strengthened — see gap) | **FULL** | Legacy `pre_id` (node03_cycle's own scheme) preserved exactly, never destroyed | `TestD2Compatibility` (unit) |
| `/api/frek/workshop` | POST | **HARDEN** | Same as above | Unchanged | **FULL** | Same as above | `TestD2Compatibility` (unit) |

**Disclosed semantic gap**: canonical `creative_lifecycle` requires an
authenticated `identity_engine` holder session or admin key
(`X-FREK-Session`/`X-Admin-Key`) for every write — this is a deliberate,
tested security property (D2's own founder decision,
`docs/decisions/0005-...`). Legacy `/genesis` and `/workshop` accept a
bare, unauthenticated `artiste_id` *string* with no identity resolution
whatsoever — there is no session, no credential, nothing to authenticate.
Silently treating that string as an authenticated canonical actor would
be exactly the case the founder's own rule forbids: **"Historical
zero-auth routes must NOT force canonical services to weaken their
security model."** Routing these two legacy writes into canonical
`creative_lifecycle` safely would require either (a) inventing an
implicit, unauthenticated actor-mapping (a security weakening,
prohibited), or (b) requiring real authentication on a route confirmed to
have no local consumer needing that hardening but with an incomplete
ecosystem-wide audit (a live-break risk this state declines to take
unilaterally). GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY vocabulary
is unchanged; GENESIS still implies nothing about legal
authorship/ownership/priority (unchanged from D2's own architecture,
not reopened). Legacy cycle stays structurally separate from
`frek_v1`'s own participant/badge stage lifecycle, exactly as D2 already
established.

---

## D3 — Relationship / Provenance Graph (7 réseau routes)

| | |
|---|---|
| Canonical target | `backend/relationship_graph/` |
| Known local callers | NONE_FOUND_LOCALLY (test/doc only) |
| Ecosystem-wide audit | INCOMPLETE |

| Route | Method | Disposition | Adapter status | Auth | Response compat. | Test evidence |
|---|---|---|---|---|---|---|
| `/api/frek/advanced/reseau` | GET | HARDEN | Rate-limited + audit-visible | Unchanged (PUBLIC READ) | FULL | `TestD3Compatibility` |
| `.../reseau/stats` | GET | HARDEN | Same | Unchanged | FULL | `TestD3Compatibility` |
| `.../reseau/node/{node_id}` | GET | **HARDEN + ADAPTER (read cross-reference)** | Rate-limited + audit-visible. When `node_id` resolves to an OEUVRE (a real FREK-ID), additively reads canonical `db.relationships` and attaches a `canonical_relationships` field via `relationship_graph.service.bounded_neighbors`/`can_read` reused directly (never reimplemented) | Unchanged; cross-reference itself only ever surfaces GLOBAL-visibility canonical relationships (never a privacy downgrade through the unauthenticated legacy path) | FULL | `TestD3Compatibility::test_node_lookup_gains_canonical_relationships_for_oeuvre`, `::test_node_lookup_never_surfaces_non_global_canonical_relationship`, `::test_cultural_relation_cross_reference_never_implies_verified` |
| `.../reseau/neighbors/{node_id}` | GET | HARDEN | Rate-limited + audit-visible | Unchanged | FULL | `TestD3Compatibility` |
| `.../reseau/artiste/{artiste_id}` | GET | HARDEN | Same | Unchanged | FULL | `TestD3Compatibility` |
| `.../reseau/lieu/{lieu_id}` | GET | HARDEN | Same | Unchanged | FULL | `TestD3Compatibility` |
| `.../reseau/path` | GET | HARDEN | Same | Unchanged | FULL | `TestD3Compatibility` |

**Why 6 of 7 stay HARDEN rather than a full ADAPTER/SUPERSEDE read-path
replacement**: `node06_reseau`'s own in-memory graph is neither a subset
nor a superset of canonical `relationship_graph`'s durable store — it
includes synthetic, never-independently-managed node types (LIEU, EPOQUE,
FREQUENCE — confirmed in D3's own `HISTORICAL_NODE_TYPE_TAXONOMY`) that
have no canonical equivalent at all, and it is wiped on every process
restart while `relationship_graph` persists. Replacing the read path
wholesale would silently drop legacy-only data (LIEU/EPOQUE/FREQUENCE
subgraphs) or fabricate canonical-shaped answers for node types canonical
`relationship_graph` was never designed to represent —
`NO_PARALLEL_TRUTH_ENGINE_INTRODUCED=TRUE` is satisfied here by being
honest that node06 remains the sole source for these 6 read routes, not
by pretending it has been replaced. `/reseau/node/{node_id}` is the one
route where a real cross-reference is both safe (additive, read-only,
GLOBAL-visibility-only) and meaningful (OEUVRE = a real FREK-ID, the one
node type with a genuine canonical counterpart).

Of the historical 17 declared relation types, only 5 were ever actually
emitted (`ONLY_5_OF_17_HISTORICAL_RELATION_TYPES_WERE_ACTUALLY_EMITTED
=TRUE`, confirmed originally in D3's own reconciliation and re-confirmed
unchanged this state — not reopened). 5 node types / 17 relation types
vocabulary preserved verbatim
(`test_historical_taxonomy_vocabulary_unchanged`). CULTURAL relationships
surfaced through the new cross-reference keep their own honest `status`
— never re-labeled VERIFIED by the legacy route
(`test_cultural_relation_cross_reference_never_implies_verified`).

---

## D4 — Offline Proof Transport (6 transmission routes)

| | |
|---|---|
| Canonical target | `backend/offline_transport/` |
| Known local callers | NONE_FOUND_LOCALLY (test/doc only) |
| Ecosystem-wide audit | INCOMPLETE |

| Route | Method | Disposition | Adapter status | Auth | Response compat. | Test evidence |
|---|---|---|---|---|---|---|
| `/api/frek/advanced/transmission` | GET | HARDEN | Rate-limited + audit-visible | Unchanged | FULL | `TestD4Compatibility` |
| `.../transmission/protocols` | GET | **ADAPTER (read merge)** | Rate-limited + audit-visible. Merges in `offline_transport.adapters.adapter_info()` per protocol (D4's own canonical protocol metadata, which itself already reuses this exact historical `PROTOCOL_CONFIG` directly — one fact, not two independent copies) as an additive `canonical_adapter_info` field | Unchanged | FULL (still exactly 5 historical protocols, same keys, one field added per entry) | `TestD4Compatibility::test_protocols_still_returns_5_historical_protocols`, `::test_protocols_gain_canonical_adapter_info_additively` |
| `.../transmission/protocol/{protocol}` | GET | **ADAPTER (read merge)** | Same merge, single protocol | Unchanged | FULL | `TestD4Compatibility::test_single_protocol_info_gains_canonical_adapter_info` |
| `.../transmission/packet` | POST | **HARDEN** | Rate-limited + audit-visible. Response gains an explicit, honest `signature_short_is_not_cryptographic_signature: true` flag and a pointer to the canonical envelope endpoint. No canonical write performed (see gap below) | Unchanged (historically zero-auth UNSAFE WRITE; no confirmed caller, but ecosystem audit incomplete so left unauthenticated with rate limiting as the safety control) | FULL | `TestD4Compatibility::test_packet_signature_short_never_promoted_as_real_signature` |
| `.../transmission/watermark` | POST | **ADAPTER (delegated)** | Now calls `offline_transport.watermark.create_watermark_reference` directly instead of duplicating the historical call — genuine canonical-module execution, not a lookalike | Unchanged | FULL — canonical wrapper's return is a strict superset of the historical dict (same keys plus `proof`/`validation_status`/`decoder_exists`/`note`) | `TestD4Compatibility::test_watermark_delegates_to_canonical_wrapper_superset_shape` |
| `.../transmission/sync` | POST | **HARDEN** | Rate-limited + audit-visible. Response gains a `note` clarifying this is a legacy simulation, not canonical reconciliation | Unchanged | FULL | `TestD4Compatibility::test_sync_gains_compatibility_note` |

**`HISTORICAL_SIGNATURE_SHORT_WAS_NOT_REAL_SIGNATURE=TRUE`** — preserved
as compatibility metadata (the 8-character hash-prefix field itself is
unchanged, per "do not silently destroy it"), never represented as
canonical proof, and now explicitly flagged as such in the response
rather than left ambiguous. **`WATERMARK_EQUALS_PROOF=FALSE`** — the
legacy route now runs the exact same canonical function
(`offline_transport.watermark.create_watermark_reference`) that D4's own
architecture already isolated from ever influencing envelope trust state
(confirmed structurally: neither `frek/routes.py` nor
`frek/routes_advanced.py` imports anything from `offline_transport.models`
or `offline_transport.service`,
`test_watermark_never_influences_canonical_offline_transport_trust_state`).

**Disclosed semantic gap (packet write)**: same shape of gap as D1
certify — canonical `TransportEnvelope` requires an Ed25519 signature
under FREKCORE's own institutional key (`passport.keys`) and a monotonic
per-issuer sequence number; the legacy packet request carries neither an
authenticated issuer nor a sequence, and its `frek_id` is not guaranteed
to reference anything canonical. Auto-issuing a real signed canonical
envelope on behalf of an anonymous legacy caller would be a security-
relevant architecture decision (who is the `issuer_id`? what authority
level?) this state declines to make unilaterally.

---

## D5 — Technical / Juridical Attestation (1 route)

| | |
|---|---|
| Canonical target | `backend/technical_evidence_report/` |
| Known local callers | NONE_FOUND_LOCALLY (test/doc only) |
| Ecosystem-wide audit | INCOMPLETE |

| Route | Method | Disposition | Adapter status | Auth | Response compat. | Test evidence |
|---|---|---|---|---|---|---|
| `/api/frek/advanced/juridique/attestation` | POST | **HARDEN** | Rate-limited (`legacy_frek_write`) + audit-visible. Overclaiming wording fixed **at the source** (`node09_juridique.py:to_legal_text` — see below), response gains one additive `canonical_technical_evidence_report_endpoint` field | Unchanged (historically zero-auth; no confirmed caller) | FULL (every historical key present; wording of `legal_text` changed, its *presence and type* did not; one field added) | `TestD5Compatibility` |

**What changed and why it is not `DESTRUCTIVE_API_MIGRATION`**: the
route's request/response *shape* is completely unchanged — same input
fields, same output keys. What changed is the *content* of one string
field (`legal_text`), per the founder's own explicit D5/STATE_6
instruction: *"Do NOT preserve: blind caller truth, unsupported legal
claims, 'mathematically irrefutable' wording, automatic legal
authorship/ownership conclusions."* The historical closing sentence —
*"Ce fait est mathematiquement certain et temporellement irrefutable"* —
is confirmed (by reading `create_attestation`/`to_legal_text` directly,
not assumed) to have been produced from caller-supplied, unverified
values with zero independent check against canonical state. It is
replaced with a sentence that describes only what the function actually
did (format the caller's own submitted values) and now points to the
real, canonical, resource-ID-only D5 report
(`POST /api/v1/reports/technical-evidence`) for anything requiring actual
verification. `Node09Juridique.ALWAYS_STATEMENTS`'s own matching entry is
fixed identically, for internal consistency within the same module. This
is `LEGAL WORDING REGRESSION`-guarded: the new text is confirmed, by
test, to pass `technical_evidence_report.models.assert_no_forbidden_
language` — the exact static/semantic guard the mission's own D5 state
built (`test_unsupported_legal_wording_not_reintroduced`).

**Canonical D5 remains the sole source of authoritative technical
reporting** (`test_arbitrary_caller_facts_cannot_become_canonical_truth`
confirms the legacy route never writes to
`db.technical_evidence_reports`) — this legacy route continues to accept
and format arbitrary caller-supplied values, it simply no longer claims
they are "mathematically irrefutable" while doing so.

---

## Cross-cutting compliance

- **No route deleted** (`ROUTES_DELETED = 0`, confirmed by the route-count
  guard staying at 19).
- **No historical concept/vocabulary deleted**: node types, relation
  types, transport protocols, stage names, the "notaire de fait" legal
  framework's NEVER/ALWAYS structure — all unchanged in shape, only D5's
  one overclaiming sentence and its matching ALWAYS-statement entry had
  their *wording* fixed (not removed).
- **No parallel truth engine introduced**: statically confirmed (see
  above) — `backend/frek/` reads canonical collections additively, never
  writes them.
- **Canonical persistence stays authoritative** for everything canonical
  services already own; legacy in-memory stores (node02–node07) remain
  the system of record only for the legacy identifiers/state they always
  owned — never promoted to canonical status by this reconciliation.
- **Rate limiting**: `security.policies.check_rate_limit`, the exact
  existing mechanism (`legacy_frek_read`/`legacy_frek_write` keys) — no
  second throttling implementation.
- **Audit**: one shared `legacy_route.invoked` event
  (`backend/frek/legacy_compat.py`), subscribed into the Audit Trail
  alongside every other real producer (now twelve, up from eleven after
  D5) — never duplicated alongside a canonical business event for the
  same call (`EVENT_DUPLICATION_AVOIDED=TRUE`, confirmed by test). Never
  carries raw request payload content (audio, GPS, sha256, artiste_id) —
  coarse compatibility metadata only.
- **Error compatibility**: all historical error codes (400 malformed
  input, 404 not found) are unchanged; the two new rate-limit paths
  return 429, matching every canonical D-state route's own convention —
  no internal exception is newly leaked.
- **Deprecation**: `DEPRECATION_MAY_BE_DOCUMENTED=TRUE, REMOVAL_ALLOWED
  =FALSE` this state — no route above is deprecated. Given D1's confirmed
  real frontend consumer and every other route's incomplete
  ecosystem-wide audit, no route has satisfied the founder's own stated
  deprecation prerequisites (canonical replacement exists + compatibility
  proven + consumer impact understood + migration path documented) — none
  is proposed for deprecation this state.

## Disclosed gaps requiring a future, separate founder decision

None of these block STATE_6 acceptance (each route already has an
explicit, evidence-grounded disposition) — they are flagged so a future
state can pick them up deliberately rather than by accident:

1. Should `/certify`/`/certify/upload` auto-create a canonical `.fk`
   object + `content_binding` as part of their own adapter, given the
   confirmed real frontend dependency on their current response shape?
2. Should `/genesis`/`/workshop` gain an optional, backward-compatible
   authenticated path (e.g. an optional `X-FREK-Session` header) that,
   when present, *also* drives canonical `creative_lifecycle`, while
   staying anonymous-callable when absent?
3. Should `/transmission/packet` gain an equivalent optional
   authenticated path into canonical `offline_transport`?
4. A genuine ecosystem-wide consumer audit (other CVLN repositories) is
   still owed before any of the 19 routes could ever be considered for
   `DEPRECATE`.

## Verification

`backend/tests/test_legacy_compatibility.py` (47 tests): route-count
guard, per-D-state response-compatibility/rate-limit/audit/cross-reference
checks, cross-cutting no-parallel-truth-engine and audit-wiring checks.
`backend/tests/test_eventbus.py`/`test_audit_trail.py` extended with the
new `legacy_route.invoked` producer's contract (twelve real producers, up
from eleven after D5). Full unit suite: 449 passed, 0 failed (was 400
after D5). Coverage gate (registry/eventbus/permissions/audit_trail/
proof_engine/storage/observability): re-verified 96.70% against ≥90%.
