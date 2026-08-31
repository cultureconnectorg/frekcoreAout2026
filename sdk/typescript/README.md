# FREKCORE TypeScript SDK (Phase 2 — Priority 7)

**Scope**: wraps only `/api/v1/registry/*` (the FREK Registry API). See
`src/registryClient.ts`'s header comment for why every other FREKCORE API
family is intentionally not wrapped yet, and
`reports/12_PHASE2_IMPLEMENTATION.md` for the reasoning. Same scope, same
rationale as `sdk/python/frekcore_sdk` — kept in sync by hand (see
`reports/13_PHASE2_GAP_ANALYSIS.md` for this being a named gap: no
generated-from-OpenAPI tooling wires the two SDKs together yet).

## Install & build

```bash
cd sdk/typescript
npm install
npm run build       # emits dist/
npm run typecheck   # tsc --noEmit
npm test            # compiles test/ and runs it with node --test
```

## Usage

```ts
import { FrekcoreRegistryClient } from "@frekcore/registry-sdk";

const client = new FrekcoreRegistryClient("https://frekcore.example.com");
const namespaces = await client.listNamespaces();
const result = await client.validate("frek.artist", { frek_id: "...", entity_type: "frek.artist" /* ... */ });

// Instance store (P1, 2026-08-31) — needs the same authority the server
// requires: an OAuth2 bearerToken (registry:write) or an identity_engine
// holder sessionToken.
const artist = await client.createObject("frek.artist", { display_name: "Luciole" }, { bearerToken: "..." });
const same = await client.getObject("frek.artist", artist.frek_id);
const page = await client.listObjects("frek.artist", { status: "draft" });
```

## Tests

`test/registryClient.test.ts` uses a mocked `fetch` (no live FREKCORE server
available in this sandbox — see `reports/09_PHASE2_BASELINE.md`), asserting
against real response shapes captured from the actual server (see
`sdk/python/tests/test_registry_client.py` for the equivalent test suite
running against the real FastAPI router in-process). 7/7 passing as of this
writing.
