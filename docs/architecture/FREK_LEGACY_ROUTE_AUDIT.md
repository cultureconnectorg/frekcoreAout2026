# FREK Legacy Route Audit — `backend/frek/` ("FREK v2")

Per founder directive §9–11 (`docs/decisions/0001-founder-decisions-2026-08-31.md`): `backend/frek/` is **NOT authorized for deletion, NOT globally deprecated** — reclassified **"HISTORICAL FREK — UNDER RECONCILIATION"**. This document is the individual, per-route audit required before any route-level decision, using the classification vocabulary founder directive §11 defines (PRESERVE / HARDEN / ABSORB / MIGRATE / ADAPTER / SUPERSEDE / DEPRECATE / NEEDS_FOUNDER_DECISION).

**Update (2026-08-31) — the 19 `NEEDS_FOUNDER_DECISION` routes below are `FOUNDER_RESOLVED / TECHNICAL_RECONCILIATION_REQUIRED`, not open questions.** The founder decision this status change records: the 19 routes marked `NEEDS_FOUNDER_DECISION` in the tables below map to exactly 5 historical FREK capabilities (Signal/Audio Fingerprint, Creative Lifecycle, Relationship/Provenance Graph, Offline Proof Transport, Human-Readable Technical Evidence), and the founder has explicitly decided **all five must be preserved** — see `reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md` for the founder decisions (D1–D6), the corrected route paths (this document's tables below omit the real `/advanced` path segment for every `routes_advanced.py` route — see that report's §B), and the per-route/per-capability technical reconciliation. The per-route classifications below (`NEEDS_FOUNDER_DECISION`) are left as originally written — they are the accurate record of what this audit found before the founder decision; the reconciliation report is the current, authoritative status for what happens next. No route classification below has been changed to `SUPERSEDE`/`DEPRECATE`/`DELETE` — none of the five capabilities is authorized for deletion.

**Update (2026-09-01) — D1's 3 routes (`/certify`, `/certify/upload`, `/verify/{frek_id}`) move from `TECHNICAL_RECONCILIATION_REQUIRED` to `IMPLEMENTED`.** `docs/decisions/0004-d1-signal-fingerprint-founder-decisions-implemented.md` records the founder's D1 decision (PRESERVE + VALIDATE + HARDEN + ABSORB) and its execution: `backend/content_binding/` is the new, canonical, hardened implementation — real MongoDB persistence, auth, rate limiting, idempotency, D6 evidence semantics, and a real-librosa validation pass (`reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`) that found and fixed one genuine defect (a too-short clip silently producing a `NaN` fingerprint). **These 3 historical routes themselves are unchanged** — zero lines of `backend/frek/` touched — per the explicit instruction not to perform destructive route migration this state; their own eventual fate (legacy adapter vs. deprecation) remains a separate, later ecosystem-consumer-audit decision. D2–D5 (the other 16 routes) remain `TECHNICAL_RECONCILIATION_REQUIRED`, unstarted.

**Update (2026-09-02) — D2's 2 routes (`/genesis`, `/workshop`) move from `TECHNICAL_RECONCILIATION_REQUIRED` to `IMPLEMENTED`.** `docs/decisions/0005-d2-creative-lifecycle-founder-decisions-implemented.md` records the founder's D2 decision (PRESERVE + ABSORB) and its execution: `backend/creative_lifecycle/` is the new, canonical implementation — real MongoDB persistence, event-sourced, authenticated, structurally separate from `frek_v1`'s participant/badge use of the same vocabulary (a verified collision, not assumed). **These 2 historical routes themselves are unchanged** — zero lines of `backend/frek/` touched. D3–D5 (the other 14 routes) remained `TECHNICAL_RECONCILIATION_REQUIRED`, unstarted, as of this update (see the next update for D3).

