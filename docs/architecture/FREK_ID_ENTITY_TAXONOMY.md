# FREK-ID Entity Taxonomy (canonical)

Per the founder's 2026-08-31 instruction ("do not assume FREK-ID represents
only a human user... produce a canonical FREK-ID Entity Taxonomy before
final lifecycle implementation"): this document surveys every entity type
this session found evidence for — in code, in historical FREK
documentation (`frek_v3/docs/`, `memory/`), and in interface contracts
(`docs/interfaces/`) — that either carries its own FREK-ID or is referenced
by one, before the MERGE/RENEW/RECOVERY lifecycle decisions
(`docs/decisions/0003-identity-lifecycle-founder-decisions-implemented.md`)
are implemented in code.

## 0. Method and classification vocabulary

Every entry below is graded by what actually supports it, not by what would
be architecturally tidy:

- **OBSERVED** — real code in this repository mints a FREK-ID (or a
  FREK-ID-shaped reference) for this entity type today. Verified by
  reading the code, not inferred from a route name.
- **DOCUMENTED** — named in historical FREK specification documents
  (`frek_v3/docs/`, `memory/PRD.md`) with no corresponding backend
  implementation found.
- **DECIDED** — an explicit founder decision has settled this entity's
  relationship to FREK-ID, independent of whether code exists yet.
- **PROPOSED** — the source material itself labels this "proposed, not
  implemented" (an interface doc's own "next step" section).
- **NOT FOUND** — searched for and not located in code or documentation.
  Listed explicitly, per the founder's instruction not to invent
  unsupported entity classes, rather than silently omitted.

Evidence trail for this pass: `grep` across every `frek_id`-minting call
site in `backend/` (21 files); every `did:frek:` occurrence across
`docs/`, `frek_v3/docs/`, `reports/`; `registry/schemas/v1/*.schema.json`
(all 8 namespaces); `identity_engine/models.py`, `frek_v1/models.py`,
`fk/models.py`, `frek/nodes/node02_identity.py`; `docs/interfaces/*.md`;
`memory/PRD.md`.

## 1. Summary table

