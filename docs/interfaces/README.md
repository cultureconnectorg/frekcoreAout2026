# CVLN Integration Interfaces (Phase 15 / Bloc 14)

**Doctrine (explicit, per the mission brief's correction):** FREKCORE does not contain Wallet ledger logic, KORA royalty/streaming logic, or Academy course/certification-issuance logic. It exposes only **contracts** — API responses, JSON Schemas, and event definitions — that the systems below may consume. Nothing in this directory adds business logic for those systems inside this repository.

Each file documents, for one CVLN system:

1. **What FREKCORE already exposes today** that the system can call, with exact routes and evidence (file:line).
2. **What this session added** (FREK Registry namespaces, Bloc 1) that is relevant to that system.
3. **What is explicitly out of scope** — logic that belongs in the other system's own repository, never in FREKCORE.

| File | CVLN System |
|---|---|
| `CVLN_WALLET.md` | CVLN Wallet |
| `KORA.md` | KORA (DSP / catalogue / royalties) |
| `CVLN_ACADEMY.md` | CVLN Academy |
| `LABELOS.md` | LabelOS |
| `LAURENTIA.md` | Laurentia (memory/RAG) |
| `CVLN_BRAIN.md` | CVLN Brain |
| `AGENT_FACTORY.md` | CVLN Agent Factory |

These are **documentation-only** deliverables — no new authentication, endpoint, or database table was created for any of the 7 systems. Where a resolver route is proposed but does not exist yet, it is explicitly marked **PROPOSED, NOT IMPLEMENTED**.
