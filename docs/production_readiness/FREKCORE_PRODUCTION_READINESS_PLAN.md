# FREKCORE Production Readiness Plan — Master Index

**Status of this document: PLANNING ARTIFACT, not an executed state.** Written
in response to the founder's 2026-09-03 roadmap message (self-hosted server +
Cloudflare Tunnel + MongoDB Atlas + full ops posture, ending in `State 9` ->
`State 10 (Freeze)` -> `Production Readiness` -> `Red/Blue/Purple` -> CVLN
wiring). This document, and its 4 companions in this directory, are **doc-only,
repo-side preparation** for that sequence — they do **not** constitute
`STATE_9`, do **not** constitute Production Readiness, provision no real
infrastructure, and change no application code. Per the founder's own
authorization pattern used throughout this project, executing any of the
states this plan prepares for still requires its own explicit
`STATE_TRANSITION_AUTHORIZATION`.

**What this session can and cannot do**: this session runs inside a sandboxed
container with no access to the founder's PC, Cloudflare account, DNS
registrar, or physical hardware. Every item below tagged **FOUNDER-OPERATED**
is something only the founder (or whoever administers that infrastructure) can
actually provision — this plan documents exactly what to do and hands over
concrete artifacts (config templates, scripts, checklists) to do it with, but
cannot do it from here. Items tagged **REPO-SIDE** are things this session can
prepare, and their status below reflects what was verified to already exist in
this repository (not assumed) versus what is still to write.

Companion documents:
- `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` — topology, service manager, reverse
  proxy/route classification, TLS, firewall.
- `FREKCORE_SECRETS_KEYS_AUTH_PLAN.md` — secrets management, Ed25519 key
  lifecycle, production auth/authz.
- `FREKCORE_OPERATIONS_RUNBOOKS.md` — monitoring, alerting, logs, backup/DR,
  capacity, power/NTP, and concrete incident runbooks.
- `FREKCORE_READINESS_ROADMAP.md` — State 9 -> State 10 -> Production
  Readiness -> Red/Blue/Purple sequencing, and the still-open technical items
  (real Mongo, real OTS/Bitcoin anchor, D1 scientific status, delegation
  runtime wiring).

## Legend

- **EXISTS** — real, verified in this repository (file/route/script cited).
- **PARTIAL** — something real exists but doesn't fully cover the ask.
- **MISSING** — nothing in this repository addresses this yet.
- **FOUNDER-OPERATED** — real infrastructure/physical/account setup outside
  any repository; this session cannot provision it, only document how.
- **REPO-SIDE** — something a repository commit can actually deliver
  (config templates, scripts, docs, code).

## 1. Serveur / hosting