**Update (2026-09-02) — D3's 7 routes (all `/reseau/*`) move from `TECHNICAL_RECONCILIATION_REQUIRED` to `IMPLEMENTED`.** `docs/decisions/0006-d3-relationship-provenance-graph-founder-decisions-implemented.md` records the founder's D3 decision (PRESERVE_MIGRATE) and its execution: `backend/relationship_graph/` is the new, canonical implementation — real MongoDB persistence, authenticated, bounded-traversal-only, structurally separates TRUST (verifiable) from CULTURAL (inferred) relationships (a CULTURAL relationship can never reach VERIFIED status, enforced structurally). Of the historical 17 declared relation types, only 5 (`cree_par`, `emis_a`, `contient`, `dominante_de`, `similar_to`) were ever actually emitted by `register_emission` — confirmed by reading every call site, not assumed from this document's or the module's own "17 types" description; full per-type disposition record in `backend/relationship_graph/models.py` and `GET /api/v1/relationships/historical-taxonomy`. **These 7 historical routes themselves are unchanged** — zero lines of `backend/frek/` touched, confirmed by a static-import test and a route-count regression guard. D4–D5 (the other 7 routes) remained `TECHNICAL_RECONCILIATION_REQUIRED`, unstarted, as of this update (see the next update for D4).

**Update (2026-09-02) — D4's 6 routes (all `/transmission/*`) move from `TECHNICAL_RECONCILIATION_REQUIRED` to `IMPLEMENTED`.** `docs/decisions/0007-d4-offline-proof-transport-founder-decisions-implemented.md` records the founder's D4 decision (PRESERVE_ADAPTER) and its execution: `backend/offline_transport/` is the new, canonical implementation — a transport-independent, cryptographically verifiable envelope (Ed25519 via `passport.keys`) + sync/reconciliation service. The historical packet's `signature_short` was an unverified 8-character hash prefix, never a real signature over anything — confirmed by reading the whole file, not assumed. `frek_v3/reference_verifier/` (FAP), previously confirmed fully isolated from `backend/`, is genuinely called for the first time (`offline_transport/fap_adapter.py`) for device attestation. **These 6 historical routes themselves are unchanged** — zero lines of `backend/frek/` touched, confirmed by a static-import test and a route-count regression guard. D5 (the last route) remains `TECHNICAL_RECONCILIATION_REQUIRED`, unstarted.

## Route count correction

The route count carried in every prior report (`docs/PERMISSION_MATRIX.md`, `reports/FREKCORE_CONTRADICTIONS.md` C4) was **33**. Reading both files in full this pass counts **43 routes**: 13 in `backend/frek/routes.py` + 30 in `backend/frek/routes_advanced.py`. Corrected here with the exact list below; the prior "33" figure is not re-derivable from the code as written and is treated as a stale estimate, not evidence of routes since removed.

**Update (2026-08-31)**: this section originally said 42 (13+29) — an off-by-one in its own header arithmetic, found while re-verifying this audit's claims for the P1 backlog. The per-route tables below were already complete and correct (every one of NODE06's 7, NODE07's 6, NODE08's 5, NODE09's 6, and NODE10's 6 `routes_advanced.py` routes was already individually classified) — only this summary sentence's count was wrong, re-verified directly against `grep -c "@advanced_router\.\(get\|post\|put\|delete\)" backend/frek/routes_advanced.py` = 30. No `frek/` code changed.

## The single most important finding: `backend/frek/`'s real storage backend

**`backend/frek/`'s NODE04 (Mémoire) and NODE06 (Réseau) are architecturally built for PostgreSQL + `pgvector`, not MongoDB** — completely separate from every other FREKCORE module. Evidence:

```python
# backend/frek/nodes/node04_memory.py:87-93
from pgvector.asyncpg import register_vector
database_url = os.environ.get('MONGO_URL', '')
# Si pas de PostgreSQL, utiliser stockage mémoire
if not database_url.startswith('postgres'):
    return None
```

It reads `MONGO_URL` (a MongoDB connection string, by name and by every other module's convention) and only activates its PostgreSQL pool if that string happens to start with `postgres` — which it never does anywhere in this codebase (`.env.example`, `docker-compose.yml`, every other module's own DB access all treat `MONGO_URL` as a `mongodb://` string). **This is not "PostgreSQL isn't provisioned in this sandbox" — it is a structurally unreachable code path under this deployment's actual environment-variable convention.** No `DATABASE_URL`/`POSTGRES_*` variable exists anywhere in this repository's configuration surface (`grep` across `.env.example`, `docker-compose.yml`, `backend/requirements.txt` found none).

**Consequence**: every write through `backend/frek/`'s NODE04/NODE05/NODE06 pipeline (certifications, genesis/workshop entries, the resonance/graph index) falls back to **pure in-process Python memory** (`node04_memory.py`'s own fallback comment: `"storage_backend": "memory" if await self._get_pool() is None else "pgvector"`). Nothing persists across a server restart. `grep -rn "db\.\|MongoClient|motor" backend/frek/nodes/*.py` found zero MongoDB usage anywhere in the node implementations. This is a structural fact, not a configuration oversight fixable by an env var tweak elsewhere — evidenced directly in the code, not inferred.

