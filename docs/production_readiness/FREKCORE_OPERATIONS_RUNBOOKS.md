# FREKCORE Operations: Monitoring, Alerting, Backup/DR, Capacity, Incident Runbooks

**Status: PLANNING ARTIFACT.** No code changed, no monitoring/alerting
service provisioned by this session.

**Note on process-manager references**: some existing scripts in this repo
(`scripts/chaos/test_mongo_cut.sh`'s `sudo supervisorctl stop mongodb`,
`scripts/backup_scheduler.py`'s docstring) assume `supervisor`, matching this
project's original container-platform deployment target. For the founder's
new self-hosted-PC + Cloudflare Tunnel target, systemd (or Docker Compose's
own `restart:` policy) is the more natural fit — see
`FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §2. The chaos scripts' *logic* (stop
the dependency, probe the API, measure recovery) stays valid regardless of
which process manager issues the stop/start commands; only that one command
needs adjusting when the target changes (e.g. `sudo systemctl stop mongod`
or `docker compose stop mongo`, depending on how Mongo itself is run — moot
once fully on Atlas, since Atlas isn't something the local machine stops).

## 1. Monitoring, alerting, logs

**What already exists (verified, not proposed)**:
- `GET /health/live` — liveness only.
- `GET /health/ready` — Mongo ping.
- `GET /health/deep` — Mongo (ping + counts), Ed25519 key (fingerprint +
  file-permission check), disk (free space, floor 500MB), memory (peak
  RSS), notary-chain integrity (last-3-blocks hash linkage spot-check),
  last-backup marker. Always HTTP 200 with `status: healthy|degraded` in
  the body — an external monitor should read that field, not just the
  status code (this is intentional and documented in the route's own
  docstring, not an oversight to "fix").
- `backend/observability/metrics.py` — real Prometheus counters/histograms,
  on their own `CollectorRegistry`, exposed at `GET /api/metrics`
  (`server.py:572`) in real Prometheus exposition format — verified via
  direct code read, not assumed. **That route has no auth check today** —
  it is public. Treat this as the real gap here, not "mount `/metrics`"
  (already done).
- `security_events` (Mongo collection) — anomalies, chain-watchdog
  criticals.
- `audit_trail` — append-only business events (STATE_7/8-validated).
- Python `logging` throughout — visible via `journalctl` (systemd path) or
  `docker compose logs` (Docker path); no external shipping configured.

**To close before/around launch (bounded, additive work)**:

1. Gate `GET /api/metrics` (`server.py:572`, already implemented and
   already returning real data) behind the **ADMIN** route class
   (architecture doc §4) — add an `X-Admin-Key` check matching this
   codebase's own existing `_require_admin` pattern (`health/routes.py`)
   and/or restrict it at the Cloudflare layer, before the tunnel goes
   live. The metric set itself (7 counters/histograms covering HTTP
   volume/latency/errors and 4 named capability counters) is already
   sufficient for launch — this is an access-control fix, not a
   build-from-scratch task.
2. External uptime/alerting (FOUNDER-OPERATED choice of tool, e.g.
   UptimeRobot, Healthchecks.io, Cronitor, or a self-hosted Prometheus +
   Alertmanager once `/metrics` is mounted): point it at
   `https://api.frekcore.example/health/deep` (through the tunnel, so the
   check itself validates the whole path end-to-end, not just localhost),
   alert when `status != "healthy"` OR the endpoint doesn't respond at
   all. This single check already covers "FREKCORE UP/DOWN", "Mongo
   inaccessible", "disque plein" (floor already enforced server-side),
   and "notary chain corrupted" in one signal — exactly the founder's own
   ask, using code that already exists.
3. `chain_watchdog.py` already writes `security_events` at
   `severity=critical` on tamper detection — wire a second, simple
   external check (or extend the watchdog itself) to also hit a
   founder-chosen alert webhook (email/SMS/Slack/Discord — whichever the
   founder already has) when it detects `valid=false`, rather than relying
   solely on someone noticing the log line.
4. Log shipping (optional at launch, worth doing once there's real
   traffic): forward `journalctl`/`docker compose logs` output to an
   external log service (FOUNDER-OPERATED choice) — no FREKCORE code
   change needed, this is purely an OS/container log-driver configuration.

## 2. Backup scheduler as a real, supervised service

`scripts/backup_scheduler.py` exists and is correct in design (daily
trigger, GPG passphrase from a root-only file, calls the real
`backup_frekcore.sh`) but has no `.service`/`.conf` file checked into this
repo to actually run it continuously. Minimal systemd unit to close this:

```ini
# /etc/systemd/system/frekcore-backup.service
[Unit]
Description=FREKCORE backup scheduler
After=network-online.target

[Service]
Type=simple
User=frekcore
EnvironmentFile=/opt/frekcore/backend/.env
ExecStart=/opt/frekcore/.venv/bin/python3 /opt/frekcore/scripts/backup_scheduler.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now frekcore-backup.service
```