| Item | Status | Evidence / note |
|---|---|---|
| Serveur (PC du founder) | FOUNDER-OPERATED | Physical machine, not this session's to provision. See `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §1 for the OS/hardening baseline to apply to it. |
| FREKCORE tourne comme un vrai service (auto-restart on crash/reboot) | PARTIAL / REPO-SIDE deliverable | `Dockerfile` + `docker-compose.yml` exist (`restart: unless-stopped` on the `mongo` service only — the `backend` service has **no** restart policy set, a real gap). No systemd unit exists in-repo. `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §2 provides both a `docker-compose.yml` fix and a systemd unit template as two alternative paths — founder picks one. |
| Firewall local | FOUNDER-OPERATED | See `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §5 for the exact rule set (only Cloudflare Tunnel's outbound connection needs to leave the machine; no inbound port should be opened at the router/OS firewall at all). |

## 2. Base de données

| Item | Status | Evidence / note |
|---|---|---|
| MongoDB Atlas | PARTIAL | Credentials supplied and confirmed reachable from GitHub Actions this session (`real-mongo-validation` CI job, `REAL_MONGO_CONNECTION` progressed past the secret-detection stage) but the connection itself currently fails at the TLS handshake layer (`SSL: TLSV1_ALERT_INTERNAL_ERROR`) on every one of the 3 shard hosts — see `FREKCORE_READINESS_ROADMAP.md` §2 for the live status and the Atlas-side action needed (most likely Network Access IP allowlist). FOUNDER-OPERATED to resolve (Atlas project settings); once resolved, the exact same CI job re-validates automatically, no code change needed. |
| TLS vers MongoDB | EXISTS (by construction) | `mongodb+srv://` connection strings are TLS-only by default in `pymongo`; nothing in this codebase disables it. Once the handshake issue above is resolved, TLS-to-Atlas is already correct, not a separate task. |
| Index MongoDB réels (vérifiés sur Atlas, pas seulement dans le code) | MISSING until real Atlas access works | `backend/tests/test_real_mongo_validation.py::TestIndexValidation` is written and ready (calls each module's real `ensure_indexes()` against the real cluster, checks idempotency and the real unique-constraint enforcement) — blocked on the same TLS issue above, not a missing test. |
| Migrations de données (versionner les changements de schéma) | PARTIAL | Corrected after verification: `backend/migrations/` exists with one real, reviewed precedent (`20260824_unique_index_preflight.{md,py}`) — a documented, read-only-first, explicit-rollback-plan convention for schema/index changes, not an assumption. **What's missing** is generalization: no runner/version-table automates applying migrations in order or tracks which have run against a given database — today's pattern is "one dated script + doc per change, run by hand." Sufficient for the current single-migration reality; worth a lightweight runner once there are enough of these to make manual tracking error-prone (a Production-Readiness-stage item, not a State-9 blocker). |

## 3. Exposition réseau / DNS / TLS public

| Item | Status | Evidence / note |
|---|---|---|
| Cloudflare Tunnel | FOUNDER-OPERATED to create; REPO-SIDE template provided | `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §3 gives the exact `cloudflared` config file and systemd unit to run the tunnel client as its own auto-restarting service, distinct from the FREKCORE process itself. |
| Nom de domaine / sous-domaine (`api.frekcore...`) | FOUNDER-OPERATED | Domain registration/DNS record creation is an account-level action; §3 of the architecture doc gives the exact `cloudflared tunnel route dns` command once the founder owns the domain in Cloudflare. |
| TLS partout (public) | FOUNDER-OPERATED (Cloudflare-managed) + REPO-SIDE (no plaintext HTTP fallback) | Cloudflare terminates public TLS by default once the tunnel/DNS above exist. Repo-side: confirm FREKCORE itself never needs to also terminate TLS (the tunnel connects to `http://localhost:8001` internally, which is correct and is what §3's template assumes — the tunnel, not FREKCORE, is the TLS boundary). |
| DNS résilient | FOUNDER-OPERATED | Cloudflare's own DNS is already a resilient anycast service once configured; no additional repo-side action. |
| Protection DDoS / WAF | FOUNDER-OPERATED (Cloudflare) | Cloudflare's free/pro tier WAF + DDoS protection covers the public edge once the domain proxies through it (orange-cloud DNS record) — no code change needed, but must be explicitly enabled in the Cloudflare dashboard, not assumed on by default for a bare tunnel. |

## 4. Secrets, clés, permissions

| Item | Status | Evidence / note |
|---|---|---|
| Gestion des secrets (jamais en dur) | EXISTS | `backend/.env.example` documents every required env var with no real values; `server.py` reads secrets exclusively via `os.environ[...]`; `.env` is never committed (confirmed: not in `git ls-files`). GitHub Actions secret (`MONGO_URI`) confirmed working this session. Full policy: `FREKCORE_SECRETS_KEYS_AUTH_PLAN.md` §1. |
| Clés cryptographiques (Ed25519) — stockage, rotation, révocation | PARTIAL | Storage: `backend/passport/keys.py` (file-based, `FREK_PASSPORT_KEY_PATH`), `/health/deep` already reports the key's SHA-256 fingerprint and file-permission mode (`mode_secure`) — real, existing verification. **Rotation and revocation have no implementation or documented procedure today** — a real gap, sized in `FREKCORE_SECRETS_KEYS_AUTH_PLAN.md` §2. |
| Authentification / autorisation production (users, services, délégations, scopes, révocations) | PARTIAL | `permissions/` (Role/Scope/Action/decide()), `permissions/delegation.py` (`delegation_authority_chain_valid()`, STATE_8) are real, tested — but **not wired into any live route** (disclosed, unchanged status since STATE_7/8). `identity_engine` (WebAuthn) and `frek_v1/auth.py` (client-credential OAuth2) are the two systems actually enforcing auth on live routes today. Full picture and the wiring gap: `FREKCORE_SECRETS_KEYS_AUTH_PLAN.md` §3. |
| Rate limiting / anti-abus | EXISTS | `backend/security/policies.py::check_rate_limit()` — per-scope/action count+window config, Mongo-backed, with `FREK_DISABLE_RATE_LIMIT=1` test escape hatch; already called from every D1-D5 write route (confirmed throughout D1-D6 test suites). |
| CORS strict | EXISTS | `server.py::cors_origins_from_env()` — fails closed (`raise RuntimeError`) if `CORS_ORIGINS` is unset in production; explicit allowlist only, no wildcard. |
| Idempotency production | PARTIAL | Domain-derived idempotency exists per-capability (content_binding dedup-by-hash, offline_transport conflict-on-same-sequence, registry 409-on-duplicate) — documented in `docs/architecture/FREKCORE_VERSIONING_POLICY.md` §7. No generic caller-supplied idempotency-key header exists across all routes; STATE_7's own policy decision was that domain-derived keys are preferred where the domain has a natural one. |

## 5. Reverse proxy / routing classification

| Item | Status | Evidence / note |
|---|---|---|
| Quelles routes sont publiques / privées / admin / service-to-service | PARTIAL | Individually, every route already has its own auth requirement in code (public-no-auth, holder-session, admin-key, client-credential OAuth2) — confirmed throughout D1-D6/STATE_6/7/8. **No single document classifies all ~65 canonical+legacy routes by this axis in one place.** `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §4 builds that classification table, reusing `docs/architecture/FREKCORE_API_CONTRACT_V1.md`'s existing per-endpoint auth column rather than re-deriving it. |

## 6. Service manager / process supervision

| Item | Status | Evidence / note |
|---|---|---|
| Auto-restart on crash | MISSING (backend service) | See §1 above — `docker-compose.yml`'s `backend` service has no `restart:` policy today. Fix + systemd alternative: `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §2. |
| Auto-restart on reboot | MISSING | Same fix covers this (`restart: unless-stopped` or `systemctl enable`). |
| Chain watchdog (background integrity daemon) | EXISTS | `scripts/chain_watchdog.py` — periodic (6h default) `FrekChain.verify_chain()`, writes `security_events` at `severity=critical` on tamper detection, wired into `server.py` startup/shutdown, opt-out via `FREK_DISABLE_CHAIN_WATCHDOG=1`. Already production code, not a gap. |
| Backup scheduler daemon | EXISTS | `scripts/backup_scheduler.py` — daily (03:00 UTC default) trigger of `backup_frekcore.sh`, designed to run under supervisor/systemd (its own docstring says so; no actual `.conf`/`.service` file checked into the repo for it yet — see `FREKCORE_OPERATIONS_RUNBOOKS.md` §2). |

## 7. Observabilité / monitoring / alerting

| Item | Status | Evidence / note |
|---|---|---|
| Health checks (`/health`, readiness, liveness, dependencies) | EXISTS | `backend/health/routes.py`: `/health/live` (liveness), `/health/ready` (Mongo ping), `/health/deep` (Mongo + Ed25519 key fingerprint/permissions + disk + memory + notary-chain-integrity spot-check + last-backup-marker, always HTTP 200 with `status: healthy|degraded` in the body — real, already thorough). |
| Logs centralisés (erreurs, sécurité, accès, événements critiques) | PARTIAL | `security_events` collection (security anomalies, chain-watchdog criticals), `audit_trail` (append-only business events), Python's `logging` module throughout (stdout, container-log-driver-visible) — no shipping to an external log aggregator (e.g. a hosted log service) configured; that's a FOUNDER-OPERATED choice of tool, not a code gap. See `FREKCORE_OPERATIONS_RUNBOOKS.md` §1. |
| Monitoring (UP/DOWN, CPU, RAM, disk, Mongo, latence, offline queue, erreurs) | PARTIAL | `backend/observability/metrics.py` defines real Prometheus counters/histograms (`http_requests_total`, `http_request_duration_seconds`, `http_errors_total`, `registry_operations_total`, `identity_operations_total`, `proof_operations_total`, `event_operations_total`), and `GET /api/metrics` (`server.py:572`) already exposes them in real Prometheus exposition format — corrected after verification (an earlier draft of this document wrongly claimed no route mounted it; it does). **Real gap found instead**: that route has **no auth check at all** — it is public today. `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §4 reclassifies it as ADMIN and recommends gating it (Cloudflare Access/IP restriction at minimum, an `X-Admin-Key` check in code for defense in depth) before the tunnel goes live, since Prometheus scrape data is not meant for the public internet. `/health/deep` already covers CPU/RAM/disk/Mongo/chain/backup as a separate pull-based check. Offline-queue depth and per-endpoint latency are not yet counted among the Prometheus metrics themselves. |
| Alertes (down, Mongo inaccessible, disque plein, proof service échoue) | MISSING (repo-side) / FOUNDER-OPERATED (delivery channel) | `chain_watchdog.py` and `/health/deep` produce the *signal*; nothing today *pushes* that signal to a human (no webhook/email/SMS integration). `scripts/chain_watchdog.py`'s own docstring already names the intended pattern ("external monitoring... can poll `GET /notary/chain/verify`") — this plan turns that into a concrete recipe in `FREKCORE_OPERATIONS_RUNBOOKS.md` §1 (e.g., an external uptime-checker polling `/health/deep` and alerting on `status != healthy`, which needs no new FREKCORE code, only a founder-chosen external service). |

## 8. Backup / disaster recovery

| Item | Status | Evidence / note |
|---|---|---|
| Sauvegardes MongoDB | EXISTS | `scripts/backup_frekcore.sh` — `mongodump` + Ed25519 key backup (with its own SHA-256 fingerprint) + `.env` files, optional GPG symmetric encryption, configurable retention, JSON manifest per backup. Triggerable via `POST /admin/backup/trigger` (admin-key-gated) or the scheduler daemon. |
| Sauvegarde de la config FREKCORE (sans secrets en clair) | PARTIAL | The backup script copies `.env` files into the (optionally GPG-encrypted) archive — so secrets ARE captured, but only ever inside the encrypted archive, never in a separate plaintext artifact; this matches "backup, not leak" but should be stated as policy explicitly, done in `FREKCORE_SECRETS_KEYS_AUTH_PLAN.md` §1. |
| Backup/restore testée | EXISTS | `scripts/restore_test.sh` — restores into a disposable, uniquely-named temp database, verifies, then drops it; never touches the production database. Also exposed as `POST /admin/backup/restore-test/{archive_name}`. |
| RPO / RTO / plan de récupération | MISSING | No document states target Recovery Point Objective / Recovery Time Objective, or a step-by-step "rebuild the server from nothing" procedure. `FREKCORE_OPERATIONS_RUNBOOKS.md` §3 defines both. |
| Capacité disque locale (logs, cache, queues, temp) | PARTIAL | `/health/deep` alerts when free disk drops below 500MB — a real, existing floor check. No documented retention/rotation policy for logs or the offline-transport queue's own growth. `FREKCORE_OPERATIONS_RUNBOOKS.md` §4. |
| Coupure de courant (arrêt brutal, reprise, pas de corruption) | PARTIAL | MongoDB's own write-ahead journal is durable-by-default against unclean shutdown (Atlas manages this) — not a FREKCORE-specific gap. The offline-transport queue (`transport_envelopes`, `sync_status`) is already designed to be safely re-processed rather than lost/duplicated on restart (STATE_8's own restart-safety findings). No local disk WAL/journal exists outside Mongo (correct — this codebase deliberately keeps no local database, per its own storage-abstraction rules). |
| UPS / onduleur | FOUNDER-OPERATED | Physical hardware; recommended if the founder's PC becomes a real single point of failure for the service, sized in `FREKCORE_READINESS_ROADMAP.md` §5. |
| Connexion Internet stable / IP sortante stable | FOUNDER-OPERATED | Cloudflare Tunnel's outbound-only model (see §3 above) removes the need for a *stable inbound* IP entirely — the tunnel client reconnects outward regardless of the founder's own IP changing. A stable outbound path still matters for reaching Atlas; no code-side mitigation exists for an ISP outage itself. |
| Horloge fiable / NTP | FOUNDER-OPERATED (OS-level) + REPO-SIDE (dependency, not fix) | Every timestamp/proof/signature/expiry in this codebase already assumes a correct system clock (RFC3339 UTC throughout, `FREKCORE_VERSIONING_POLICY.md` §5) — this is a real, disclosed dependency, not something FREKCORE code can self-correct. Runbook: `FREKCORE_OPERATIONS_RUNBOOKS.md` §5 (enable `systemd-timesyncd`/`chrony`, verify with `timedatectl`). |

## 9. CI/CD, environments, testing

| Item | Status | Evidence / note |
|---|---|---|
| CI/CD (GitHub tests/validates/deploys without manual server edits) | PARTIAL | `.github/workflows/ci.yml` EXISTS and is real (built across STATE_6/7/8: blocking lint/format/typecheck, unit tests + coverage, Python/TypeScript SDK tests, plus the new `real-mongo-validation` job) — this directly **contradicts** the stale "no CI/CD exists" finding in `reports/07_DEPLOYMENT_REPORT.md` (written before this workflow was built; that report is now outdated on this specific point, not this plan's to silently correct further than noting here). **What's still missing**: a *deploy* step — CI validates but nothing pushes a new build to the founder's server automatically. Sized in `FREKCORE_READINESS_ROADMAP.md` §4. |
| Environnements séparés dev/staging/production | MISSING | Single `docker-compose.yml` serves all purposes today (matches `07_DEPLOYMENT_REPORT.md`'s finding, still accurate). `FREKCORE_DEPLOYMENT_ARCHITECTURE.md` §6 sketches the split. |
| Tests réels MongoDB | PARTIAL, infrastructure built this session | `backend/tests/test_real_mongo_validation.py` (20 tests) + `real-mongo-validation` CI job — written, dry-run-validated, wired to the real secret; blocked only on the Atlas TLS handshake issue (§2 above), not on missing test code. |
| Tests de redémarrage | PARTIAL | `TestRestartReconnection` in the same file covers process/client-level restart against real Mongo (blocked, same reason). `chaos/test_mongo_cut.sh` and the offline-queue's own restart-safety (STATE_8) cover adjacent ground already. |
| Tests de backup/restore | EXISTS | `scripts/restore_test.sh`, described above — a genuine, already-automatable restore verification, not just a written plan. |
| Tests de perte réseau | EXISTS | `scripts/chaos/test_mongo_cut.sh`, `scripts/chaos/test_ots_cut.sh` — already-written chaos scripts for exactly this. |
| Tests de perte Mongo | EXISTS | `scripts/chaos/test_mongo_cut.sh` (see above) — this session's own real-Mongo TLS failure this run is, incidentally, a live instance of exactly this scenario, and FREKCORE's blocking CI stayed green throughout (confirmed both times), which is itself a positive data point for this item. |
| Tests de coupure brutale | PARTIAL | No SIGKILL-mid-write chaos test exists yet; Mongo's own durability (§8 above) covers the data-layer half. `FREKCORE_OPERATIONS_RUNBOOKS.md` §6 proposes the missing test. |
| Tests de révocation | EXISTS | `tests/test_offline_transport_unit.py::TestRevocation`, the STATE_8 delegated-authority revocation-propagation tests (`tests/test_permissions.py`), identity revocation tests (`tests/test_identity_lifecycle.py`, `test_identity_recovery_unit.py`). |
| Tests de permissions | EXISTS | The entire `permissions/` test suite (31 tests as of STATE_8) plus every route's own `TestUnauthorized` class throughout D1-D6. |
| Tests d'attaque / Red Team / Blue Team / Purple Team | NOT STARTED (by explicit prior instruction) | Every prior state's authorization has explicitly prohibited this (`RED_TEAM=FALSE` etc.) — correctly not attempted. Sequencing: `FREKCORE_READINESS_ROADMAP.md` §1. |

## 10. Versioning / contracts / observability of the proof layer

| Item | Status | Evidence / note |
|---|---|---|
| Gestion des versions API | EXISTS | `docs/architecture/FREKCORE_VERSIONING_POLICY.md` (STATE_7) — `/api/v1/...` policy, backward-compat rules, schema/enum/identifier/time contracts. |
| Contrat SDK/API figé | EXISTS | `docs/architecture/FREKCORE_API_CONTRACT_V1.md` + golden snapshot test (`backend/tests/test_api_contract.py`) — genuinely detects breaking changes, re-verified green through STATE_8. |
| Observabilité de la Proof Layer | PARTIAL | `/health/deep`'s notary-chain spot-check + `docs/architecture/FREKCORE_EVENT_CONTRACT_V1.md`'s event catalog cover the basics; no dedicated proof-layer dashboard/metric set beyond the generic `proof_operations_total` counter (unmounted, §7 above). |
| Validation OTS réelle | BLOCKED (environment) | `docs/validation/FREKCORE_STATE8_VALIDATION_RESULTS.md` §6 — OTS calendar servers unreachable from this sandbox; not yet attempted from an environment with open egress. |
| Validation Bitcoin anchor réelle | NOT_VERIFIED (depends on OTS above) | Same source — depends on real OTS confirmation plus real wall-clock time. |
| Validation réelle du fingerprint D1 | PARTIAL, by design | `D1_VERIFIED=PARTIAL` is the deliberate, evidence-scoped status (`reports/FREKCORE_D1_VALIDATION_EVIDENCE.md`) — determinism/exact-match/fail-safe DEMONSTRATED, gain/noise/resample robustness PARTIALLY_DEMONSTRATED on narrow fixtures, lossy-compression/re-recording/collision-rate NOT_TESTED. Not upgraded without new scientific evidence, per every prior state's own instruction. |
| Validation runtime des délégations (branchement live) | PARTIAL, by design | STATE_8 closed `DELEGATED_AUTHORITY` to `VERIFIED` at the UNIT_VERIFIED level (`permissions.delegation.delegation_authority_chain_valid()`) — genuinely not wired into any live route, matching `RoleGrant`/`decide()`'s own long-standing, disclosed status. Wiring it into a real route is Production-Readiness-stage work, sized in `FREKCORE_READINESS_ROADMAP.md` §3. |

## 11. Sequencing (summary — full detail in `FREKCORE_READINESS_ROADMAP.md`)

`STATE_9_FINAL_HISTORICAL_ARCHITECTURAL_RECONCILIATION` -> `STATE_10` (freeze
assessment) -> formal `PRODUCTION_READINESS` -> Red/Blue/Purple Team -> CVLN
ecosystem wiring. None of these are started by this plan. This plan exists so
that when each is formally authorized, the concrete preparation (templates,
scripts, checklists, honest status) is already sitting in the repository
rather than needing to be improvised under time pressure.