**Why this matters for classification**: a route whose writes never survive a restart cannot be "PRESERVE"d as a working production capability as-is — preserving it would mean preserving a capability that silently doesn't do what its own API contract implies (a client calling `POST /certify` reasonably expects the resulting FREK-ID to be retrievable later). This is the dominant factor behind several routes below being classified ABSORB or NEEDS_FOUNDER_DECISION rather than PRESERVE, even where the underlying *concept* (audio certification, resonance search) is real, original FREK IP worth keeping.

## Second finding: `frek/`'s "FREK-ID" is a different concept than `frek_v1`'s or `identity_engine`'s

`backend/frek/`'s own header (`routes.py:2-4`, `frek_stats`'s NODE map) is explicit: this FREK-ID identifies a **creative work** (an audio recording), minted from a **triple SHA-256** over the extracted 528-dimension frequency vector plus metadata (`nodes/node02_identity.py`) — not a person, not an event badge. `frek_v1`'s FREK-ID (Contradiction C1) identifies an event participant. `identity_engine`'s frek_id identifies a WebAuthn-registered person. **All three use the identical stage-name lifecycle (GENESIS → WORKSHOP → METAMORPHOSE/... → EMISSION → LEGACY, `frek/routes.py`'s NODE03 vs. `frek_v1/models.py:STAGE_ORDER`) for three different kinds of subject** (work / event-badge-person / long-lived-person). This is not the same overload as C1 (which is about two systems both minting *person* identities) — it is a third, distinct overload: the same lifecycle vocabulary applied to an entirely different *kind* of subject. Recorded here and cross-referenced into `docs/architecture/FREK_ID_CANONICAL_MODEL.md`; not resolved in this document.

## Per-route audit

Grouped by NODE (each NODE's routes share purpose/auth/data/security characteristics almost entirely; final classification is per-route). Every route: **AUTHENTICATION: none found** (`grep -n "Depends|Header|x_admin|require_" backend/frek/routes.py backend/frek/routes_advanced.py` → zero matches) — confirmed, not assumed. **EVENTS: none** — no `eventbus`/`audit_trail` usage anywhere in `backend/frek/`. **PROOFS: none** — no `notary`/`proof_engine` usage. **IDENTITY RELATIONSHIP**: mints its own FREK-ID namespace, disjoint from both `frek_v1` and `identity_engine` (see finding above) — not cross-referenced to either.

### NODE01–02 — Extraction & Identity (`routes.py`)

| Route | Purpose | Data written | Modern equivalent | Security risk | Classification |
|---|---|---|---|---|---|
| `POST /frek/certify` | Full pipeline: audio → 528D vector → triple-SHA-256 FREK-ID → in-memory record | In-process memory only (see finding above) | None — `.fk`/`passport` certify real creative-work provenance differently (manifest+signature, not a frequency vector) | Unauthenticated; also accepts up to 100MB base64 payload per call with no rate limit — real DoS surface even before considering the identity question | **NEEDS_FOUNDER_DECISION** — real, original concept (audio-frequency-fingerprint certification); current implementation cannot honestly preserve data; founder must decide whether this concept moves to a real (MongoDB-backed) implementation (ABSORB) or is retired (DEPRECATE) |
| `POST /frek/certify/upload` | Same as `/certify`, multipart upload instead of base64 | Same (in-memory) | Same | Same, plus no file-type/content validation beyond a byte-size floor | Same as `/certify` |
| `POST /frek/extract` | NODE01 alone — vector extraction without certifying | In-memory (transient, not even stored beyond the response) | None | Low (no persistence, debug/preview tool per its own docstring) | **PRESERVE** as a debug utility if kept at all, else DEPRECATE with it — low individual risk either way |
| `GET /frek/verify/{frek_id}` | Look up a certification by FREK-ID | Read from the same in-memory store | None | Low read risk, but returns data that (per the finding above) will not exist after any restart — a functional-correctness issue more than a security one | **NEEDS_FOUNDER_DECISION** (tied to `/certify`'s fate) |
| `GET /frek/verify/{frek_id}/qr.png` | QR code linking to a public verify URL | None (renders from `/verify` lookup) | `.fk`/`passport` have their own QR/verification flows | Low | **ADAPTER candidate** if `/certify`'s concept is ABSORBed elsewhere — the QR-rendering behavior itself is reusable | 
| `GET /frek/verify/{frek_id}/certificat.pdf` | PDF certificate for a certification | None | None found elsewhere in FREKCORE (no other module generates a PDF certificate) | Low | **PRESERVE the capability** (PDF certificate generation is genuinely useful and not duplicated), **NEEDS_FOUNDER_DECISION** on where its data comes from once `/certify`'s storage question is resolved |
| `GET /frek/` (info) | Static NODE map / doctrine text | None | None | None — read-only, no PII, no side effect | **PRESERVE** — this is the clearest expression of FREK's original 11-node vision in the codebase; valuable as documentation even independent of the implementation questions above |
| `GET /frek/stats` | Aggregate counts from `pipeline.get_stats()` | None | None | Low | **PRESERVE** (harmless read), contingent on `/certify` |

### NODE03 — Cycle (lifecycle) (`routes.py`)

| Route | Purpose | Classification |
|---|---|---|
| `POST /frek/genesis` | Declares creative intent before a work exists (`pipeline.start_genesis`) | **NEEDS_FOUNDER_DECISION** — same in-memory-persistence issue; the *concept* (intent declared before creation, "l'œuvre existe dans FREK avant d'exister dans le monde") is genuinely distinct from `frek_v1`'s GENESIS (a person's badge issuance) and from `identity_engine` (no lifecycle at all yet) — worth preserving as a concept, not as this implementation |
| `POST /frek/workshop` | Adds a private, timestamped intermediate version | **NEEDS_FOUNDER_DECISION** — same reasoning as `/genesis` |

### NODE05 — Résonance (`routes.py`)

| Route | Purpose | Classification |
|---|---|---|
| `POST /frek/resonance`, `GET /frek/resonance/{frek_id}` | Cosine-similarity search across certified works ("what vibrates like this") | **ABSORB candidate** — a real, distinctive FREK concept (frequency-similarity search across a creative-work corpus) not found in any other module; if pursued, needs a real vector-index backend (the `pgvector` intent was directionally right, just never wired to a reachable database) |
| `GET /frek/coherence/{artiste_id}` | Style-consistency score across an artist's certified works | **ABSORB candidate**, same reasoning — depends on `/certify`'s data actually persisting first |

### NODE06 — Réseau (graph) (`routes_advanced.py`)

`GET /frek/reseau`, `/reseau/stats`, `/reseau/node/{id}`, `/reseau/neighbors/{id}`, `/reseau/artiste/{id}`, `/reseau/lieu/{id}`, `/reseau/path` — 7 read-only routes over a graph of "5 node types, 17 relations" (per `frek_stats`'s own description). Same PostgreSQL/pgvector-only, in-memory-fallback storage as NODE04 — the graph itself is not persisted either. **NEEDS_FOUNDER_DECISION** as a group: real conceptual value (a living creative-network graph — creator/place/work/event relations) that nothing else in FREKCORE currently models, but zero of it survives a restart today.

### NODE07 — Transmission (`routes_advanced.py`)

`GET /transmission`, `/transmission/protocols`, `/transmission/protocol/{id}` (3 reads) + `POST /transmission/packet`, `/transmission/watermark`, `/transmission/sync` (3 writes, in-memory `Node07Transmission` instance state, confirmed no DB access in `node07_transmission.py`). Documents an offline-first transmission doctrine (BLE/NFC/WiFi/Ultrasound) with an `OfflineCertification` dataclass carrying a `local_storage_path` field — i.e. this NODE's own design already anticipates local-disk persistence, never implemented. **NEEDS_FOUNDER_DECISION** — offline-first transmission is a real, unduplicated FREK concept (no other module addresses "how does a certification survive with no network"), but nothing here is wired to actual storage, network transport, or ultrasonic hardware — it is a well-specified interface with an unimplemented backend.

### NODE08 — Système (`routes_advanced.py`)

`GET /systeme`, `/systeme/position`, `/systeme/references`, `/systeme/roadmap`, `/systeme/integrations` — 5 read-only routes, all static/doctrine text (positioning FREK relative to Dolby/Shazam/Siri, an adoption roadmap, an integrations list). No data written, no security surface. **PRESERVE as documentation** — these routes are effectively a machine-readable pitch deck; harmless, arguably useful, zero risk either way, not urgent.

### NODE09 — Juridique (`routes_advanced.py`)

`GET /juridique`, `/principle`, `/protection`, `/jurisdictions`, `/compliance` (5 reads, static/doctrine) + `POST /juridique/attestation` (`create_attestation`, in-memory `Node09Juridique` state — no DB access confirmed). The reads articulate FREK's own legal doctrine precisely ("FREK atteste un fait technique — jamais un droit": a technical fact, never a legal right) — this is exactly the kind of conceptual IP founder directive §12 says must not be normalized away. **PRESERVE the reads** (doctrine, zero risk). **NEEDS_FOUNDER_DECISION on `/attestation`** — "technical-legal attestation" sounds adjacent to `backend/notary/`'s real, MongoDB-backed, hash-chained attestation mechanism (Proof Engine level 2, `reports/18_RUNTIME_VALIDATION.md`), but this route produces an unrelated, non-persisted, non-notarized object under the same word ("attestation") — a naming collision worth the founder's explicit attention before deciding whether this is the same concept poorly implemented (→ SUPERSEDE by `notary`) or a genuinely different one (→ ABSORB as its own thing).

### NODE10 — Institutionnel (`routes_advanced.py`)

`GET /institutionnel`, `/offers`, `/oapi`, `/cvl-brain`, `/sovereignty`, `/observatory` — 6 read-only routes, all static/doctrine content (OAPI = the 17-country African intellectual-property organization; CVL BRAIN references the sibling FREK ecosystem product; data-sovereignty framing; a "cultural observatory" metrics stub). **PRESERVE as documentation** — zero write surface, zero security risk, articulates real positioning (OAPI, data sovereignty) not expressed anywhere else in the codebase.

### NODE11 — Expérience

No routes found under this name in either file. `frek_stats`'s own NODE map describes it ("3% visible, 1 bouton" — a minimal-UI philosophy) but it has no backend surface — this is a frontend/UX concept, not a missing backend route. Not audited further here; cross-reference for the UI/UX mission when it runs (not this session).

## Summary disposition

**Update (2026-08-31)**: this table originally read 15/4/1/22/0 (summing to 42, the same off-by-one this document's opening section already corrected). Recounted here route-by-route against the per-route tables above — every individual route's classification is unchanged; only this aggregate table's arithmetic was wrong (it undercounted PRESERVE, most, and overcounted NEEDS_FOUNDER_DECISION and ABSORB, likely from counting `/reseau/*` toward ABSORB in an earlier draft before the NODE06 section settled it as NEEDS_FOUNDER_DECISION-as-a-group).

| Classification | Count | Routes |
|---|---|---|
| PRESERVE | 20 | routes.py: `/extract`, `/verify/{frek_id}/certificat.pdf`, `/` (info), `/stats` (4). routes_advanced.py: all 5 NODE08 `/systeme*` reads, all 5 NODE09 `/juridique*` reads (excl. `/attestation`), all 6 NODE10 `/institutionnel*` reads (16) |
| ABSORB candidate | 3 | `/resonance` (POST + GET), `/coherence` |
| ADAPTER candidate | 1 | QR code rendering (`/verify/{frek_id}/qr.png`) |
| NEEDS_FOUNDER_DECISION | 19 | routes.py: `/certify`, `/certify/upload`, `/verify/{frek_id}`, `/genesis`, `/workshop` (5). routes_advanced.py: all 7 NODE06 `/reseau/*` routes, all 6 NODE07 `/transmission/*` routes, `/juridique/attestation` (14) |
| SUPERSEDE / DEPRECATE / MIGRATE | 0 | None found — no route in this module was found to have a clean, semantically-equivalent modern replacement already built; every apparent overlap (`/juridique/attestation` vs. `notary`) turned out to need founder input rather than being a clean supersession |

20 + 3 + 1 + 19 + 0 = 43, matching the corrected route count above.

**No route in this audit was found safe to authenticate, harden, or modify in-place this session** — every mutation's real defect (non-persistent storage) is architectural, not a missing `Depends(...)`, and fixing it would mean either wiring a real database (new scope, a capability decision) or accepting the ephemeral-memory behavior as intentional for a debug/demo surface (also a decision). Per founder directive §28, this stops for founder input rather than guessing.
