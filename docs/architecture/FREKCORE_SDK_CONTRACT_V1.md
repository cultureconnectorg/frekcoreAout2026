# FREKCORE SDK Contract — v1

STATE_7 (2026-09-03). What `sdk/python` and `sdk/typescript` cover, how
canonical API errors map into each language, and the version-
compatibility policy between an SDK release and the server it talks to.

## Scope, before this state

Both SDKs wrapped **only** `registry` (`FrekcoreRegistryClient`/
`RegistryClient`) and `identity_engine`'s **read** surface
(`FrekcoreIdentityClient`/`IdentityClient`) — confirmed by reading
`sdk/python/frekcore_sdk/__init__.py` and `sdk/typescript/src/index.ts`
directly. Every D1–D5 capability (content_binding, creative_lifecycle,
relationship_graph, offline_transport, technical_evidence_report) had
**no SDK coverage at all** before this state — a real, disclosed gap,
not previously documented as one.

## Scope, added this state

Deliberately **lean, not exhaustive** — matching `identity_client.py`'s
own established precedent of wrapping only the operations with strong,
reproducible evidence of a stable contract (a real, tested endpoint),
not every single route each module exposes. One canonical
create/generate operation and one canonical read operation per new
capability, in both languages:

| Capability | Python class | TypeScript class | Methods added |
|---|---|---|---|
| Content Binding (D1) | `FrekcoreContentBindingClient` | `ContentBindingClient` | `get_binding`/`getBinding`, `list_bindings`/`listBindings` |
| Creative Lifecycle (D2) | `FrekcoreCreativeLifecycleClient` | `CreativeLifecycleClient` | `start_genesis`/`startGenesis`, `get_history`/`getHistory` |
| Relationship / Provenance (D3) | `FrekcoreRelationshipGraphClient` | `RelationshipGraphClient` | `get_relationship`/`getRelationship`, `get_neighbors`/`getNeighbors` |
| Offline Transport (D4) | `FrekcoreOfflineTransportClient` | `OfflineTransportClient` | `get_protocols`/`getProtocols`, `get_envelope`/`getEnvelope` |
| Technical Evidence Report (D5) | `FrekcoreTechnicalEvidenceReportClient` | `TechnicalEvidenceReportClient` | `generate_report`/`generateReport`, `verify_report`/`verifyReport` (public, no auth) |

Every method maps to exactly one real, existing endpoint from
`FREKCORE_API_CONTRACT_V1.md` — no method here corresponds to an
endpoint that does not exist (the same invariant `client.py`'s own
header comment states, carried forward). File-upload-shaped write
endpoints (D1's own binding create, D2's workshop/metamorphose) and
session-ceremony-shaped endpoints (WebAuthn) remain unwrapped this
state for the same reasons `identity_client.py` already gave for its own
unwrapped surface — not a new exception, the same one applied
consistently.

## SDK error model

**Python** (`sdk/python/frekcore_sdk/errors.py`, new) and **TypeScript**
(`sdk/typescript/src/errors.ts`, new) define the identical hierarchy,
mapped from HTTP status — not from the (today, inconsistent) `detail`
string content, matching `FREKCORE_ERROR_CONTRACT_V1.md`'s own
"current status" section:

| Class | HTTP status | Canonical code |
|---|---|---|
| `FrekError` (base) | any | — |
| `InvalidRequestError` | 400, 422 | `INVALID_REQUEST` |
| `AuthenticationError` | 401 | `AUTHENTICATION_REQUIRED` |
| `AuthorityError` | 403 | `AUTHORITY_DENIED` |
| `NotFoundError` | 404 | `NOT_FOUND` |
| `ConflictError` | 409 | `CONFLICT` |
| `RateLimitError` | 429 | `RATE_LIMITED` |
| `VerificationError` | 422 (verification-endpoint context) | `VERIFICATION_FAILED` |
| `UnsupportedVersionError` | reserved, no `v1` endpoint returns this today | `UNSUPPORTED_VERSION` |
| `InternalError` | 5xx | `INTERNAL_ERROR` |

Every existing and new client method raises the matching subclass
instead of a raw `httpx.HTTPStatusError`/`fetch` rejection — a **strictly
additive** change for the two existing clients (`FrekcoreRegistryClient`,
`FrekcoreIdentityClient`): `FrekError` subclasses `httpx.HTTPStatusError`
in Python (so any existing caller catching the old exception type still
works) and the TypeScript `FrekError` carries the original `Response` on
a `.response` property (so an existing caller reading `.status` off a
raw fetch rejection can migrate at its own pace). `422` is ambiguous
between `INVALID_REQUEST` and `VERIFICATION_FAILED` in general FastAPI
usage (422 is also Pydantic's own default validation-error status) — the
SDK maps plain 422 to `InvalidRequestError` by default and only a
verification-shaped endpoint's own documented 422 (none exist yet at
`v1`) would need a narrower mapping; this is disclosed rather than
silently guessed.

## SDK version compatibility

- **SDK version**: `sdk/python`'s own `__version__` /
  `sdk/typescript/package.json`'s own `version` — bumped whenever a
  method is added or an error-mapping change occurs (SAFE per
  `FREKCORE_VERSIONING_POLICY.md` §3 — additive, no major bump required
  for adding capability-group clients).
- **Supported API version**: `v1` only, for both SDKs, today.
- **Behavior on an unsupported server version**: not yet exercised (no
  `v2` exists) — the documented intent is that a `v2`-only server
  response the SDK does not recognize surfaces as
  `UnsupportedVersionError`, not a silent misparse; this is declared
  policy ahead of the first time it is needed, matching
  `FREKCORE_API_CONTRACT_V1.md`'s own versioning section.
- **Behavior on unknown response fields**: every SDK method already
  either returns the raw parsed JSON dict/object (registry, offline
  transport, technical evidence report clients) or constructs a
  `dataclass`/interface from named fields it expects, ignoring anything
  else present (`RegistryNamespace(**row)`-style construction in Python;
  TypeScript's structural typing does the same implicitly) — unknown
  fields are already tolerated everywhere, confirmed by re-reading every
  existing client method this pass, not newly added as a behavior.

## No canonical storage internals exposed

Every SDK method returns/accepts capability-domain shapes (a binding, a
lifecycle event, a relationship, an envelope, a report) — never a raw
Mongo document shape, a `db.<collection>` name, or an internal Python/TS
class from the server's own module tree. Confirmed for the five new
capability clients by construction (they return the same JSON dicts the
HTTP layer already returns, which are themselves `to_public_dict()`-style
projections — see each server module's own model).
