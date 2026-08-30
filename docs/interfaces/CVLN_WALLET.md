# Interface: CVLN Wallet

**Role of FREKCORE**: Identity + Signature + Wallet-Owner attestation only. No ledger, no balance, no transaction logic.

## What FREKCORE exposes today

| Capability | Route | Evidence |
|---|---|---|
| Resolve the identity that owns a wallet | `GET /api/v1/identity/me` (session) | `backend/identity_engine/routes.py`, `identity_engine/models.py:73-83` (`IdentityPublicResponse`) |
| Prove the identity's public key / signature capability | `GET /api/v1/fk/pubkey` (Ed25519 public key) | `memory/INVENTORY.md:67` |
| Cryptographic proof of any wallet-linkage event, once emitted | `POST /api/v1/notary/notarize` | `backend/notary/routes.py` |

## What this session added (Bloc 1)

`frek.wallet` namespace (`backend/registry/schemas/v1/frek.wallet.schema.json`): a schema for the **identity ↔ wallet linkage record** only — `holder_id` (FREK-ID), `wallet_provider`, `external_wallet_ref` (an opaque reference *owned by* CVLN Wallet), `linked_at`. It has no `balance`, `currency amount`, or `transaction` field by design.

```json
{
  "frek_id": "id-...",
  "entity_type": "frek.wallet",
  "status": "active",
  "created_at": "2026-08-30T00:00:00Z",
  "holder_id": "id-abcdef012345-ab12",
  "wallet_provider": "cvln-wallet",
  "external_wallet_ref": "opaque-ref-owned-by-wallet-service",
  "linked_at": "2026-08-30T00:00:00Z"
}
```

Validate a candidate linkage record via `POST /api/v1/registry/validate {"namespace": "frek.wallet", "payload": {...}}` before persisting it in CVLN Wallet's own database.

## Explicitly out of scope (belongs in CVLN Wallet's own repository)

- Ledger, balances, JCC token accounting.
- Apple/Google Wallet pass generation.
- Fintech compliance (KYC/AML) workflows.
- The `wallet.linked` event (catalogued as `implemented: false` in `backend/registry/events/event_registry.json`) is **not emitted** by any FREKCORE code path today — CVLN Wallet cannot currently subscribe to it because no producer exists. See `reports/02_GAP_ANALYSIS.md` Bloc 7.

## Proposed next step (PROPOSED, NOT IMPLEMENTED)

A `POST /api/v1/identity/{id}/wallet-link` endpoint that (a) validates the payload against `frek.wallet`, (b) calls `notary.notarize_event(...)` to produce a signed receipt, and (c) emits `wallet.linked` per the envelope in `event_registry.json`. Not built this session — it would be the first real producer for the Event Registry catalog.
