# Interface: CVLN Agent Factory

**Role of FREKCORE**: FREK-ID issuance for agent identities + the Event Registry catalog as a shared vocabulary. FREKCORE does not orchestrate agents, hold agent memory, or provide tools.

## What FREKCORE exposes today

| Capability | Route | Evidence |
|---|---|---|
| Issue a FREK-ID for any entity (an agent can be represented as `identity_type: "professional"` or via `frek.organization`) | `POST /api/v1/identity/init` | `backend/identity_engine/routes.py`, `identity_engine/models.py:49-53` (`InitIdentityRequest`) |
| Scoped API-client permissions (the closest existing primitive to an "agent with limited permissions") | `frek_clients.permissions[]` | `backend/frek_v1/auth.py:50-58` |

## What this session added (Bloc 1 / Bloc 7)

- `GET /api/v1/registry/namespaces` — Agent Factory can validate that an object it is about to hand to an agent (e.g. a `frek.certificate` or `frek.track`) matches the canonical FREK shape before acting on it.
- `GET /api/v1/registry/events` — a shared, versioned vocabulary of event types agents might react to. Today `implemented: false` for most entries (see `reports/02_GAP_ANALYSIS.md` Bloc 7) — Agent Factory should not build subscriptions against events that have no producer yet.

## Explicitly out of scope (belongs in Agent Factory's own repository)

- Agent registry/orchestration, tool definitions, agent memory.
- The Master Prompt's "Agent" role (Bloc 6: "Permissions limitées") does not exist as a distinct CVLN role in FREKCORE's current permission model (`reports/05_SECURITY_REPORT.md` §6) — Agent Factory should not assume FREKCORE can already scope an agent's access down to "its own works only" until Bloc 6 is redesigned.

## Proposed next step (PROPOSED, NOT IMPLEMENTED)

Adding an `Agent` role to the Permission Engine redesign (see `reports/02_GAP_ANALYSIS.md` priority #2) is a prerequisite before Agent Factory can safely be granted scoped, auditable access to FREKCORE identities on behalf of autonomous agents.
