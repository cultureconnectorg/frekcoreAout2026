# FREKCORE Deployment Architecture (Self-Hosted + Cloudflare Tunnel)

**Status: PLANNING ARTIFACT.** Templates and recommendations below are ready
to apply; none have been applied to any running system by this session (no
access to the founder's machine). Companion to
`FREKCORE_PRODUCTION_READINESS_PLAN.md`.

## Topology (as the founder described it, made concrete)

```
Internet
  |
  v
DNS (Cloudflare)
  |
  v
Cloudflare edge (TLS termination, WAF, DDoS protection)
  |
  v
Cloudflare Tunnel (outbound-only connection FROM the founder's PC --
                    no inbound port is ever opened on that machine)
  |
  v
cloudflared daemon (systemd-managed, on the founder's PC)
  |
  v
http://localhost:8001  <-- FREKCORE (uvicorn, systemd- or compose-managed)
  |
  v
MONGO_URI (TLS)  --> MongoDB Atlas
```

Nothing in this topology requires the founder's PC to have a public IP,
open inbound ports, or a static IP — Cloudflare Tunnel's whole point is that
the connection is always initiated outward from the PC to Cloudflare's edge.
This directly satisfies the founder's own "pare-feu local ne doit pas exposer
inutilement des ports" requirement: with a tunnel in place, the correct local
firewall posture is to allow **zero** inbound ports at all, not even 8001
(the tunnel reaches FREKCORE over `localhost`, never over the LAN/WAN
interface).

## 1. Host OS baseline (FOUNDER-OPERATED)

- A dedicated, non-admin OS user to run FREKCORE and `cloudflared` (never
  root) — matches this codebase's own existing discipline (`backup_frekcore.sh`
  already assumes secrets live in root-only-readable paths; the running
  process itself should not need root).
- OS auto-updates enabled for security patches (unattended-upgrades on
  Debian/Ubuntu, or the platform equivalent) — covers the founder's "mises à
  jour sécurisées: OS" item; Python/dependency updates are separate (§7
  below).
- `systemd-timesyncd` or `chrony` enabled — covers "horloge fiable / NTP".
  Verify with `timedatectl status` (`System clock synchronized: yes`).

## 2. Running FREKCORE as a real service

Two equally valid paths — pick one, don't run both. Neither is applied by
this session.

### Path A — fix `docker-compose.yml` (minimal, one line)

The `backend` service currently has **no** `restart:` policy (`mongo` does).
Add one:

```yaml
services:
  backend:
    build: {context: ., dockerfile: Dockerfile}
    restart: unless-stopped   # <-- add this line
    ...
```

`unless-stopped` restarts on crash and on daemon/host reboot (as long as
Docker itself is enabled to start on boot — `sudo systemctl enable docker` at
the OS level), but respects a deliberate `docker compose stop`.

### Path B — systemd unit (no Docker, direct `uvicorn`)

```ini
# /etc/systemd/system/frekcore.service
[Unit]
Description=FREKCORE backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=frekcore
WorkingDirectory=/opt/frekcore/backend
EnvironmentFile=/opt/frekcore/backend/.env
ExecStart=/opt/frekcore/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001
Restart=on-failure
RestartSec=5
# Hardening (safe defaults for a network service with no need to touch
# unrelated parts of the filesystem):
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/opt/frekcore/backend /app/backups
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now frekcore.service
sudo systemctl status frekcore.service     # confirm active (running)
journalctl -u frekcore.service -f          # tail logs
```

Bind to `127.0.0.1`, not `0.0.0.0`, in this path specifically — the tunnel
reaches it over loopback, and nothing else ever should.

## 3. Cloudflare Tunnel

```ini
# /etc/systemd/system/cloudflared.service (installed by `cloudflared service install`,
# shown here for reference / to confirm it exists after that command)
[Unit]
Description=cloudflared
After=network-online.target

[Service]
Type=notify
ExecStart=/usr/local/bin/cloudflared --config /etc/cloudflared/config.yml tunnel run
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```yaml
# /etc/cloudflared/config.yml
tunnel: <tunnel-uuid>              # from `cloudflared tunnel create frekcore`
credentials-file: /etc/cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: api.frekcore.example  # replace with the founder's real domain
    service: http://localhost:8001
  - service: http_status:404        # catch-all, required as the last rule
