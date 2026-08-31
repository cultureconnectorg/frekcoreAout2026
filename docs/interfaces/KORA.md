# Interface: KORA (DSP / Catalogue / Royalties)

**Role of FREKCORE**: Artist / Track / Album resolver + cultural-object provenance proof. No royalty calculation, no streaming/CVE logic.

## What FREKCORE exposes today

| Capability | Route | Evidence |
|---|---|---|
| Cultural object detail (a track/album packaged as a `.fk`) | `GET /api/v1/fk/detail/{id}` | `backend/fk/routes.py`, `memory/INVENTORY.md:65` |
| Offline, third-party-verifiable proof of a track's existence/integrity | `POST /api/v1/fk/verify` (public, anonymous) | `memory/INVENTORY.md:176` |
| Catalogue stats | `GET /api/v1/fk/stats` | `backend/fk/routes.py` |

## What this session added (Bloc 1)

Three namespaces give KORA a stable, versioned shape to resolve against:

- **`frek.artist`** — `display_name`, `isni`, `aliases`, `primary_role`, `verified`/`verified_by` (so KORA can mark an artist as verified and FREKCORE's schema will validate the resulting record), `organization_ids` (link to `frek.organization`, e.g. a label).
- **`frek.track`** — `title`, `artist_ids` (≥1, required), `album_id`, `isrc`, `iswc`, `duration_seconds`, `fk_object_ref` (pointer to the underlying `.fk` container carrying the actual audio + Ed25519 proof).
- **`frek.album`** — `title`, `artist_ids`, `track_ids`, `upc`, `release_date`.

`GET /api/v1/registry/namespaces/frek.track` returns the full JSON Schema so KORA can validate its own catalogue ingestion against the canonical FREK shape before writing to its own database.

## Explicitly out of scope (belongs in KORA's own repository)

- CVE v1.2 royalty computation.
- Streaming delivery, DSP aggregation, play-count ingestion.
- The `artist.verified` event (catalogued as `implemented: false`) is not emitted anywhere in FREKCORE today — see `reports/02_GAP_ANALYSIS.md` Bloc 7. KORA marking an artist `verified: true` in its own system does not currently trigger any FREKCORE-side event; this is a documented gap, not a working notification channel.

## Registry instance store — DELIVERED (2026-08-31)

The gap this section used to describe is closed: `backend/registry/routes.py` now persists real objects into a `registry_objects` MongoDB collection, schema-validated before insert.

- **`GET /api/v1/registry/objects/frek.artist/{frek_id}`** is that proposed resolver, in substance — same lookup, kept under `/objects` (the resource's natural REST path) rather than a separate `/resolve` path. Public, no auth, returns 404 if the artist hasn't been registered.
- **`GET /api/v1/registry/objects/frek.artist`** lists artists (paginated, filterable by `owner_id`/`status`).
- **`POST /api/v1/registry/objects/frek.artist`** creates one — requires either an OAuth2 client credential with the `registry:write` permission (KORA's own integration path, once provisioned as a `frek_clients` entry the way `kiltikonet-cc2026` already is) or an `identity_engine` holder session (an artist self-publishing their own record). See `docs/architecture/FREK_ID_RECONCILIATION.md`-adjacent write-up in `backend/registry/routes.py`'s module docstring for the full authority rationale.

Live-tested end-to-end against a real (mongomock-backed) server: `backend/tests/test_registry_objects.py`.
