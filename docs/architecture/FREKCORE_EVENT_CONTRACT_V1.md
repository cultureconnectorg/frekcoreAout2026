# FREKCORE Event Contract — v1

STATE_7 (2026-09-03). The Event Bus (`backend/eventbus/`) contract:
`EventEnvelope` shape, the canonical catalog (`registry/events/
event_registry.json`), and the audit/business-event distinction.

## Envelope shape (`eventbus/envelope.py:EventEnvelope`)

| Field | Type | Contract |
|---|---|---|
| `event_id` | string | Unique per envelope, server-generated |
| `event_type` | string | `"<producer_domain>.<action>"`, matches a `registry/events/event_registry.json` catalog entry |
| `event_version` | string | Reserved on the envelope itself; the catalog's own per-event-type `"version"` field (currently `"v1"` for every real event type) is the authoritative version — see §"Event evolution" |
| `producer` | string | The module that built this event (`identity_engine`, `fk`, `content_binding`, `creative_lifecycle`, `relationship_graph`, `offline_transport`, `technical_evidence_report`, `frek_legacy_compat`) |
| `subject` | string | The event's own primary resource ID (never the referenced/related entities — those live in `payload`) |
| `correlation_id` | optional string | Caller-supplied, for cross-event tracing |
| `occurred_at` | string (RFC 3339 UTC) | Server-set at publish time |
| `payload` | dict | Event-type-specific fields, schema below |
| `schema_version` | string | Per-envelope-instance schema marker, set by each `build_*_event()` producer (currently `"1.0.0"` for every real event type) |

## Canonical catalog — `registry/events/event_registry.json`

Re-read directly from the registry file this pass (not assumed):

| event_type | producer | version | status | Privacy classification |
|---|---|---|---|---|
| `identity.created` | identity_engine | v1 | EXISTS | Coarse metadata only (`frek_id`, `identity_type`, `status`, `created_at`) — never credentials |
| `identity.updated` | identity_engine | v1 | EXISTS | `changed_fields` list only, never the new values themselves |
| `identity.revoked` | identity_engine | v1 | EXISTS | Coarse metadata |
| `identity.recovered` | identity_engine | v1 | EXISTS | Coarse metadata |
| `identity.reconciled` | identity_engine | v1 | EXISTS | Both identity references + system name, no credential data |
| `identity.merged` | identity_engine | v1 | **REJECTED** | N/A — this event type is explicitly not implemented; `MERGE` was founder-rejected in favor of `RECONCILE` (`docs/decisions/0003-...`), kept in the catalog as a documented non-choice, not a gap |
| `object.created` | fk | v1 | EXISTS | `frek_id`, `object_type`, `title`, `created_at` — never media content |
| `object.verified` | fk | v1 | PARTIAL | Documented, not wired to a live publish call — a pre-existing, disclosed gap, not created or closed this state |
| `proof.generated` | notary | v1 | PARTIAL | Documented, no live `build_*_event()`/publish call found this pass (notary blocks are created via `notarize_event`, but no `EventEnvelope` is published for the block itself) — a pre-existing, disclosed gap |
| `certificate.issued` | certificate_engine | v1 | MISSING | No such module exists — Academy Certificate Engine is itself not built (see `FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`) |
| `wallet.linked` | identity_engine | v1 | MISSING | No wallet-linking capability exists in this codebase |
| `artist.verified` | registry | v1 | MISSING | No such verification flow exists |
| `content_binding.created` | content_binding | v1 | EXISTS | Never echoes the raw signal-fingerprint vector |
| `creative_lifecycle.recorded` | creative_lifecycle | v1 | EXISTS | Coarse metadata; `payload.stage` distinguishes GENESIS/WORKSHOP/METAMORPHOSE/EMISSION/LEGACY |
| `relationship.recorded` | relationship_graph | v1 | EXISTS | Never echoes the full assertions/claims/evidence list |
| `offline_transport.envelope_recorded` | offline_transport | v1 | EXISTS | Never echoes claim/signature/device_attestation |
| `technical_evidence_report.recorded` | technical_evidence_report | v1 | EXISTS | Never echoes report sections (statements/data) |
| `legacy_route.invoked` | frek_legacy_compat | v1 | EXISTS | Never echoes raw request payload (audio, GPS, sha256, artiste_id) |

