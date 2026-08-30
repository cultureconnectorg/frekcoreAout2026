# Interface: Laurentia

**Role of FREKCORE**: Identity Memory Resolver — a stable, safe-to-quote identity fact source for Laurentia's memory/RAG/reasoning layer. FREKCORE stores no embeddings, no conversation memory, no RAG index.

## What FREKCORE exposes today

| Capability | Route | Evidence |
|---|---|---|
| Public-safe identity view (never raw credentials) | `GET /api/v1/identity/me` → `IdentityPublicResponse` | `backend/identity_engine/models.py:73-83` |
| Human-readable audit timeline for an identity | `/api/v1/audit/*` | `backend/audit/routes.py:1-8` |

`IdentityPublicResponse` is explicitly designed as a safe external-facing view (docstring: "vue publique safe d'une identite (jamais de credentials en clair)", `identity_engine/models.py:74`) — this is the correct shape for Laurentia to ground identity facts in, without ever touching WebAuthn credential material.

## What this session added (Bloc 1)

The Registry's `GET /api/v1/registry/namespaces` gives Laurentia a machine-readable list of every FREK object type it may encounter (`frek.artist`, `frek.track`, ..., `frek.event`) with their JSON Schemas — useful as grounding context for a reasoning layer that needs to know "what shape of object is this FREK-ID" before reasoning about it, without hard-coding the type list.

## Explicitly out of scope (belongs in Laurentia's own repository)

- Embeddings, vector stores, RAG retrieval.
- Conversation memory, context windows.
- Reasoning/inference over FREKCORE data — FREKCORE only supplies facts, never conclusions.

## Proposed next step (PROPOSED, NOT IMPLEMENTED)

None specific — Laurentia's memory architecture is out of scope for FREKCORE by design; this document exists so Laurentia's own implementation knows exactly which FREKCORE routes are safe to cite as ground truth.
