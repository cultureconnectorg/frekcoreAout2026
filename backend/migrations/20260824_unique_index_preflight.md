# 20260824 — Staff Scanner unique-index preflight

## Why

`scans.client_uuid` and `transactions.client_uuid` are idempotency constraints. Startup
previously attempted to repair incompatible indexes by dropping them, which could temporarily
remove uniqueness protection and did not inspect duplicate data first.

## Procedure

1. Back up the target database.
2. Run `python backend/migrations/20260824_unique_index_preflight.py` with `MONGO_URL` and
   `DB_NAME`. Exit code 0 means no duplicate groups; 1 means duplicates were reported.
3. If duplicates exist, stop. Decide a business-specific reconciliation rule and record it in
   a new reviewed migration. This migration must not delete data implicitly.
4. Review the existing index definition. Apply any index replacement in a scheduled migration
   after the preflight is clean; startup will now refuse unsafe replacement.
5. Validate scan/transaction counts, idempotency replay behavior, and index definitions.

## Rollback

This preflight is read-only and has no rollback. Any later index migration must include its
own rollback plan and must not drop a unique index before a replacement is ready.