**Twelve event types are real** (`EXISTS`, a genuine `build_*_event()` in
`eventbus/producers.py` with a passing unit test): the six identity
events, `object.created`, and the six D1–D5/legacy-compat events added
this session. These twelve are exactly `server.py`'s own
`_AUDIT_TRAIL_EVENT_TYPES` tuple — every real business event is
subscribed into the Audit Trail, none is missing, none is duplicated
(verified by a standing static test,
`test_server_py_subscribes_all_twelve_real_producers_to_audit_trail`).
Two (`object.verified`, `proof.generated`) are `PARTIAL` — cataloged
intent, no live publish call. Three (`certificate.issued`, `wallet.
linked`, `artist.verified`) are `MISSING` — the capability itself does
not exist yet. `identity.merged` is `REJECTED` by explicit founder
decision, kept as a documented non-choice.

## Event evolution / compatibility

A consumer of any `EXISTS` event type must:

- **Ignore unknown payload fields** — additive payload fields are SAFE
  per `FREKCORE_VERSIONING_POLICY.md` §3, never treated as a parse
  failure.
- **Key on `event_type` + the catalog's own `version`** (currently `v1`
  for all of them) to know the payload schema in force — a future
  breaking payload change ships as a new `event_type` version suffix or
  a new `event_type` string entirely (this repo has no precedent yet for
  versioning an event_type string in place — the policy, stated ahead of
  need: **prefer a new catalog entry over silently reshaping an existing
  one's payload in a breaking way**).
- **Never assume delivery-once or delivery-ordering guarantees beyond
  what `InProcessEventBus` actually provides**: `eventbus/bus.py`'s
  `InProcessEventBus.publish()` calls subscribers synchronously, in
  subscription order, and catches any subscriber exception so one
  broken subscriber never blocks another or the publisher — this is a
  same-process fan-out, not a durable queue. No cross-process delivery
  guarantee exists today (no external message broker is in use) — this
  is disclosed here, not silently assumed away.

## Audit ≠ Event Bus (preserved distinction)

`backend/audit_trail/` (`AuditEvent`, `MongoAuditRecorder`) is a
**subscriber** to the twelve real business events above — it is fed BY
the Event Bus, it does not define a second, competing event catalog. An
`AuditEvent` (`audit_trail/models.py`) is a strict, append-only
*projection* of an `EventEnvelope` (`action=event_type`,
`resource_type=producer`, `actor_frek_id=subject`, plus the raw
`payload` under `metadata.payload` — never more than what the business
event itself already carried). A consumer integrating against
FREKCORE's Event Bus contract (this document) integrates against the
`EventEnvelope`/catalog shape above; `audit_trail`'s own storage schema
is an internal implementation detail of the Audit Trail feature, not a
second public event contract. See `FREKCORE_API_CONTRACT_V1.md` §9 for
the disclosed gap that `audit_trail` has no HTTP read surface of its own
today.

## Traceability

`correlation_id` is the cross-event tracing field every producer already
accepts (optional, caller-supplied). `event_id` is unique per envelope.
No separate `request_id`/`trace_id` propagation exists across the HTTP →
Event Bus boundary today (a request's own request-scoped ID, where
`observability/request_id.py` sets one, is not currently threaded into
`correlation_id` automatically) — disclosed as a real gap, not fixed
this state (no evidence any consumer needs end-to-end trace stitching
yet; adding it without a real requirement would be inventing
infrastructure ahead of need, the same discipline STATE_7 applies
throughout).