Verify it actually ran: `GET /admin/backup/status` (admin-key-gated,
already exists) — shows `last` backup timestamp and the archive list.

## 3. Backup / disaster recovery: RPO, RTO, and rebuild procedure

**RPO (Recovery Point Objective)** — how much data can be lost:
- With the scheduler above running daily at 03:00 UTC, worst-case data loss
  on total server loss is **just under 24 hours** of writes to MongoDB
  Atlas plus the Ed25519 key file (which changes only on rotation, not per
  write — so effectively zero loss for the key itself between backups,
  since it's static). If this RPO is too coarse once real usage starts,
  reduce `FREK_BACKUP_HOUR_UTC`/add a second daily run, or (better, and
  the actual right long-term answer) rely on **Atlas's own continuous
  backup / point-in-time recovery** if the founder's Atlas tier supports it
  — that gives near-zero RPO for the database itself independent of this
  repo's own daily-dump cadence, which then exists mainly to also capture
  the Ed25519 key and `.env` together in one restorable, encrypted unit.
- Target: state explicitly once real users exist (e.g. "RPO <= 24h" is the
  current honest ceiling; tighten via Atlas continuous backup before that
  matters).

**RTO (Recovery Time Objective)** — how long to get back up:
- Rebuild-from-scratch procedure (tested manually, not yet automated end to
  end):
  1. Provision a new machine (or repair the existing one).
  2. Install Docker or the systemd/venv path (architecture doc §2).
  3. Restore the latest backup archive:
     `scripts/restore_test.sh <archive>` first, against a **temporary**
     database, to confirm the archive is actually valid before touching
     anything real (this script already exists and already does exactly
     this, non-destructively).
  4. Once confirmed valid, restore for real: `mongorestore` the dump into
     the real Atlas cluster/database, copy `.passport_key.pem` back into
     place with `chmod 600`, restore `.env`.
  5. Re-run `cloudflared tunnel create`/`route dns` if the tunnel
     credentials were lost too (they should also be in the encrypted
     backup archive per §1's `.env` capture — confirm `cloudflared`'s own
     credentials file path is added to `backup_frekcore.sh`'s file list if
     not already covered; verify before relying on it).
  6. Bring the service up, confirm `/health/deep` reports `healthy`.
- Target: state explicitly once measured — a first real rebuild drill (not
  performed by this session; needs the actual host) is the way to get a
  real RTO number rather than an estimate.

## 4. Capacity: disk, logs, offline queue

- `/health/deep`'s disk check already alerts below 500MB free — a floor,
  not a full capacity plan.
- Log rotation: if using systemd, `journald` already rotates by default
  (`journalctl --vacuum-size=...` to bound it explicitly); if using Docker,
  set a `logging:` driver with `max-size`/`max-file` in
  `docker-compose.yml` (not set today — add
  `logging: {driver: "json-file", options: {max-size: "10m", max-file: "5"}}`
  under the `backend` service).
- Offline-transport queue (`transport_envelopes`): grows with
  received-but-not-yet-synced envelopes. No automatic pruning exists today
  (correct — synced/reconciled history should not be silently deleted,
  matching this codebase's append-only discipline elsewhere) — capacity
  planning here means monitoring `db.transport_envelopes.count_documents
  ({"sync_status": "pending"})` growth over time via a future `/metrics`
  counter (§1) rather than assuming it self-bounds.
- Backup archive retention: `backup_frekcore.sh` already prunes by
  `BACKUP_RETENTION_DAYS` (default 30) — real, existing, not a gap.

## 5. Clock / NTP

Covered in the architecture doc §1 (FOUNDER-OPERATED: enable
`systemd-timesyncd`/`chrony`). Verification command:
`timedatectl status | grep "synchronized"`. Every signature, proof
timestamp, credential expiry, and delegation validity window in this
codebase assumes this holds (`FREKCORE_VERSIONING_POLICY.md` §5) — this is
a real, load-bearing dependency, not a nice-to-have.

## 6. Missing chaos test: brutal power-off mid-write

`scripts/chaos/test_mongo_cut.sh` and `test_ots_cut.sh` cover *dependency*
loss cleanly. Neither simulates the FREKCORE **process itself** being
SIGKILL'd or the host losing power mid-request. A bounded addition (not
implemented by this document, sized for whoever picks this up):

```bash
# scripts/chaos/test_process_kill.sh (proposed, not yet written)
# Fires N concurrent writes, SIGKILLs the FREKCORE process partway through,
# restarts it, and confirms:
#  - no request appears to have "partially" succeeded (each write's own
#    Mongo insert is atomic per-document, so this should already hold by
#    construction -- this test would PROVE it, not assume it)
#  - the notary chain's integrity check still passes after restart
#  - the offline queue (if any envelope was mid-flight) reconciles
#    correctly rather than being lost or duplicated
```

This directly extends the existing `scripts/chaos/` pattern and would give
real evidence for the founder's "coupure brutale" item beyond the
by-construction argument already made in
`FREKCORE_PRODUCTION_READINESS_PLAN.md` §8.

## 7. Incident runbooks

### Mongo (Atlas) is unreachable

1. Confirm via `GET /health/deep` — `checks.mongo.ok: false`.
2. Check Atlas's own status page and the project's Network Access list
   first (the most common cause — see
   `FREKCORE_READINESS_ROADMAP.md` §2 for this session's own live example
   of exactly this failure mode).
3. FREKCORE does not crash on Mongo loss — routes that need it return
   real errors (`/health/ready` returns 503; individual routes surface
   their own DB errors) rather than hanging or corrupting state; this is
   already exercised by `scripts/chaos/test_mongo_cut.sh`.
4. Once Atlas is reachable again, no manual FREKCORE restart should be
   needed — `motor`'s client retries connections automatically. If
   `/health/deep` still reports `mongo.ok: false` a full minute after Atlas
   itself is confirmed healthy, restart the FREKCORE service
   (`systemctl restart frekcore` / `docker compose restart backend`).

### An Ed25519 key (or any secret) leaks

1. Do not wait for a scheduled rotation — this is an emergency action.
2. Revoke immediately per `FREKCORE_SECRETS_KEYS_AUTH_PLAN.md` §2's planned
   procedure (not yet implemented — until it is, the only available action
   is to generate a brand-new key at a new `FREK_PASSPORT_KEY_PATH`,
   restart the service, and treat every signature from the old key as
   suspect going forward; this is the honest current limitation, not
   glossed over).
3. Rotate every other secret in `.env` that could plausibly have leaked
   alongside it (if the leak vector was "whole `.env` file exposed",
   rotate all of them, not just the one suspected).
4. Post-incident: add whatever monitoring would have caught this sooner
   (e.g., a canary check on `.env` file permissions/exposure) to this
   runbook.

### FREKCORE won't restart after a reboot

1. `systemctl status frekcore` (or `docker compose ps`) — read the actual
   failure, don't guess.
2. Common causes in this codebase specifically: `.env` missing/unreadable
   (service user permissions changed on reboot?), `FREK_PASSPORT_KEY_PATH`
   unreachable (disk not mounted yet at boot — add `After=` /
   `RequiresMountsFor=` in the systemd unit if the key lives on a separate
   mount), `CORS_ORIGINS` unset (fails closed by design — check `.env` is
   actually being loaded, not a bug to route around).
3. `journalctl -u frekcore -n 100` for the real traceback.

### Cloudflare Tunnel is down

1. `systemctl status cloudflared` on the host.
2. Check Cloudflare's own status page — if it's a Cloudflare-side outage,
   there is nothing to fix locally; FREKCORE itself is unaffected and
   still running on `localhost:8001`, only unreachable from the public
   internet until Cloudflare recovers.
3. If `cloudflared` itself crashed, `systemctl restart cloudflared` — its
   own `Restart=on-failure` should have already done this automatically;
   investigate why it didn't if this step is ever needed manually.

### Disk full

1. `/health/deep` already alerts below 500MB free before this becomes
   critical — this runbook step is for after that warning was missed.
2. Check, in order: backup archive count (`GET /admin/backup/status` —
   is `BACKUP_RETENTION_DAYS` pruning actually running?), log file size
   (§4), Docker image/layer bloat (`docker system df` if using Docker).
3. Never delete `.passport_key.pem` or an unverified backup archive to
   free space — confirm a given backup is safely superseded (a newer,
   verified-restorable one exists) before removing it.

### Proof/notary service (chain append, OTS submission) fails

1. `GET /notary/chain/verify` (or `/health/deep`'s `notary_chain` check)
   — is the *local* chain still internally consistent? If yes, the local
   proof pipeline (hash + local chain append) is unaffected even if OTS
   submission itself is failing — this is the intended, already-tested
   degradation mode (`scripts/chaos/test_ots_cut.sh`: local block creation
   continues, OTS submission queues and drains on network recovery, never
   blocks the main pipeline).
2. If the *local* chain check itself fails (`valid: false`), this is a
   `chain_watchdog.py`-severity-critical event — treat as data-integrity
   incident, not a routine ops issue: stop writes, investigate before
   resuming (a genuinely corrupted local chain is the one failure mode
   this codebase does not have a documented automatic-safe-degradation
   path for, correctly, since silently continuing on top of a broken
   chain would be worse than stopping).
