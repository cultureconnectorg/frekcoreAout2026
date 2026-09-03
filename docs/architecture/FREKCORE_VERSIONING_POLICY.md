# FREKCORE Versioning & Compatibility Policy

STATE_7 (API/SDK Contract Stabilization, 2026-09-03). This is the policy
document `FREKCORE_API_CONTRACT_V1.md`, `FREKCORE_SDK_CONTRACT_V1.md`,
`FREKCORE_EVENT_CONTRACT_V1.md`, and `FREKCORE_ERROR_CONTRACT_V1.md` all
point back to for the rules governing change.

## 1. API versioning

Path-level: `/api/v1/...`. A future breaking change ships as a new
`/api/v2/...` path prefix, coexisting with `v1` until `v1` is explicitly
deprecated (with a documented migration path — never silently). See
`FREKCORE_API_CONTRACT_V1.md`'s own "API versioning" section for the
current state (v1 only, no v2 needed yet).

The 19 historical `backend/frek/` routes are `LEGACY_COMPATIBILITY`, not
`v0` — they were never inside the versioned contract and are not
retroactively assigned to it.

## 2. Schema versioning — audit of existing fields, no new ones added redundantly

Every externally-consumable canonical model already carries its own
version field, independently, matching this repo's established
convention of "each module keeps its own local version marker" (the same
convention `canonical_json` follows — each module keeps its own copy
rather than importing a shared one):

| Model | Version field | Source |
|---|---|---|
| `.fk` manifest | `fk_version` | `fk/models.py:ManifestFK.fk_version` |
| Transport envelope | `schema_version` | `offline_transport/models.py:TransportEnvelope.schema_version` |
| Technical evidence report | `report_schema_version` + `generator_version` | `technical_evidence_report/models.py:TechnicalEvidenceReport` |
| Event envelope | `schema_version` | `eventbus/envelope.py:EventEnvelope.schema_version` (also `registry/events/event_registry.json`'s own per-event-type `"version"` field) |
| Proof/notary block | `spec_version` | `notary/models.py:BlockResponse.spec_version` |
| Signal fingerprint | `algorithm` + `algorithm_version` | `content_binding/models.py:SIGNAL_ALGORITHM_ID/SIGNAL_ALGORITHM_VERSION` |
| FAP device attestation | `scheme` (`DeviceAttestationScheme`) | `offline_transport/models.py` |

**Policy**: a schema evolution that stays backward-compatible (see §3)
bumps nothing. A breaking schema change bumps the relevant version field
above (not the API path — unless the change is also API-shape-breaking,
in which case both bump together) and the new version must be
distinguishable by consumers inspecting that field — never a silent
reinterpretation of the same version number.

No redundant version field is added anywhere by this state — every
canonical model that needs one already has one.

## 3. Backward compatibility rules

**SAFE** (no version bump required):
- Adding an optional response field.
- Adding a new enum value where the consumer contract already requires
  tolerating unknown values (see §6, Enum contract).
- Adding an optional request field with a server-side default.
- Adding a new endpoint.
- Adding a new event type.
- Fixing wording/text content of a field whose *type* and *presence* are
  unchanged (STATE_6's own D5 precedent: `legal_text`'s content changed,
  its being-a-string-that-is-always-present did not).

**POTENTIALLY_BREAKING** (requires a new API/schema version per §1/§2,
and — for a canonical `v1` endpoint — the change ships as `v2`, never an
in-place `v1` mutation):
- Renaming a field.
- Changing a field's type.
- Making an optional field required.
- Changing identifier semantics (what a given ID string resolves to).
- Changing a status enum's *meaning* (not just adding a new value to it).
- Changing auth requirements (tightening OR loosening).
- Removing an endpoint or a response field.
- Changing pagination semantics (page-size defaults, cursor format,
  ordering guarantees).
- Changing idempotency-key scope or retry semantics.

This mirrors the mission brief's own SAFE/POTENTIALLY_BREAKING list
verbatim, restated here as the canonical text every other contract
document defers to (never re-derived independently elsewhere in this
docs tree).

## 4. Identifier contract

FREKCORE has multiple, deliberately distinct identifier families — a
consumer must not guess an ID's type from its string shape alone unless
stated here:

| Identifier | Minted by | Format guarantee |
|---|---|---|
| FREK-ID (`.fk` Object) | `POST /api/v1/fk/create` only | Opaque string; treat as opaque, do not parse |
| Legacy identifier (`backend/frek/`) | `pipeline.certify` (node02_identity triple-SHA-256 chain) | Opaque string; **never the same identifier family as the canonical FREK-ID above** — `FREK_ID_EQUALS_SIGNAL_FINGERPRINT=FALSE`, structurally enforced by `content_binding/models.py`'s `legacy_identifier` field existing as a distinct, optional compatibility alias, never conflated with `frek_id` |
| `binding_id` (D1) | `content_binding` create | Opaque string, unique per binding |
| `pre_id` (D2) | `creative_lifecycle` genesis | Opaque string, one per lifecycle cycle |
| `event_id` (D2) | Each lifecycle stage transition | Opaque string, one per event (history is append-only, never reused) |
| `relationship_id` (D3) | `relationship_graph` create | Opaque string, one per canonical (subject, predicate, object) slot |
| `assertion_id` (D3) | Each relationship assertion | Opaque string, nested under a `relationship_id` |
| `envelope_id` (D4) | `offline_transport` create | Opaque string, one per transport envelope |
| `device_id_hex` (D4/FAP) | Device provisioning (external to FREKCORE) | Hex string, FAP's own device identity |
| `report_id` (D5) | `technical_evidence_report` generate | Opaque string, one per immutable report snapshot |
| `frek_id` (identity_engine) | `POST /api/v1/identity/init` | Opaque string, `id-{12hex}-{4hex}` shape historically but **not guaranteed** — do not parse |

**Policy**: every identifier above is an opaque string. No consumer
contract guarantees a parseable internal structure for any of them,
even where today's implementation happens to have one (e.g. `frek_id`'s
`id-...` shape) — depending on that shape is depending on an
implementation detail, not the contract, and is called out explicitly
wherever an existing doc might otherwise suggest structure is guaranteed.

