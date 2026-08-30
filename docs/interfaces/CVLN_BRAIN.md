# Interface: CVLN Brain

**Role of FREKCORE**: Identity Lookup Service for analytics. FREKCORE computes no analytics itself.

## What FREKCORE exposes today

| Capability | Route | Evidence |
|---|---|---|
| Identity lookup (already used by an existing external client) | `/api/v1/*` (client `cvl-brain` seeded with `permissions: ["stats"]`) | `backend/server.py:465-471` — **CVLN Brain already exists as a seeded API client in this codebase**, unlike the other 6 systems in this directory |
| Aggregate stats already exposed | `GET /api/v1/fk/stats`, `GET /api/v1/event/stats/live`, `GET /api/v1/event/stats/export` | `backend/fk/routes.py`, `backend/event/routes.py:173-236` |

This is the one CVLN system in Phase 15 that already has a concrete, working integration point in the code (`FREK_CLIENT_CVLBRAIN_ID`/`FREK_CLIENT_CVLBRAIN_SECRET` env vars, `server.py:466-471`) — the gap is documentation, not implementation.

## What this session added (Bloc 1)

`GET /api/v1/registry/events` gives CVLN Brain a machine-readable list of every event type FREKCORE intends to emit (with honest `implemented: true/false` flags) — useful for Brain to know in advance which analytics signals are real today (`proof.generated`, via the legacy stage log) versus planned (`identity.created`, `wallet.linked`, ...).

## Explicitly out of scope (belongs in CVLN Brain's own repository)

- Analytics computation, dashboards, ML models.
- Any reasoning over the raw stats FREKCORE exposes.

## Proposed next step (PROPOSED, NOT IMPLEMENTED)

Extend the `stats` permission scope to also cover `GET /api/v1/registry/events` and `GET /api/v1/registry/namespaces` (today these are unauthenticated/public, so no extension is strictly required — noted here only for completeness of the permission audit in `reports/05_SECURITY_REPORT.md`).
