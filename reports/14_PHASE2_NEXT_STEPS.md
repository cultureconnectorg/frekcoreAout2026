# 14 — Phase 2 Next Steps

Recommended order for Phase 3, ranked by risk/dependency (same method as Phase 1's ranking, re-run against Phase 2's actual output rather than Phase 1's predictions).

## 1. Resolve the two `backend/requirements.txt` install blockers (P0)

This is now the single highest-leverage fix available: it currently prevents (a) a fresh `pip install -r backend/requirements.txt` on any machine, (b) `docker build` on a public CI runner, and (c) running the 335-test integration suite anywhere this session could reach. Concretely, a human needs to decide between:
- Removing/making-lazy the `emergentintegrations` import in `backend/services/webhook.py:8` (pattern already exists in this codebase: `backend/frek_v1/stages.py:10-14`'s `try/except` fallback for `notary.service.notarize_event`), **or** providing a private package index as a CI/Docker-build secret.
- Bumping `cryptography` to `>=49.0.0` (satisfying `webauthn==3.0.0`) and re-running the full test suite against that bump — cannot be done blind; needs the integration suite actually running somewhere (see #2).

## 2. Get the 335 integration tests running somewhere (P0, blocks almost everything else)

Once #1 is resolved, stand up `docker-compose.yml`'s `mongo` service + a live `uvicorn server:app` and run `pytest -m integration`. Every subsequent priority below benefits from being verifiable against real behavior instead of unit-level evidence alone.

## 3. Wire `backend/permissions/` into `frek_v1/auth.py` (P1)

The model is done and tested (`reports/12_PHASE2_IMPLEMENTATION.md` Priority 3). The safe path: add `permissions.decide()` as an **additional, opt-in** check behind a new `require_role(...)` dependency, additive alongside the existing `require_permission(...)`, migrate routes one at a time (starting with the newest/least-depended-on), and only remove the old mechanism once every route has a verified equivalent role grant. Do this only once #2 is available to catch regressions.

## 4. Wire `backend/audit_trail/` as the sink for `permissions.decide()` output (P1)

Trivial once #3 exists — `permissions.audit_integration.decision_to_audit_event()` already produces the right shape; only a MongoDB-backed `AuditRecorder` implementation (append-only collection, `insert_one` only, no update/delete route ever exposed) needs to be added.

## 5. Wire real producers for the remaining 5 events (P1/P2, per event)

In order of how contained the change is:
1. `identity.revoked` — needs a revoke endpoint on `identity_engine` first (does not exist yet, see `02_GAP_ANALYSIS.md` Bloc 3).
2. `identity.updated` — same module, similarly contained once a real update endpoint exists.
3. `object.created` — `backend/fk/routes.py:POST /fk/create`, not touched this phase; needs its own careful read before adding a publish call (larger file, more side effects than `identity_engine/routes.py`).
4. `proof.generated` — `backend/notary/service.py:notarize_event`, called from many places; higher blast radius, do last among these four.
5. `certificate.issued` — blocked entirely on Bloc 5 (Certificate Engine) not existing yet; not a wiring task, a build task.

## 6. Wire `backend/observability/RequestIdMiddleware` into `server.py` (P2, low risk)

Literally `app.add_middleware(RequestIdMiddleware)`. Low risk, high value (every subsequent debugging session benefits). Do this early in Phase 3 regardless of what else is prioritized — it was only deferred this phase to keep the `server.py` diff to the one reviewed Priority-6 change.

## 7. Extend the SDKs once more API families are proven stable (P2)

Once #2 makes it possible to verify a family end-to-end, extend `sdk/python`/`sdk/typescript` to cover it — Identity Engine's read endpoints (`GET /identity/me`, `GET /identity/{id}`) are the natural next candidate (already documented as safe/public in `docs/interfaces/LAURENTIA.md` and `CVLN_BRAIN.md`).

## 8. Dependency CVE triage (P2)

Work through the table in `reports/11_SECURITY_PHASE2.md` §3 — each has a fixed version available; the blocker is only "needs a regression pass" (see #2).

## 9. Registry instance store (P3, carried over from Phase 1's `08_NEXT_INTEGRATION.md`)

Still not built: `backend/registry/` remains schema-only. Every `docs/interfaces/*.md`'s "PROPOSED, NOT IMPLEMENTED" resolver endpoint depends on this existing first.

## What NOT to do next (explicit, matching this phase's non-goals)

- Do not attempt a DDD reorganization of the 30-module backend.
- Do not build Wallet/KORA/Academy/LabelOS business logic inside FREKCORE.
- Do not add Kafka/RabbitMQ — `backend/eventbus/InProcessEventBus` has no evidenced need for a distributed broker yet (single-process monolith, confirmed in `03_ARCHITECTURE_MAP.md`).
- Do not add an S3/Cloudinary `StorageProvider` implementation without a real, named consumer for it.
