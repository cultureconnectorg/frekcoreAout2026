# FREKCORE TypeScript SDK (Phase 2/3 — Priority 7)

**Scope**: two clients, each wrapping one API family with strong,
reproducible evidence it's stable enough to commit to as a client
contract — same rationale as `sdk/python/frekcore_sdk`, kept in sync by
hand (see `reports/13_PHASE2_GAP_ANALYSIS.md` for this being a named gap:
no generated-from-OpenAPI tooling wires the two SDKs together yet).

- `FrekcoreRegistryClient` (`src/registryClient.ts`) — the full FREK
  Registry API (`/api/v1/registry/*`).
- `FrekcoreIdentityClient` (`src/identityClient.ts`) — `identity_engine`'s
  public-**read** surface only (`/api/v1/identity/*`). See that file's
  header comment for exactly why the write/lifecycle surface isn't
  wrapped.

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
import { FrekcoreRegistryClient, FrekcoreIdentityClient } from "@frekcore/registry-sdk";

const client = new FrekcoreRegistryClient("https://frekcore.example.com");
const namespaces = await client.listNamespaces();
const result = await client.validate("frek.artist", { frek_id: "...", entity_type: "frek.artist" /* ... */ });

// Instance store (P1, 2026-08-31) — needs the same authority the server
// requires: an OAuth2 bearerToken (registry:write) or an identity_engine
// holder sessionToken.
const artist = await client.createObject("frek.artist", { display_name: "Luciole" }, { bearerToken: "..." });
const same = await client.getObject("frek.artist", artist.frek_id);
const page = await client.listObjects("frek.artist", { status: "draft" });

// Identity Engine — public read surface (P2, 2026-08-31)
const identityClient = new FrekcoreIdentityClient("https://frekcore.example.com");
const publicView = await identityClient.getIdentity("id-...");
const me = await identityClient.getMe("holder-session-token");
const objects = await identityClient.getLinkedObjects(me.frek_id, "holder-session-token");
const results = await identityClient.searchIdentities("admin-key", { displayName: "Luciole" });
```

## Tests

`test/registryClient.test.ts` and `test/identityClient.test.ts` use a
mocked `fetch` (no live FREKCORE server available in this sandbox — see
`reports/09_PHASE2_BASELINE.md`), asserting against real response shapes
captured from the actual server (see `sdk/python/tests/` for the
equivalent test suites running against the real FastAPI routers
in-process). 13/13 passing as of this writing (7 Registry + 6 Identity).
