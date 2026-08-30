# Interface: LabelOS

**Role of FREKCORE**: Catalogue Resolver (artists, tracks, albums, organizations) + provenance proof. No rights management, no distribution, no contracts.

## What FREKCORE exposes today

| Capability | Route | Evidence |
|---|---|---|
| Catalogue object detail/verification | `GET /api/v1/fk/detail/{id}`, `POST /api/v1/fk/verify` | `backend/fk/routes.py` |
| Heritage/versioning for long-term catalogue preservation | `/api/v1/heritage/*` | `backend/heritage/routes.py` |

## What this session added (Bloc 1)

All four catalogue namespaces are relevant to LabelOS: `frek.artist`, `frek.track`, `frek.album` (see `KORA.md` for their shapes), plus **`frek.organization`** — `legal_name`, `org_type` (`label|academy|foundation|studio|group|collective|other`), `member_ids` (FREK-ID references, e.g. signed artists), `parent_organization_id` (e.g. FMS under CVLN Group). This lets LabelOS validate its own label/roster structure against a canonical shape:

```json
{
  "frek_id": "id-...",
  "entity_type": "frek.organization",
  "status": "active",
  "created_at": "2026-08-30T00:00:00Z",
  "legal_name": "Factory Maker Studio",
  "org_type": "label",
  "member_ids": ["id-artist-1", "id-artist-2"],
  "parent_organization_id": "id-cvln-group"
}
```

## Explicitly out of scope (belongs in LabelOS's own repository)

- Rights/licensing contracts, revenue splits.
- Distribution to DSPs.
- `fk.rights` (`backend/fk/models.py:99-104`, `RightsLayer`) already models `owner`/`co_owners`/`licenses`/`transfers` at the *object* level inside a single `.fk` container — LabelOS may read this via `GET /api/v1/fk/detail/{id}` but FREKCORE does not aggregate rights across a catalogue; that aggregation belongs in LabelOS.

## Proposed next step (PROPOSED, NOT IMPLEMENTED)

A read-only catalogue export endpoint scoped by `organization_id` — requires the Registry instance-store gap (see `KORA.md`) to be closed first.
