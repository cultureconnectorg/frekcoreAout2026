# FREKCORE STATE_8 — Migration / Legacy Validation

Re-verifies the historical -> canonical migration boundary STATE_6 established
(`docs/architecture/FREK_HISTORICAL_COMPATIBILITY_MATRIX.md`, the authoritative
per-route table — this document does not repeat it, it re-checks it still
holds and records the regression evidence). All 19 routes, all checks below,
against `backend/frek/`'s empty diff this state (`git diff --stat -- backend/frek/`
confirmed empty) — nothing here changed the legacy module itself.

## 1. Route reachability

All 19 routes present in the OpenAPI schema generated from an isolated app
mounting `frek_router` + `frek_advanced_router`: `backend/tests/
test_api_contract.py::test_all_19_legacy_routes_present_in_openapi_surface`
— **PASS**, re-run this state.

```
POST /api/frek/certify                              POST /api/frek/genesis
POST /api/frek/certify/upload                        POST /api/frek/workshop
GET  /api/frek/verify/{frek_id}                       GET  /api/frek/advanced/reseau
GET  /api/frek/advanced/reseau/stats                  GET  /api/frek/advanced/reseau/node/{node_id}
GET  /api/frek/advanced/reseau/neighbors/{node_id}     GET  /api/frek/advanced/reseau/artiste/{artiste_id}
GET  /api/frek/advanced/reseau/lieu/{lieu_id}          GET  /api/frek/advanced/reseau/path
GET  /api/frek/advanced/transmission                   GET  /api/frek/advanced/transmission/protocols
GET  /api/frek/advanced/transmission/protocol/{protocol} POST /api/frek/advanced/transmission/packet
POST /api/frek/advanced/transmission/watermark         POST /api/frek/advanced/transmission/sync
POST /api/frek/advanced/juridique/attestation
```

## 2. Canonical target mapping (unchanged from STATE_6)

| Legacy group | Route count | Canonical target |
|---|---|---|
| Certify / Verify | 3 | `content_binding` (D1) |
| Genesis / Workshop | 2 | `creative_lifecycle` (D2) |
| Reseau (network/graph) | 7 | `relationship_graph` (D3) |
| Transmission | 6 | `offline_transport` (D4) |
| Juridique attestation | 1 | `technical_evidence_report` (D5) |

3 + 2 + 7 + 6 + 1 = 19. Matches STATE_6's own count, matches this state's
`test_api_contract.py::LEGACY_19_ROUTES` set exactly (re-verified this state,
not assumed).

## 3. No route writes an independent second truth

`tests/test_legacy_compatibility.py` (all 5 `TestD*Compatibility` classes +
`TestCrossCutting`) exercises every one of the 19 routes against the same
canonical D1-D5 storage the new routes use, confirming: HARDEN-only routes
(certify, certify/upload, genesis, workshop, reseau reads, transmission
reads/writes, juridique attestation) write only to their own historical
collections, never fabricating a second canonical record; HARDEN+ADAPTER
routes (`verify/{frek_id}`, `reseau/node/{node_id}`) additively *read* the
canonical store via the same service functions the canonical routes
themselves use (`relationship_graph.service.bounded_neighbors`/`can_read`
reused directly, never reimplemented) — never writing through the legacy
path into canonical collections. **INTEGRATION_VERIFIED, re-run green.**

## 4. Legacy identifiers remain usable/mapped; canonical identifiers remain canonical

- `certify`/`certify/upload`: legacy `frek_id` (node02_identity's triple-SHA-256
  chain) preserved exactly as historically minted — never destroyed, never
  silently replaced by a canonical FREK-ID.
- `verify/{frek_id}`: the `canonical_binding` cross-reference is attached only
  when a D1 `ContentBinding.legacy_identifier` field explicitly matches this
  legacy id — an explicit, queryable mapping (`content_bindings` collection,
  `legacy_identifier` field), not an inferred/coerced identity.
- `genesis`/`workshop`: legacy `pre_id` (node03_cycle's own scheme) preserved
  exactly, same discipline.
- `reseau/node/{node_id}`: the `canonical_relationships` cross-reference is
  attached only when `node_id` itself resolves to a real canonical FREK-ID —
  never guessed from shape (`FREKCORE_VERSIONING_POLICY.md` §4's identifier
  contract, unchanged).

Alias/mapping persistence explicitly tested: `tests/test_identity_reconcile_
unit.py::test_duplicate_reconciliation_is_idempotent` (a mapping record,
once created, is not duplicated on retry) and `::test_reconciliations_are_
visible_from_either_side` (the mapping is queryable from either identifier).
**INTEGRATION_VERIFIED.**

## 5. Response compatibility remains safe

Every HARDEN-only route: **FULL** compatibility (every historical field
unchanged, at most one additive field — `canonical_note` — appended), per
STATE_6's own matrix, re-confirmed unchanged this state (`backend/frek/`
empty diff). Every HARDEN+ADAPTER route: **FULL**, with the cross-reference
field additive and omitted (not null/error) when no canonical match exists
(`TestD1Compatibility::test_verify_without_canonical_binding_omits_the_field`,
`TestD3Compatibility::test_node_lookup_never_surfaces_non_global_canonical_
relationship`). No breaking response shape change is possible this state
(no legacy route code changed at all).

## 6. Unsafe historical semantics remain removed

The 19 routes deliberately did **not** gain new mandatory authentication
(adding it would break the confirmed live frontend caller of `certify`/
`verify` — safety/compatibility was prioritized over hardening auth here);
rate limiting (`legacy_frek_write`/`legacy_frek_read` scopes) is the safety
control instead, and audit visibility (`legacy_route.invoked`,
`canonical_target=...`) makes every legacy call observable. Both are
unchanged and re-verified this state via `tests/test_legacy_compatibility.py`.
The unsafe pattern that *was* structurally removed across this codebase — a
route reading/writing another CVLN system's data with no scope check at all
— was never present in these 19 routes to begin with (they only ever touch
`backend/frek/`'s own historical collections plus, additively, their own
canonical read cross-reference); the separate, already-closed P0
(`reports/22_P0_SECURITY_CLOSURE.md`) concerned fingerprint/geo/counter/
checkout, not this route set.

## 7. Result

`LEGACY_ROUTES_DELETED=0`. `LEGACY_COMPATIBILITY_REGRESSION=GREEN`. All 7
checks above hold unchanged from STATE_6, re-verified (not assumed) against
this state's actual `backend/frek/` diff (empty) and a fresh, green run of
`test_legacy_compatibility.py` + `test_api_contract.py`.
