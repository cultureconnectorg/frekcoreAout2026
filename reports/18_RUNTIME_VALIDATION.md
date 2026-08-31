# 18 — Runtime Validation (Priorities 7, 8, 9, 10)

All evidence in this report was captured against the **real** `backend/server.py` application (240 routes after this phase's additions), booted with `mongomock_motor.AsyncMongoMockClient` substituted for `motor.motor_asyncio.AsyncIOMotorClient` (see `scripts/run_dev_server_mongomock.py` and `reports/16_INTEGRATION_TEST_BASELINE.md` §1 for exactly why — Docker registry pulls are blocked by network policy in this sandbox, so this is the closest available substitute for a live MongoDB, clearly labeled as such throughout).

## Priority 7 — Observability wiring

**Wired** (additive, `backend/server.py`, +22 lines / -0):
- `RequestIdMiddleware` (`backend/observability/request_id.py`, built Phase 2) — added via `app.add_middleware(RequestIdMiddleware)`, positioned after `CORSMiddleware` so it is outermost.
- `GET /api/metrics` — Prometheus exposition endpoint, `generate_latest(_obs_metrics.registry)`.

**Validated** (real `TestClient` against the real app, `mongomock`-backed):
```
GET /api/v1/health/live
  status: 200
  headers: {..., 'x-request-id': 'b421298a-d7a4-46de-b319-e02fcdaaaf27',
                 'x-correlation-id': 'b421298a-d7a4-46de-b319-e02fcdaaaf27'}

GET /api/metrics
  status: 200
  content-type: text/plain; version=1.0.0; charset=utf-8
  body starts: "# HELP frekcore_http_requests_total Total HTTP requests handled
                # TYPE frekcore_http_requests_total counter
                # HELP frekcore_http_request_duration_seconds HTTP request latency
                ..."
```

**Sensitive-data audit** (per the mission's explicit requirement):
- `backend/observability/request_id.py` reads exactly two headers (`X-Request-ID`, `X-Correlation-ID`) and writes them back — grep confirms no reference to `Authorization`, `X-Admin-Key`, `X-FREK-Session`, or any credential header anywhere in that file.
- `backend/observability/metrics.py`'s label sets are closed enums defined in this codebase (`method`, `path`, `status`, `operation`, `namespace`, `event_type`) — none accept arbitrary user-supplied free text that could carry PII (e.g. no email, no FREK-ID as a label value, which would blow up Prometheus's cardinality anyway and was avoided for that reason too).
- No metric or log line introduced this phase includes a header value, request body, or credential.

**Not wired**: structured JSON logging (the mission's "structured request logs") was not added — `backend/server.py`'s existing `logging.basicConfig` text format was left untouched to keep this phase's `server.py` diff to the one reviewed block above; see `reports/FREKCORE_COMPLETION_BACKLOG.md` P1.

## Priority 8 — Proof Engine runtime classification

Per-level classification, each with file:line evidence (extends `backend/proof_engine/`, built Phase 2, and corrects `ecosystem/registry.json`'s prior overclaim about block-level Ed25519 signing, already fixed in Phase 2):

| Level | Status | Evidence |
|---|---|---|
| 1. Hash/fingerprint | **IMPLEMENTED** | `backend/passport/merkle.py:claim_leaf_hex`, `backend/fk/packager.py:sha256_hex` — real SHA-256 over canonical JSON |
| 2. Local receipt | **IMPLEMENTED** | `backend/notary/chain.py` — hash-chained blocks (`block_hash = sha256(prev_hash + payload_hash)`), persisted to `notary_blocks`. Verified live this phase: `GET /api/v1/notary/chain/status` → `200 OK` against the mongomock-backed server (see server log excerpt in `reports/16_INTEGRATION_TEST_BASELINE.md`) |
| 3. Signed receipt | **IMPLEMENTED**, but not at the block level | `backend/passport/service.py:build_passport` — genuine Ed25519 signature (`backend/passport/keys.py`) over a Merkle root of claims. **Not** the notary block itself (no `signature` field on `BlockResponse`, confirmed by inspection in Phase 2 — `backend/notary/models.py`) |
| 4. Trusted timestamp | **PARTIAL** | `BlockResponse.timestamp` is a local server clock timestamp recorded at block-creation time, not a third-party-attested trusted timestamp (no TSA/RFC 3161 integration found — `grep -rn "rfc3161\|TSA\|timestamp.*authority" backend/` → no matches) |
| 5. OpenTimestamps | **IMPLEMENTED (submission code), runtime-BLOCKED in this sandbox** | `backend/notary/anchor.py` genuinely calls `opentimestamps.calendar.RemoteCalendar` against 5 real calendar servers (`a.pool.opentimestamps.org`, `b.pool.opentimestamps.org`, `alice.btc.calendar.opentimestamps.org`, `bob.btc.calendar.opentimestamps.org`, `finney.calendar.eternitywall.com`). **Live evidence this phase**: every submission attempt failed with `<urlopen error Tunnel connection failed: 403 Forbidden>` — the same network-policy block that stops Docker pulls (`reports/16_INTEGRATION_TEST_BASELINE.md` §1) also blocks outbound calls to these calendar servers from this sandbox. The code path is real; it could not be proven to reach a real calendar server from here. |
| 6. External anchoring (Bitcoin) | **NOT VERIFIED THIS PHASE** | Depends on level 5 completing (an OTS proof reaching Bitcoin-confirmation takes real wall-clock time, typically hours, even outside this sandbox's network restriction) — `BlockResponse.btc_anchored`/`btc_block_height` fields exist and are read/written correctly in code, but no block was observed transitioning to `btc_anchored=true` in this session |

**Compatibility test between `backend/notary` and `ProofProvider`**: `backend/proof_engine/notary_adapter.py` (built Phase 2) is exactly this — a pure function mapping a real `BlockResponse`-shaped dict to a `ProofState`. `backend/tests/test_proof_engine.py` (7 tests, Phase 2) already exercises every branch. This phase adds no new test here because Phase 2's tests already cover the mapping; what's new this phase is the **live confirmation** that `backend/notary`'s real HTTP behavior (OTS submission attempts, the exact log line format) matches what the adapter's docstring assumed.

## Priority 9 — Storage runtime validation

See `backend/storage/emergent_object_storage.py`'s docstring and `reports/FREKCORE_CONTRADICTIONS.md` for the full correction. Summary:

| Question | Answer | Evidence |
|---|---|---|
| What storage is used today? | Emergent's remote Object Storage API (`https://integrations.emergentagent.com/objstore/api/v1/storage`) | `backend/moment/storage.py:23` |
| What is local? | Nothing, in production. `backend/storage/local.py`'s `LocalFilesystemStorageProvider` (Phase 2) is a dev/test convenience only, not used by any real route | — |
| What is external? | The entire real storage path — a third-party-hosted service tied to the Emergent platform, gated by `EMERGENT_LLM_KEY` | `backend/moment/storage.py:36` |
| What requires secrets? | `EMERGENT_LLM_KEY` (env var) | `backend/moment/storage.py:36` |
| What is not implemented? | Any local-disk fallback in the real code path — when the key is absent, uploads are simply disabled (`is_available()` → False), not redirected to disk | `backend/moment/storage.py:60-61` |

**Live evidence this phase**: booting the real server without `EMERGENT_LLM_KEY` set produced the exact log line `EMERGENT_LLM_KEY absent — Object Storage desactive.` (captured in this session's server startup output) — confirms the degraded-mode behavior described above is real, not just read from source.

**Adapter added**: `EmergentObjectStorageProvider` (`backend/storage/emergent_object_storage.py`) — wraps the exact same HTTP calls as `backend/moment/storage.py`, behind the `StorageProvider` interface. 11 unit tests (mocked `requests`, never calls the real service), verifying the wire protocol (URL, headers, JSON shape) matches byte-for-byte. Not wired into `backend/moment/storage.py` or any route — parallel, typed access to the same real service.

## Priority 10 — SDK contract validation against the running service

`sdk/python/frekcore_sdk`'s existing test suite (Phase 2, 5 tests) already validated the Registry API against a real `registry_router`. This phase re-ran it against the **full real application** (`server.py`, not an isolated router) to confirm no route conflict or middleware interaction broke it:

```
$ PYTHONPATH=backend python3 -m pytest sdk/python/tests -q
5 passed
```

Additionally, with the mongomock-backed live server running, the SDK's underlying HTTP calls were exercised manually against `http://localhost:8001` (not just the in-process `TestClient` path) to confirm the contract holds over a real socket, not only ASGI-transport:
```
GET  /api/v1/registry/namespaces   -> 200, 8 namespaces (matches SDK's RegistryNamespace shape)
POST /api/v1/registry/validate     -> 200, ValidationResult shape matches
```
No SDK method was added or changed. Scope remains Registry-API-only per Phase 2's decision (`reports/12_PHASE2_IMPLEMENTATION.md` Priority 7) — this phase did not find new evidence strong enough to extend it (see `reports/16_INTEGRATION_TEST_BASELINE.md` for the Identity Engine's real pass/fail state, which would be the natural next candidate once fully green).

**TypeScript SDK** (`sdk/typescript`, not covered by Phase 2's SDK validation): `npm install` succeeds (3 packages, no registry access issue — this is npm's registry, unrelated to the Docker-pull network-policy block), `npm run typecheck` clean, `npm test` → **3 passed, 0 failed** (mocked-fetch unit tests). Additionally exercised live against the real mongomock-backed socket this phase (not just mocked fetch):
```
$ node -e "new FrekcoreRegistryClient('http://localhost:8001').listNamespaces()"
namespaces: 8  [{"namespace":"frek.album","version":"1.0.0",...}, ...]
$ node -e "...listVersions()"
versions: {"versions":["v1"],"default":"v1"}
```
Same conclusion as the Python SDK: contract holds over a real socket, scope remains Registry-API-only, no method added.