## 5. Time contract

**Policy for `/api/v1/...` canonical endpoints**: timestamps are ISO 8601
/ RFC 3339 UTC strings (`datetime.now(timezone.utc).isoformat()` — the
convention every D1–D5 module and `identity_engine` already independently
converged on; confirmed by reading each module's own `_now_iso()`/
equivalent helper — this document codifies existing, uniform practice, it
does not change it). Never epoch milliseconds, never a naive
(timezone-less) timestamp, on any canonical endpoint.

**Legacy compatibility exception**: the 19 historical `backend/frek/`
routes keep their own historical timestamp conventions unchanged
(`timestamp_ms`, epoch-millisecond integers, per `frek/pipeline.py`) —
`LEGACY_COMPATIBILITY` routes are explicitly exempt from the canonical
time contract, per the same "preserve historical response shape" rule
that governs every other field of those routes.

## 6. Enum contract

Every canonical enum exposed on a `/api/v1/...` response
(`ProofState`, `RelationshipStatus`, `RelationLayer`, `SyncStatus`,
`LocalValidationStatus`, `AuthorityStatus`, `ClaimOrigin`, `EvidenceKind`,
`SectionKind`, `ReportSubjectType`, `IDENTITY_TYPES`, `IDENTITY_STATUS`,
`TransportProtocol`, ...) is a **closed vocabulary** for STATE_7's
purposes: a consumer should treat an unrecognized value as a forward-
compatibility signal (log and degrade gracefully — e.g. render as
"unknown status"), not a hard parse failure, since §3 permits adding a
new enum *value* as SAFE. No historical FREK vocabulary (node/relation
types, transport protocols, lifecycle stage names, legal NEVER/ALWAYS
statement wording) is renamed for style anywhere in this state
(`REWRITE_D1_D6_ARCHITECTURE=FALSE` and the founder's own explicit "do
not rename historical FREK vocabulary merely for style" rule).

## 7. Idempotency contract

**Existing mechanisms, audited (not retrofitted)**:

| Endpoint family | Mechanism | Scope | Same-key-same-payload | Same-key-different-payload |
|---|---|---|---|---|
| D1 `POST /content-binding/{frek_id}` | Content-derived: `(frek_id, exact_hash)` | Per object + exact content hash | Returns the existing binding, no new record | A *different* hash is simply a different binding (not a conflict — the key itself differs) |
| D2 `POST /{pre_id}/emission` | Domain-derived: re-emitting to the same `fk_frek_id` | Per cycle + target object | Safe no-op | N/A (emission target is the only variable input) |
| D3 `POST /relationships` | Assertion-derived: `(subject, predicate, object, actor_id, origin)` | Per assertion tuple | Safe no-op (same assertion, not duplicated) | A different actor is preserved as independent provenance (by design — `SAME_SUBJECT_PREDICATE_OBJECT != SAME_ASSERTION`) |
| D4 `POST /envelopes/{id}/receive`, `/sync` | Resource-state-derived: envelope's own persisted `sync_status` | Per envelope | Returns the existing, already-computed outcome, never re-runs side effects | N/A (the envelope's own content is immutable after signing — a "different payload" would be a different, tamper-invalid signature, rejected on its own) |
| `notary.service.notarize_event` | Best-effort, non-blocking, append-only | Per call | Appends a new block each time (by design — an audit chain is meant to record every attempt, not deduplicate them) | N/A |