```

```bash
cloudflared tunnel login                       # once, opens a browser to authorize
cloudflared tunnel create frekcore              # creates the tunnel + credentials file
cloudflared tunnel route dns frekcore api.frekcore.example   # creates the DNS record
sudo cloudflared service install                # installs the systemd unit above
sudo systemctl enable --now cloudflared
```

After this, `https://api.frekcore.example` reaches FREKCORE, with Cloudflare
handling public TLS, DDoS protection, and (once enabled in the dashboard) WAF
— all FOUNDER-OPERATED dashboard/CLI steps, no FREKCORE code involved.

## 4. Route classification (public / private / admin / service-to-service)

Built from `docs/architecture/FREKCORE_API_CONTRACT_V1.md`'s existing
per-endpoint auth column — not re-derived, summarized here by class so the
tunnel/WAF layer can reason about it in one place:

| Class | Examples | Cloudflare-layer guidance |
|---|---|---|
| **PUBLIC (no auth)** | `GET /health/live`, `GET /health/ready`, `.../verify` endpoints (public verification, D5/notary), `GET /registry/objects/{namespace}` (public read), legacy `/api/frek/verify/{frek_id}` | Fine to expose through the tunnel as-is. Consider a Cloudflare rate-limiting rule per-path here specifically (FREKCORE's own app-level rate limiter already covers this too — belt and suspenders, not a required duplicate). |
| **HOLDER-SESSION** | Most D1-D5 write/read routes with `X-FREK-Session` | Requires a real identity_engine session token; no additional Cloudflare-layer restriction needed beyond the default. |
| **ADMIN (`X-Admin-Key`)** | `/admin/backup/*`, `.../force-upgrade`, most legacy `backend/frek/` writes' admin path | **Recommend a Cloudflare Access policy** (or at minimum a Cloudflare firewall rule restricting these paths to the founder's own IP/known IPs) in addition to the app-level key — the key alone, over the public internet, is a single factor. |
| **SERVICE-TO-SERVICE (client-credential OAuth2)** | `frek_v1/auth.py`-issued bearer tokens, registry write | These are meant for other systems, not browsers — no Cloudflare Access policy needed, but confirm `CORS_ORIGINS` (§ below) never includes a wildcard that would let a browser page call them cross-origin. |
| **INTERNAL_ONLY (contract)** | None currently (`INTERNAL_ENDPOINTS=0` per `FREKCORE_API_CONTRACT_V1.md`) | If one is ever added, it must never be routed through the public tunnel ingress at all — a second, non-public `cloudflared` ingress rule (or simply not adding it to `ingress:` above) is the correct control, not an app-level check alone. |

`GET /api/metrics` (`server.py:572` — already implemented, already
returning real Prometheus data, verified this document, not hypothetical)
belongs in the ADMIN class but currently has **no auth check at all**. This
is a real, concrete pre-launch fix: add an `X-Admin-Key` check (matching
`health/routes.py`'s own `_require_admin` pattern) and/or a Cloudflare
Access/IP restriction on this specific path before the tunnel goes live —
Prometheus scrape targets should never be public.

## 5. Local firewall (FOUNDER-OPERATED)

With Cloudflare Tunnel in place (§3), the correct baseline is:

- **Inbound**: deny everything from the WAN/router interface. The tunnel
  needs zero inbound ports.
- **Outbound**: allow HTTPS (443) to Cloudflare's edge (the tunnel) and to
  `*.mongodb.net` (Atlas) — both are outbound-initiated, so a default-deny-
  inbound / allow-outbound-established posture (the OS firewall default on
  most distros) already covers this without special-casing.
- If SSH is used to administer the machine remotely, restrict it to a known
  source IP or put it behind the same Cloudflare Access/Tunnel model rather
  than exposing port 22 directly.

## 6. dev / staging / production environment split

Not present today (`docker-compose.yml` is single-purpose). Minimal split
that keeps `docker-compose.yml` as the shared base:

```
docker-compose.yml            # base: image build, shared config
docker-compose.override.yml   # dev: bind-mounts source, hot reload, FREK_ENV=development
docker-compose.prod.yml       # prod: restart policy, resource limits, FREK_ENV=production, no bind mounts
```

```bash
# dev (override.yml is picked up automatically by `docker compose` if present)
docker compose up

# prod (explicit, no accidental dev override)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

A `staging` environment, if the founder wants one before promoting to
`api.frekcore.example`, is the same `prod` compose file pointed at a
**separate** Atlas database name (never a namespace/prefix inside the same
one — accidental cross-contamination between staging and production data is
exactly the class of mistake a separate `DB_NAME`/cluster prevents
structurally) and a separate Cloudflare Tunnel hostname (e.g.
`staging-api.frekcore.example`).
