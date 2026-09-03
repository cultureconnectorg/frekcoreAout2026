# FREKCORE STATE_8 — Regression / Evidence / Migration Validation Plan

**Founder authorization**: `FREKCORE_EXECUTION_PROTOCOL_V1`, `CURRENT_STATE=STATE_8_REGRESSION_EVIDENCE_MIGRATION_VALIDATION`, `BASELINE_HEAD=fc37516` (STATE_7, ACCEPTED). Date: 2026-09-03.

## 1. What this state is, and is not

STATE_8 is **validation**, not redesign. It does not touch D1-D6 behavior, does not
retrofit API/SDK contracts beyond a bounded, evidence-driven correction, does not
begin Production Readiness, and does not wire any CVLN system. Its one question:

> Do the modules preserve their invariants when combined?

Every module (D1-D6, Identity, Permissions, Registry, Offline Transport, Notary,
Legacy Compatibility, the STATE_7 contracts) was independently implemented and
regression-tested across D1-D6/STATE_6/STATE_7. STATE_8 re-runs that full
regression suite as its baseline, then adds targeted, genuinely new cross-module
tests for the specific gaps STATE_7 itself disclosed as PARTIAL or untested:
delegated-authority full-chain validation, persistence/restart behavior, index
idempotency, DB/EventBus failure injection, and a set of direct, structural
re-checks of the mission's named invariants.

## 2. Method

1. **Full regression** — `pytest -v` (unit tier, the project's default), backend
   coverage on the CI blocking-scope modules, both SDK suites, the OpenAPI golden
   snapshot test, run exactly as CI runs them.
2. **Genuinely new tests only where a real gap exists** — audited each validation
   domain in the mission against the existing 62-file backend test suite before
   writing anything; where a domain (e.g. offline-transport revocation/replay/
   conflict, D1 determinism/non-finite-input safety, identity reconciliation
   idempotency) already has direct, passing tests, this state cites them as
   regression evidence rather than duplicating them (`docs/validation/
   FREKCORE_STATE8_VALIDATION_RESULTS.md` records exactly which file covers
   which requirement).
3. **Real infrastructure attempted, not assumed** — real MongoDB and real
   OpenTimestamps/Bitcoin-anchor validation were re-attempted this state (not
   carried forward as "still blocked" without re-checking); both remain
   environment-blocked, with the exact reproducing command recorded.
4. **Bounded, disclosed corrections only** — one real doc/code inconsistency was
   found (a `DelegationGrant` docstring overclaiming what `delegation_permits()`
   alone checks) and fixed by adding the composed check
   `permissions.delegation.delegation_authority_chain_valid()` the docstring was
   describing — this is the one "demonstrated defect" bounded correction this
   state makes to a STATE_7 contract, not a redesign.
5. **Test-level fault injection only** — `monkeypatch`-based DB/EventBus failure
   injection inside existing isolated TestClient+mongomock apps; no chaos
   infrastructure was built.

## 3. Validation domains and where each is addressed

| Domain | Primary evidence |
|---|---|
| Identity / Authority / Permissions / Service Identity / Delegated Authority | `tests/test_permissions.py` (24 -> 31 tests this state), `tests/test_identity_*.py` |
| Registry / FK Object / Content Binding | `tests/test_registry*.py`, `tests/test_content_binding*.py`, `tests/test_fk*.py` |
| Creative Lifecycle / Relationship Graph | `tests/test_creative_lifecycle_unit.py`, `tests/test_relationship_graph_unit.py` |
| Claims / Evidence / Proof / Verification | `tests/test_evidence_semantics.py`, `tests/test_proof_engine.py`, `tests/test_state8_validation.py::TestCrossModuleInvariants` |
| Credentials / Notary / FREK Chain | `tests/test_notary*.py`, `tests/test_did_vc.py` |
| Offline Transport / FAP | `tests/test_offline_transport_unit.py`, `tests/test_offline_verifier.py` |
| Technical Evidence Report | `tests/test_technical_evidence_report_unit.py` |
| EventBus / Audit | `tests/test_eventbus.py`, `tests/test_audit_trail*.py`, `tests/test_fk_object_created_event.py` |
| Legacy Compatibility | `tests/test_legacy_compatibility.py`, `docs/validation/FREKCORE_MIGRATION_VALIDATION.md` |
| API Contracts / Python SDK / TypeScript SDK | `tests/test_api_contract.py`, `sdk/python/tests/`, `sdk/typescript/test/` |
| Persistence / Migration / Aliasing / Errors / Idempotency / Revocation / Privacy | `tests/test_state8_validation.py` (new this state), `tests/test_identity_reconcile_unit.py` |

Full per-requirement evidence classification (DOCUMENTED / IMPLEMENTED /
UNIT_VERIFIED / INTEGRATION_VERIFIED / REAL_INFRA_VERIFIED / BLOCKED /
NOT_VERIFIED): `docs/validation/FREKCORE_STATE8_VALIDATION_RESULTS.md`.

## 4. Explicit non-goals (per authorization)

`EXECUTE_STATE_9=FALSE`, `FINAL_FREEZE=FALSE`, `PRODUCTION_READINESS=FALSE`,
`RED_TEAM=FALSE`, `BLUE_TEAM=FALSE`, `PURPLE_TEAM=FALSE`, `WIRE_CVLN=FALSE`,
`DEPLOY=FALSE`, `MERGE_PR=FALSE`, `GENERAL_REAUDIT=FALSE`,
`AUTO_TRANSITION=FALSE`, `DELETE_LEGACY_ROUTES=FALSE`,
`UPGRADE_D1_SCIENTIFIC_STATUS_WITHOUT_EVIDENCE=FALSE`.