| Entity type | Gets its own FREK-ID? | Classification | Where |
|---|---|---|---|
| Person (individual/professional) | **Yes** | OBSERVED | `identity_engine` (`FREKIdentity`), `frek_v1` (event-participant identity) |
| Institution / Organization | **Partial** — Registry record yes, credentialed actor no | OBSERVED (Registry) + DOCUMENTED (typed DID) | `registry/schemas/v1/frek.organization.schema.json`; `identity_engine`'s `identity_type="institution"`; `did:frek:org-<uuid>` documented, not minted |
| Role / Authority | **No — never a FREK-ID subject** | OBSERVED (as a grant, not a subject) | `permissions.Role`, `permissions.protocol_roles.ProtocolRole` — both attach to a Subject's `frek_id`, neither is one |
| Cultural Object / Work (`.fk`) | **Yes**, its own `frek_id` | OBSERVED | `backend/fk/` (`fk_objects`), `backend/registry/` (`frek.track`/`frek.album`/`frek.work`) |
| Work-certification (legacy `frek/`) | **Yes**, distinct ID format | OBSERVED (legacy, non-persistent storage) | `backend/frek/nodes/node02_identity.py` — `FREK-YYYY-NNNN-hash-hash` |
| Device / Hardware | **No** — documented only | DOCUMENTED | `did:frek:device-<uuid>` (`frek_v3/docs/`), never minted in `backend/` |
| Wallet / Account | **Yes**, but as a link record, not an independent actor | OBSERVED | `registry/schemas/v1/frek.wallet.schema.json` — `holder_id` FK reference, no credentials of its own |
| Software Agent / Service | **One institutional instance only** | OBSERVED (1) + DOCUMENTED + PROPOSED | `did:frek:frekcore` (the platform's own DID, `did/vc.py:84`); `did:frek:app-<uuid>` documented, not minted; CVLN Agent Factory's "Agent" role explicitly `PROPOSED, NOT IMPLEMENTED` |
| Physical Asset | **No dedicated identity model** | DOCUMENTED (spec) + OBSERVED (as a generic `.fk` `object_type`) | `frek_v3/docs/FREK_Object_Model_Specification_v0.1.md` "FK PHYSICAL"; `fk/models.py`'s `OBJECT_TYPES` includes `artwork`/`heritage`/`document` but no physical-specific fields |
| Location / Infrastructure | **No — never a FREK-ID subject** | OBSERVED (as free-text metadata only) | `fk/models.py`'s `Context.location`/`coordinates`/`institution` are plain strings, not FREK-ID references |
| Certificate / Credential record | **Yes**, its own `frek_id`, with its own expiry | OBSERVED | `registry/schemas/v1/frek.certificate.schema.json` — `holder_id`, `issuer`, `expires_at` |
| Staff / Terrain Agent (operational) | **No — deliberately a separate system** | OBSERVED (as a negative finding) | `backend/staff/routes.py` — `agent_id` + PIN + role, no `frek_id` anywhere |
| Project / Production | Not found | NOT FOUND | — |
| Événement vérifiable | **Yes**, its own `frek_id` | OBSERVED | `registry/schemas/v1/frek.event.schema.json` |
| Droits / mandat / relation juridique | **No — a linked object, not an identity** | OBSERVED (as attachment) + DOCUMENTED (spec `rights.splits`) | `fk/models.py`'s `RightsLayer` (free-text `Contributor`, not FREK-ID-linked) |
| Heritage / Transmission (succession) | N/A — a *lifecycle event* on an existing Person FREK-ID, not its own entity | OBSERVED, `frek_v1`-only | `backend/heritage/routes.py` — real, notarized, transfers control without regenerating `frek_id`; no `identity_engine` equivalent |

## 2. Per-entity detail

### 2.1 Person (individual / professional)

| Dimension | Answer |
|---|---|
| Own FREK-ID | Yes — two independent minting systems, Contradiction C1 (`reports/FREKCORE_CONTRADICTIONS.md`): `identity_engine.service.generate_identity_id()` (`id-{12hex}-{4hex}`) and `frek_v1`'s event-participant identity (same format, separate collection `frek_identities`) |
| Linked to another FREK-ID? | N/A — this is the root subject other entities link to |
| Ownership/control model | Self-controlled via WebAuthn Passkey + session token (`identity_engine`); `frek_v1`'s is OAuth2-client-scoped (the *client*, not the person, holds the credential — see `docs/architecture/FREK_ID_RECONCILIATION.md`) |
| Authority model | Holder session (`X-FREK-Session`) or admin-key override (`_holder_or_admin`, `identity_engine/routes.py`) |
| Credential model | WebAuthn Passkeys (`Credential` — `credential_id`, `public_key`, `sign_count`, `aaguid`, `transports`) — 0 or more per identity |
| Merge semantics | Was `MISSING` before `docs/decisions/0003-...md`; now DECIDED (non-destructive reconciliation) |
| Recovery semantics | Was a real gap (`register_begin`'s ownership check had no admin override) before `0003`; now DECIDED |
| Key/device rotation | Adding a second+ Passkey while holding a valid session is already implemented (`register_begin`/`register_complete`'s "holder session required to add a credential once one exists" branch) — this **is** device rotation for a Person, already OBSERVED, just not previously named as such |
| Lifecycle/status | `anonymous → protected → revoked` / `archived` (`IDENTITY_STATUS`, `identity_engine/models.py`) |
| Provenance requirements | `created_at`, `linked_objects`, `linked_sessions` on the identity document itself |
| Proof/audit requirements | Revoke is notarized (`notary.notarize_event`); Audit Trail subscribes to `identity.created`/`updated`/`revoked` (`backend/server.py`) |
| Relationship to `.fk`/FAP/FREK-Chain | Owns `.fk` objects via `owner_id`; is the `creator` referenced by a `.fk`'s `identity` layer (spec) / `Contributor` (code, free-text only — see §2.4) |

**Sub-roles (artiste/auteur/producteur/etc.)**: not a property of the
identity itself in either minting system — `identity_engine.FREKIdentity`
has no role field beyond `identity_type` (individual/professional/
institution). The closest evidenced sub-role vocabulary is
`registry/schemas/v1/frek.artist.schema.json`'s `primary_role` enum
(`musician`/`producer`/`songwriter`/`label`/`performer`/`other`) — but
that lives on the **Registry catalog record** (`frek.artist`, owned *by*
a Person via `owner_id`), not on the Person identity itself. `salarié`
(employee), `client`, `utilisateur` (platform user), and `représentant
légal` (legal representative) have **no evidence anywhere** in code or
historical docs as distinct sub-roles — NOT FOUND, not invented here.

**Heritage / Transmission (succession) — a real, separate, `frek_v1`-only
mechanism found while researching RECOVERY, worth naming precisely so it
is never confused with it**: `backend/heritage/routes.py` is a fully
implemented, notarized, append-only succession flow for `frek_v1`
identities (`declare` a beneficiary → `claim` or admin-`force` transfer →
same `frek_id`, `email_hash` ownership changes; `GET /heritage/lineage/
{frek_id}` exposes the full chain-of-custody). It already satisfies "never
regenerate a FREK-ID because control changes hands" for the one case it
covers (death, donation, retirement — see `TransferRequest.reason`'s own
docstring). Two things distinguish it from this ADR's RECOVERY: (1)
heritage transfers control to a **different** person by design; recovery
restores the **same** person's own access; (2) heritage exists only for
`frek_v1` identities (`db.frek_identities`) — `identity_engine`'s
`frek_persons` has no equivalent, a real, evidenced asymmetry between the
two identity systems, not addressed by this pass (recorded here, not
solved — a genuine C1-shaped gap for a future pass, not invented scope
for this one).

### 2.2 Institution / Organization

| Dimension | Answer |
|---|---|
| Own FREK-ID | **Registry**: yes — `POST /registry/objects/frek.organization` mints one, per `frek.organization.schema.json`. **`identity_engine`**: partial — `identity_type: "institution"` exists on `FREKIdentity` but grants no organization-specific capability (no member roster, no roles) beyond what any individual identity gets; `memory/PRD.md:648` names this gap explicitly: *"Multi-membres organizational identity (structure identity_type=professional prête, pas d'endpoint /organization)"* |
| Linked to another FREK-ID? | `frek.organization.member_ids: FREK-ID[]` — an organization references its members' FREK-IDs; the reverse link (a person declaring their org membership) is not implemented |
| Ownership/control model | `owner_id` on the Registry envelope (the identity that registered the org record) — not the same as "who can act as this organization," which is undefined |
| Authority model | Registry write authority (`_authorize_write` — OAuth2 `registry:write` or an `identity_engine` holder session) governs *editing the record*; no concept of "acting on the organization's behalf" exists |
| Representatives / delegation (mandat) | **NOT FOUND as a real mechanism.** `spec/routes.py`'s notary payload-type catalog documents a `"transfer"` type (*"Transmission de FREK-ID (heritage / delegation, P2 backlog)"*) — a named placeholder, not an implementation. `member_ids` (above) lists members but grants none of them authority to act for the organization. DOCUMENTED intent, MISSING implementation. |
| Credential model | None — a `frek.organization` Registry object has no WebAuthn credentials, no session concept; it cannot itself authenticate anywhere |
| Merge semantics | Not addressed by `0003` (that ADR is scoped to Person identities in `identity_engine`) — a `frek.organization`-to-`frek.organization` reconciliation is out of scope this pass, NOT FOUND as a distinct requirement anywhere |
| Recovery semantics | Not applicable — no credentials exist to lose |
| Key/device rotation | Not applicable |
| Lifecycle/status | Standard Registry envelope `status` (`draft`/`active`/`archived`/`revoked`) — generic, not org-specific |
| Provenance requirements | Standard Registry envelope (`created_at`, `version`, `checksum`) |
| Proof/audit requirements | Same as any Registry object — no dedicated organizational audit trail |
| Relationship to `.fk`/FAP/FREK-Chain | Referenced as `organization` in the `.fk` spec's `identity` layer (DOCUMENTED — `Context.institution` in the real code is a free string, see §2.4) |

### 2.3 Role / Authority

**Never a FREK-ID subject in this codebase — always an attribute attached to one.** Three independent role vocabularies exist, none overlapping:

| Vocabulary | Attaches to | Values | Status |
|---|---|---|---|
| `permissions.Role` (CVLN) | A `Subject.frek_id` via `RoleGrant` | `founder`/`executive`/`artist`/`student`/`teacher`/`admin_label`/`agent` | OBSERVED, not wired into any route (`permissions/__init__.py`'s own docstring) |
| `permissions.protocol_roles.ProtocolRole` | Conceptual, not a grant at all | `issuer`/`holder`/`verifier` (W3C VC roles) | OBSERVED (P2, 2026-08-31) — documented mapping to `Role`, all three map to `None` today (no route enforces them) |
| Staff `role` | `agent_id` (a **non**-FREK-ID staff account) | `SUPERVISEUR`/`EMISSION`/`ACCES`/`CASHLESS` (`staff/routes.py`) | OBSERVED — explicitly outside the FREK-ID system entirely (see §2.11) |

`docs/interfaces/AGENT_FACTORY.md`'s own text: *"The Master Prompt's 'Agent' role... does not exist as a distinct CVLN role in FREKCORE's current permission model"* — PROPOSED, not implemented.

### 2.4 Cultural Object / Work — `.fk` container

| Dimension | Answer |
|---|---|
| Own FREK-ID | Yes — `fk/routes.py`'s `POST /fk/create` mints `frek_id` for `fk_objects`; also `registry/schemas/v1/frek.track.schema.json`/`frek.album.schema.json`/`frek.work.schema.json` mint Registry-side envelopes that can carry an `fk_object_ref` pointing at one |
| Linked to another FREK-ID? | `owner_id` (Registry envelope, points to the owning Person/Institution); `artist_ids`/`creator_ids` (`frek.track`/`frek.work`, arrays of FREK-IDs) |
| Ownership/control model | `owner_id` + `_authorize_write` (Registry) / the identity that called `POST /fk/create` (`fk/`) |
| Authority model | Same as §2.1's Person, since only a Person/Institution identity can authenticate a write |
| Credential model | Not applicable to the object itself — it *carries* credentials (a `.fk`'s `credentials` layer holds a signed VC, per spec) |
| Merge semantics | **Real gap, spec vs. code**: the spec's `identity.creator`/`organization`/`device`/`contributors` are all `DID:frek:<id>` references (`FREK_Object_Model_Specification_v0.1.md` §2); the real code's `Contributor` (`fk/models.py`) is `{name, role, isni}` — plain strings, no FREK-ID linkage at all. This is not a merge-semantics gap in the MERGE/RENEW/RECOVERY sense — it is a pre-existing, separately tracked contradiction (see `reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`'s `.fk` taxonomy entry) |
| Recovery semantics | Not applicable — a `.fk` object has no credentials to recover |
| Key/device rotation | Not applicable |
| Lifecycle/status | `.fk`'s own version history (`Version`/`TimelineLayer`, `fk/models.py`); Registry envelope's generic `status` for the catalog-record side |
| Provenance requirements | `ProofLayer` (`content_hash`, `BlockRef`, `BtcAnchor`) — real, notary-integrated |
| Proof/audit requirements | `object.created` event now subscribed to the Audit Trail (this session's earlier P2 work) |
| Relationship to FAP/FREK-Chain | `BlockRef`/`BtcAnchor` in `ProofLayer` are the FREK-Chain/Bitcoin-anchoring integration points; FAP (hardware capture) itself is DOCUMENTED_ONLY (see §2.5) |

### 2.5 Work-certification (legacy `backend/frek/`)

A **third, independent** FREK-ID format, minting identities for audio works (not people): `FREK-{year}-{seq:04d}-{signal_hash[:8]}-{metadata_hash[:8]}` (`frek/nodes/node02_identity.py:_generate_frek_id`), triple-SHA-256-chained (signal, metadata, previous-block). `FrekMetadata` carries a `device_id: Optional[str]` field — the capturing device is recorded as **metadata on the work**, not as its own linked FREK-ID (device identity for this module is DOCUMENTED_ONLY per §2.6, not OBSERVED here).

Per `docs/architecture/FREK_LEGACY_ROUTE_AUDIT.md` (this session's earlier finding): this module's storage backend is architecturally PostgreSQL/`pgvector`, structurally unreachable under this deployment's `MONGO_URL` convention — every write here is non-persistent in-process memory. This taxonomy entry inherits that same caveat: the work-certification lifecycle exists in code, correctly, but produces nothing durable in the current deployment.

### 2.6 Device / Hardware

| Dimension | Answer |
|---|---|
| Own FREK-ID | **No.** `did:frek:device-<uuid>` is fully specified (`frek_v3/docs/FREK_Architecture_Integree_v0.2.md` §3.2, worked example `did:frek:device-luciole-001` issuing a `FREKCaptureCredential`) but this session's `did/document.py` grep (repeated every phase) finds no code that mints a typed or untyped `did:frek:device-*` anywhere |
| Linked to another FREK-ID? | Referenced, not linked — `.fk`'s `identity.device` field (spec only); `frek/`'s `FrekMetadata.device_id` (a free string, not a FREK-ID) |
| Ownership/control model | DOCUMENTED_ONLY: the spec assumes PUF-derived, device-owned key material (`frek_v3/docs/` FAP fields) — no such key-management code exists in `backend/` |
| Authority model | Not implemented |
| Credential model | `FREKCaptureCredential` (spec, `Ed25519Signature2020` proof) — DOCUMENTED_ONLY |
| Merge/renew/recovery semantics | Not applicable — no device identity exists to merge, renew, or recover |
| Lifecycle/status | Not implemented |
| Provenance/proof requirements | The spec's device counter/nonce/replay-protection fields match FAP's own historical field list (per the mid-session directive) but have no corresponding Proof Engine wiring found — flagged for the FAP ↔ Proof Engine reconciliation pass (§3 below) |
| Relationship to `.fk`/FREK-Chain | Would be the *issuer* of a `FREKCaptureCredential` embedded in a `.fk`'s `credentials` layer, per spec — not built |

Fingerprint module's `observe/{device,...}` (`backend/fingerprint/`) is a **different, unrelated** concept — browser/canvas/WebGL device *fingerprinting* for anti-fraud (a signal *about* a Person's session, keyed to their `frek_id`), not a device that itself holds a FREK-ID. Naming collision only, noted so it is not mistaken for FAP device identity.

### 2.7 Wallet / Account

| Dimension | Answer |
|---|---|
| Own FREK-ID | Yes, but structurally a **link record**, not an independent actor — `registry/schemas/v1/frek.wallet.schema.json`: `holder_id` (the Person's FREK-ID), `wallet_provider`, `external_wallet_ref` (opaque, owned by CVLN Wallet) |
| Linked to another FREK-ID? | Yes — `holder_id`, required |
| Ownership/control model | Controlled by whoever controls `holder_id`'s identity; the wallet record itself has no separate authority |
| Authority model | Standard Registry write authority |
| Credential model | None — explicitly, per `docs/interfaces/CVLN_WALLET.md`: *"No ledger, no balance, no transaction logic"* |
| Merge/renew/recovery semantics | Inherits the holder's — a wallet-link record has no independent lifecycle beyond `linked_at` |
| Lifecycle/status | Standard Registry envelope `status` |
| Provenance/proof requirements | `wallet.linked` event is catalogued (`event_registry.json`) but `implemented: false` — PROPOSED, not built (`docs/interfaces/CVLN_WALLET.md`'s own "Proposed next step") |
| Relationship to FAP/`.fk`/FREK-Chain | None found |

### 2.8 Software Agent / Service

| Dimension | Answer |
|---|---|
| Own FREK-ID | **Exactly one instance exists**: `did:frek:frekcore` — the platform's own institutional DID (`did/vc.py:84`'s hardcoded `issuer_did`), proven live via `.well-known/did-configuration.json` (`memory/PRD.md:169`) |
| Linked to another FREK-ID? | N/A — this is FREKCORE itself, the root issuer |
| Ownership/control model | Controlled by FREKCORE's own Ed25519 signing key (`backend/passport/keys.py`) — an institutional key, not a per-agent one |
| Authority model | Not per-agent — every VC issuance uses this one identity regardless of which internal process triggered it |
| Credential model | The Ed25519 key pair itself; no WebAuthn, no session |
| Merge/renew/recovery | Not applicable to a singleton platform identity; key rotation for it is `reports/21_FREEZE_ASSESSMENT.md`'s long-standing "Key rotation: MISSING" finding, unrelated to this taxonomy pass |
| Lifecycle/status | Not applicable |
| Other agent instances | `did:frek:app-<uuid>` (typed, per-application) is DOCUMENTED_ONLY (`FREK_Architecture_Integree_v0.2.md` §3.2), never minted. CVLN Agent Factory's autonomous-agent concept is explicitly `docs/interfaces/AGENT_FACTORY.md`'s own **"PROPOSED, NOT IMPLEMENTED"** — an agent today can only be represented as a Person (`identity_type: "professional"`) or as an `frek.organization`, both real stretches of what those types actually mean |
| Relationship to `.fk`/FAP/FREK-Chain | The institutional DID is the default `issuer` for every VC embedded in a `.fk`'s `credentials` layer unless/until per-subject issuance is built (see `permissions/protocol_roles.py`'s own note on this) |

### 2.9 Physical Asset

| Dimension | Answer |
|---|---|
| Own FREK-ID | No dedicated identity model — a physical asset becomes a `.fk` object like any other, via `object_type` (`fk/models.py`'s `OBJECT_TYPES` includes `artwork`, `heritage`, `document`, `photo`) |
| Linked to another FREK-ID? | Via the generic `.fk` `owner_id`/`creator` mechanism — no physical-asset-specific field (materials, dimensions, physical provenance) exists in code |
| Spec vs. code | `frek_v3/docs/FREK_Object_Model_Specification_v0.1.md` §3 names "FK PHYSICAL" as a full sibling category to Audio/Video/Image/Document/Asset (worked examples: objet d'art, produit, capteur IoT, document physique scanné) with its own extensibility recipe (§8: "Définir metadata spécifique (matériaux, dimensions, provenance physique)") — none of that metadata shape exists in `fk/models.py` today |
| Merge/renew/recovery | Not applicable — same reasoning as §2.4 |
| Classification | DOCUMENTED (spec) + OBSERVED only at the generic-`.fk`-container level, not as its own distinct entity shape |

### 2.10 Location / Infrastructure

**Never a FREK-ID subject.** `fk/models.py`'s `Context` model (`location: Optional[str]`, `coordinates: Optional[Dict[str, float]]`, `institution: Optional[str]`) is free-text/free-number metadata attached to a `.fk` object's `identity` layer — none of these fields is a FREK-ID reference, typed or otherwise. `backend/geo/` records a Person's geolocation *observations* (tied to their own `frek_id`, consent-gated) — it does not mint identities for places. No historical document this session found proposes location-as-FREK-ID-subject. Classified OBSERVED (as non-FREK-ID metadata) rather than NOT FOUND, since the *concept* of recording location clearly exists — just never as its own identity.

### 2.11 Certificate / Credential record

A distinct entity type worth calling out on its own, because it is the one place `expires_at` already lives as a **first-class, correctly-scoped** concept — directly relevant evidence for the RENEW decision (`0003`'s "FREK-ID itself does not renew"):

| Dimension | Answer |
|---|---|
| Own FREK-ID | Yes — `registry/schemas/v1/frek.certificate.schema.json` |
| Linked to another FREK-ID? | `holder_id` (required) |
| Lifecycle | `issued_at` / `expires_at` / `jcc_credits` — an Academy/Culture-Connect certificate genuinely does expire on its own schedule, independent of its holder's identity, exactly the pattern `0003` describes as correct ("credentials... may expire, rotate or renew... never regenerate an identity") |
| Merge/renew/recovery | A certificate's own renewal (reissuing/extending `expires_at`) is a real, currently-unbuilt capability distinct from identity renewal — flagged here as a legitimate future Registry-API item, not conflated with `identity_engine`'s RENEW decision |
| Proof/audit requirements | `signature`, `verification_url`, `qr_payload` fields already model an externally-verifiable artifact |

### 2.12 Staff / Terrain Agent (operational, non-FREK-ID)

Deliberately excluded from the FREK-ID system entirely: `backend/staff/routes.py`'s `agent_id` (`SUPERVISEUR-01`, `EMISSION-01`, etc.) is PIN-authenticated, JWT-scoped by `role`, with **no `frek_id` field anywhere** in `StaffLoginRequest`/`StaffMeResponse`/the staff account documents. This is a correct, evidenced negative finding, not a gap: terrain staff are an operational-access concept (who may operate the scanner PWA), not a cultural/provenance identity — conflating the two would be exactly the kind of invented scope this taxonomy is meant to prevent.

### 2.13 Project / Production — NOT FOUND (distinct from Event, §2.14)

Searched `backend/` (route/model names), `frek_v3/docs/`, `memory/PRD.md`,
`docs/interfaces/*.md` for "project," "production," "session studio,"
"campagne," "formation" as a FREK-ID-bearing entity concept (a
multi-work container with its own identity, as opposed to a single
`.fk`). No route, no schema, no historical specification section names
this. Not classified further — there is nothing to classify. If KORA,
LabelOS, or Academy needs a Project entity, that is new scope for whoever
builds it, not a gap in FREKCORE's existing model.

### 2.14 Événement vérifiable (verifiable event)

Distinct from "Project" (§2.13) precisely because there **is** real
evidence for this one — a cultural event is already a first-class,
FREK-ID-bearing Registry entity, not a human-identity-shaped subject but
an addressable/traceable one, matching the founder's own framing.

| Dimension | Answer |
|---|---|
| Own FREK-ID | Yes — `registry/schemas/v1/frek.event.schema.json` |
| Linked to another FREK-ID? | Via the generic Registry `owner_id`; no `organizer_id`/`participant_ids` field found — an event's relationship to the people/orgs running it is not yet modeled beyond ownership |
| Ownership/control model | Standard Registry `_authorize_write` |
| Credential model | None |
| Merge/renew/recovery | Not applicable — same reasoning as §2.2/§2.4: no credentials, so nothing to recover; a duplicate-event reconciliation is NOT FOUND as a requirement anywhere |
| Lifecycle/status | Standard Registry envelope `status`; `starts_at`/`ends_at` for the event's own real-world timing (distinct from the envelope's `status` lifecycle) |
| Provenance/proof requirements | Standard Registry envelope only — no event-specific proof mechanism found |
| Relationship to `.fk`/FAP/FREK-Chain | None found beyond the generic Registry envelope; a `frek.event` does not currently reference the `.fk` objects captured at it |

### 2.15 Droits / mandat / relation juridique (rights, mandate, legal relationship)

**Confirmed: a linked-object concept, not an autonomous FREK-ID**, exactly
as the founder's own framing anticipates ("probablement pas un FREK-ID
principal... plutôt des objets liés au graphe d'identité"). Evidence:

| Where | What it models |
|---|---|
| `fk/models.py`'s `RightsLayer` | `owner: Contributor`, `co_owners: List[Dict]` — attached to a `.fk` object, referencing people by free-text `Contributor` (name/role/isni), not by FREK-ID (same gap as §2.4's creator/contributor fields) |
| `frek_v3/docs/FREK_Object_Model_Specification_v0.1.md` §2 | `rights.splits` (répartition des droits), `rights.contributors` (rôles et pourcentages) — DOCUMENTED, not implemented (code has no `splits` field) |
| `registry/schemas/v1/frek.certificate.schema.json` | `holder_id`, `issuer` — a certificate *is* a rights-adjacent artifact with its own `frek_id`, already covered in §2.11 |

No mechanism anywhere establishes a **mandate** (one FREK-ID authorized to
act legally on another's behalf) as a first-class, verifiable relationship
— the closest adjacent concepts are the Organization's undelivered
delegation placeholder (§2.2) and `frek_v1`'s Heritage/Transmission module
(§2.1), neither of which is a general-purpose mandate mechanism. NOT
FOUND as its own entity; DOCUMENTED as a rights-attachment concept;
classified here explicitly so it is not silently treated as equivalent to
an identity going forward, per the founder's own caution.

## 3. What this means for entity-aware MERGE/RENEW/RECOVERY

`docs/decisions/0003-identity-lifecycle-founder-decisions-implemented.md`'s
approved semantics apply, by evidence, to exactly one entity type as
implemented today: **Person / Institution identities in
`backend/identity_engine`** — the only entity type in this taxonomy that
has (a) its own authentication credentials (WebAuthn Passkeys) that can be
lost, (b) its own holder-session-based authority model that "recovery"
and "cross-holder takeover" are meaningful concepts against, and (c) no
built-in expiry (making "FREK-ID does not renew" a live distinction rather
than a moot one).

Every other FREK-ID-bearing entity type in this taxonomy is either:

- **Owned by, not itself a holder of, credentials** (`.fk` objects,
  `frek.organization`, `frek.wallet`, `frek.certificate` — all Registry
  envelopes with `owner_id`/`holder_id` pointing at a Person/Institution).
  For these, "recovery" is meaningless (nothing to lose) and "merge" would
  mean something entirely different (e.g. two catalog records for the same
  underlying work) — **not** addressed by `0003` and **not** implemented
  by this pass. A future reconciliation for Registry objects, if ever
  needed, is separate scope.
- **DOCUMENTED_ONLY, never minted** (typed device/org/app DIDs, FAP) — no
  code exists for MERGE/RENEW/RECOVERY to apply to.
- **Deliberately outside the FREK-ID system** (Staff/Terrain agents).

Implementation of `identity_engine`'s `POST /{frek_id}/reconcile` (MERGE),
the RENEW documentation/regression-test pass, and the admin-key RECOVERY
path is therefore correctly scoped to `identity_engine`'s `frek_persons`
collection only — this document is the evidence for why that scoping is
entity-aware rather than an unexamined default, per the founder's
instruction.

## 4. The canonical model, going forward

The founder's own framing, confirmed rather than contradicted by every
finding above: **FREK-ID is the canonical identifier of an addressable,
verifiable entity; `entity_type` then selects which rules apply.** This
is not a new invention this document is proposing — it is already the
literal shape of the Registry API's own envelope
(`registry/schemas/v1/_base.schema.json`: every object carries `frek_id`
+ `entity_type`, and each namespace's schema is exactly "the base envelope
plus this type's own rules"). The gap this taxonomy closes is that
`identity_engine`'s lifecycle work (revoke/update/archive/search, and now
merge/renew/recovery) was designed and reasoned about as if every FREK-ID
behaved like a Person's — this document is the record that it was
checked, not assumed, and does not.

Per-type asymmetry this evidence actually supports (not a speculative
target design, a description of what already exists or is already
decided):

| Entity type | Has credentials to recover? | Has keys/devices to rotate? | Has representatives/delegation? | Has provenance/ownership? |
|---|---|---|---|---|
| Person | **Yes** (WebAuthn Passkeys) | Yes (same mechanism) | N/A | Yes (`linked_objects`, `created_at`) |
| Institution/Organization | No | No | DOCUMENTED gap, not implemented (§2.2) | Yes (Registry envelope) |
| Cultural Object (`.fk`) | No | N/A | N/A | Yes — its defining feature (`ProofLayer`, `RightsLayer`) |
| Device (FAP) | DOCUMENTED_ONLY — PUF-derived key rotation is spec'd, not built | DOCUMENTED_ONLY | N/A | DOCUMENTED_ONLY |
| Software Agent | No (institutional key only) | No | N/A | N/A |
| Wallet/Certificate | No | No | N/A | Yes (`holder_id`/`issuer`, `expires_at` for certificates) |

No entity type in this codebase currently has a "capabilities/scopes"
model the way an autonomous software agent eventually would (`Permission`
in `identity_engine/models.py` is explicitly `"Extensible pour futur
multi-tenant / role-based"` — PROPOSED shape, not populated) — recorded
here as the honest current answer, not filled in with an invented one.

This table is descriptive, not a commitment to build every empty cell —
each MISSING/DOCUMENTED_ONLY gap it names was already tracked elsewhere
in this taxonomy (§2) with its own evidence; this table exists so the
per-type asymmetry itself, not just each individual gap, is visible in
one place.