**Policy for future canonical write endpoints**: prefer a
**domain-derived** idempotency key (a natural tuple already meaningful to
the operation, as every table row above does) over a caller-supplied
`Idempotency-Key` header — this repo has no precedent for the latter, and
introducing one now, absent evidence a consumer needs it, would be
inventing infrastructure ahead of a real requirement. If a future
operation's domain has no natural idempotency key (unlike every
operation audited above, which does), that is the trigger to add a
caller-supplied `Idempotency-Key` header, scoped per-endpoint, with a
short TTL (matching the endpoint's own rate-limit window as a starting
default) — not before.

## 8. Pagination contract

**Existing mechanisms, audited**:

- `registry`'s object-list endpoints (`GET /objects/{namespace}`):
  **offset/limit**, `limit`/`offset` query params, default `limit=50`.
- `relationship_graph`'s bounded reads (`neighbors`/`outgoing`/
  `incoming`/`traverse/path`): **limit-only** (no pagination token — a
  hard cap, `MAX_NEIGHBORS=200`/`MAX_PATH_NODES_VISITED=2000`, not a
  paged listing).
- `notary`'s `GET /blocks`: **limit-only** (most-recent-first, capped).
- `identity_engine`'s `GET /search`: **offset/limit**, default `limit=50`.

**Policy**: **offset/limit is the canonical pagination model** for any
future `/api/v1/...` list endpoint — it is what every existing paged
canonical endpoint already uses, and introducing cursor-based pagination
now would mean two coexisting pagination conventions for no
demonstrated reason (`REUSE_BEFORE_BUILD`). Canonical defaults: `limit`
default 50, hard max 200 (matching `registry`'s own existing ceiling
convention where declared, and `relationship_graph`'s own `MAX_NEIGHBORS`
elsewhere) — a request for `limit` above the max is clamped, never
rejected with an error, matching every existing endpoint's own behavior.
Ordering is stable per endpoint (each already orders by its own natural
key — `computed_at`, `sequence`, `created_at` — ascending unless
documented otherwise) and is not part of this policy to change.

