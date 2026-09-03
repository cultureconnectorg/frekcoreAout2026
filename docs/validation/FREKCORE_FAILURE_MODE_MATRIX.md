# FREKCORE STATE_8 — Failure Mode Matrix

Test-level fault injection only (`monkeypatch` inside isolated TestClient +
mongomock apps) — no chaos infrastructure was built, per the mission's own
instruction. Every row below is a real, executed test, not a hypothetical.

| # | Failure | Injection method | Where | Observed behavior | Verdict |
|---|---|---|---|---|---|
| 1 | DB write failure (`insert_one` raises) | Patch `mongomock_motor.AsyncMongoMockCollection.insert_one`, scoped to one collection name | content_binding create | Never returns a false 200; error surfaces without a traceback or file path in the body; not yet a canonical error code (bare 500) | Safe, disclosed compatibility debt |
| 2 | EventBus `publish()` raises | Replace `fk.routes._event_bus` with an exploding stub | fk object creation | Creation still succeeds; publish failure never breaks the triggering request (existing, pre-STATE_8 test, re-run green) | Safe, by design |
| 3 | EventBus subscriber raises | Subscribe a raising callable | `InProcessEventBus.publish()` | Caught and logged inside `publish()`, other subscribers still run, publisher unaffected (existing, pre-STATE_8 test, re-run green) | Safe, by design |
| 4 | Invalid signature on offline envelope | Tamper envelope bytes after signing | offline_transport receive | Rejected at receive, tampering detected (`test_receive_detects_tampering`, pre-existing) | Safe |
| 5 | Expired/stale authority at sync time | Device revoked between receive and sync | offline_transport sync | Reconciliation blocked at sync, not silently accepted (`TestRevocation`, pre-existing) | Safe |
| 6 | Permission denial | `decide()` with no covering RoleGrant | permissions | Clean `Decision(allowed=False, reason=...)`, no exception | Safe |
| 7 | Revoked authority (delegated) | Delegator's RoleGrant removed from `Subject.roles` after grant creation | `delegation_authority_chain_valid()` | Denied with an explicit reason distinguishing it from a grant-record-level revocation (new, STATE_8) | Safe |
| 8 | Missing canonical reference | Unknown `content_binding`/`relationship`/`creative_lifecycle_event` id referenced from offline envelope | offline_transport | 404, not a crash (`test_unknown_content_binding_is_404` and siblings, pre-existing) | Safe |
| 9 | Duplicate idempotency key, same payload | Resubmit identical audio | content_binding | Returns existing record (`deduplicated: true`), no duplicate row | Safe |
| 10 | Conflicting idempotency key, different payload | Two envelopes at the same `(issuer_id, sequence)` | offline_transport | Flagged as conflict, not silently overwritten (`TestConflict`, pre-existing) | Safe |
| 11 | Bad pagination token — offset far beyond data | `offset=999999` | registry list | Empty page, `count: 0`, no error (new, STATE_8) | Safe |
| 12 | Bad pagination token — negative limit | `limit=-5` | registry list | Clamped to the policy floor (>=1), 200 OK (new, STATE_8) | Safe |
| 13 | Bad pagination token — non-numeric | `offset=not-a-number` | registry list | Clean 422 from FastAPI's own type validation, no 500 (new, STATE_8) | Safe |
| 14 | Unsupported API version | `GET /api/v2/...` | any canonical router | Clean 404 — no `/api/v2` router is mounted anywhere in `server.py` (new, STATE_8) | Safe, disclosed compatibility debt (not yet a canonical `UNSUPPORTED_VERSION` error code) |
| 15 | Index re-creation | `ensure_indexes()` called twice against the same db | content_binding startup | No exception; the unique index it creates still rejects a real duplicate afterward (new, STATE_8) | Safe |
| 16 | mongomock instance discontinuity ("restart" without real Mongo) | Fresh `AsyncMongoMockClient()` at the same connection string | n/a (diagnostic, not a route test) | Returns `None` for previously-written data — confirms mongomock does **not** simulate real-MongoDB persistence across a restart | **Not a pass/fail** — a documented limitation of the test substrate, see `FREKCORE_STATE8_VALIDATION_RESULTS.md` §5 |
| 17 | Real MongoDB unreachable | `docker pull mongo:7` / `docker info` | sandbox environment | `Cannot connect to the Docker daemon at unix:///var/run/docker.sock` | BLOCKED (environment, reproduced, documented) |
| 18 | Real OpenTimestamps calendar unreachable | `curl` to `alice.btc.calendar.opentimestamps.org` | sandbox environment | Connection failure (curl exit 56, HTTP code 000) | BLOCKED (environment, reproduced, documented) |

## Notes

- Rows 1-15 are genuine test-level fault injections against real route code
  (isolated FastAPI app + TestClient + mongomock_motor); none required
  changing production code to make pass except where noted as "disclosed
  compatibility debt" (rows 1, 14) — those are pre-existing, honestly
  reported gaps, not newly introduced by this state, and are not fixed here
  per `REWRITE_D1_D6_ARCHITECTURE=FALSE`/bounded-correction-only scope.
- Rows 16-18 are environment/substrate limitations, not application defects —
  recorded so they are never mistaken for "passed" or silently dropped.
- No row above required or used a mocked equivalent presented as real
  infrastructure verification.