Bounded-traversal endpoints (`relationship_graph`'s neighbor/path
queries) are **not** paginated list endpoints in the offset/limit sense
— they are graph-traversal safety caps, a different contract, documented
as such in `FREKCORE_API_CONTRACT_V1.md` rather than forced into the
offset/limit shape they were never designed for.

## 9. Service identity & delegated authority contract

`permissions/models.py` (Role/Scope/Action/ResourceRef/Decision/
`RoleGrant`/`Subject`) is the existing, real, tested, `NO_PARALLEL_
AUTHORITY_ENGINE`-compliant primitive set for this. It has had zero live
callers anywhere in this codebase through D1–D6 and STATE_6 (confirmed
repeatedly, not reopened here) — STATE_7 does not change that; it
documents the **contract** these primitives are meant to express once a
consumer needs it, and adds the one missing piece needed for that
contract to be *coherent* (not a "huge IAM product" — the founder's own
explicit boundary):

- **`ServiceIdentity`** (new, pure data model, `permissions/models.py`):
  represents a non-human caller — `service_id`, an owning
  organization/entity reference (`ResourceRef`), a credential reference
  (opaque — this model never carries key material itself, matching every
  other credential-adjacent model in this codebase), `allowed_scopes`
  (`List[Scope]`), `expires_at`, `revoked_at`. This is the "service_id /
  organization owner / credential / allowed scopes / expiry / revocation"
  list the mission names, expressed with existing `Scope` types, not a
  new vocabulary.
- **`DelegationGrant`** (new, pure data model): `delegator` (a `Subject`
  or `ServiceIdentity` reference), `delegate` (same), `scope` (`Scope`),
  `actions` (`List[Action]`), `resource` (optional `ResourceRef` boundary
  narrower than `scope`), `valid_from`/`valid_until`, `revoked_at`,
  `proof_reference` (optional — a `credential_id`/`envelope_id`/whatever
  proof backs the grant, opaque reference only).
- **`delegation_permits(...)`** (new, pure function): given a
  `DelegationGrant` and a `DecisionRequest`-shaped ask, returns whether
  the delegate's requested action/resource is *contained within* the
  grant's own scope/actions/resource/validity window —
  **`delegation_permits` can never grant more than the delegator's own
  scope already contains** (a delegate cannot escalate past its
  delegator — enforced by construction: the function only ever narrows,
  never widens, checked by test).

None of this is wired into any live route this state (no
`ServiceIdentity`/`DelegationGrant` persistence exists, matching
`RoleGrant`'s own long-standing disclosed gap) — it is the documented,
tested, ready-to-adopt contract for the day a real service consumer
(KORA, Agent Factory, ...) needs it, per STATE_7's own explicit
"prepare to be consumed later, do not wire it now" mandate.

## 10. Public verification contract

`VERIFICATION_MAY_BE_PUBLIC=TRUE`, `PUBLIC_VERIFY != PUBLIC_DISCLOSURE` —
D5's own rule (`docs/decisions/0008-...`), restated here as the
cross-cutting policy every future public-verify-shaped endpoint follows:
a public verifier may learn **that** something exists, its **shape**
(kind/type/status label), and an **integrity confirmation** (hash/
signature match) — never the underlying evidence content, relationship
detail, or credential material. `GET /api/v1/reports/technical-evidence/
{report_id}/verify` is the canonical example; `GET /api/v1/notary/
proof/{payload_id}` and `GET /api/v1/fk/verify` follow the same shape
(existence + cryptographic-validity confirmation, no private payload).

## 11. Report / snapshot immutability

A `technical_evidence_report` is generated fresh on every
`POST .../technical-evidence` call (not idempotent, by design — see §7)
and, once persisted, is an **immutable historical snapshot**
(`is_snapshot=True`, `report_hash` computed over content fields only).
Re-verifying an existing `report_id` never changes its content or hash;
generating a *new* report about the same subject produces a *new*
`report_id` with its own hash — the two are never silently merged or
treated as the same resource. This is the general pattern any future
"report" or "snapshot" shaped canonical resource should follow.
