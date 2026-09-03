# 07 — Deployment Report — FREKCORE

## 1. What exists today (evidence)

- `Dockerfile` (repo root): single-stage `python:3.12-slim`, installs `backend/requirements.txt`, runs `uvicorn server:app --host 0.0.0.0 --port 8001`. No multi-stage build, no non-root user, no `HEALTHCHECK` instruction.
- `docker-compose.yml`: two services — `mongo:7.0` and `backend` (built from the `Dockerfile` above). `SECRET_KEY`, `FREK_CLIENT_KILTIKONET_SECRET`, `FREK_CLIENT_CVLBRAIN_SECRET` are required (`${VAR:?...}` syntax — compose refuses to start without them, a correct fail-closed pattern). No frontend service, no reverse proxy/ingress, no volumes for anything but Mongo data.
- `.env.example` exists at `backend/.env.example` (not at repo root).
- No `docker-compose.dev.yml` / `docker-compose.prod.yml` split — a single compose file serves both purposes today.
- No CI/CD pipeline exists (`.github/workflows/` is absent — confirmed by directory listing, see `01_FORENSIC_AUDIT.md` §3). Nothing currently builds the Docker image, runs the test suite, or lints on push/PR.

## 2. Gap vs. Master Prompt Phase 13 (Docker) / Bloc 12 (CI/CD)

| Requirement | Status | Evidence |
|---|---|---|
| `Dockerfile` | EXISTS | see above |
| `docker-compose.yml` | EXISTS (single, not split dev/prod) | root `docker-compose.yml` |
| `.env.example` | PARTIAL (present under `backend/`, not at root as the prompt implies) | `backend/.env.example` |
| Production Compose | MISSING (no separate prod overlay) | — |
| Development Compose | MISSING (no separate dev overlay) | — |
| Healthcheck (Docker-level) | MISSING | no `HEALTHCHECK` in `Dockerfile`, no `healthcheck:` block in `docker-compose.yml` — even though the app itself exposes `/api/v1/health/live` and `/health/deep`, Docker/Compose is not configured to poll them |
| Volumes | PARTIAL | Mongo data volume only (`frekcore_mongo`); no volume for uploaded media / object storage referenced by `backend/moment/storage.py` |
| GitHub Actions: Lint | MISSING | no workflow file |
| GitHub Actions: Type Check | MISSING | `mypy` is a listed dependency (`backend/requirements.txt:70`) but nothing invokes it in CI |
| GitHub Actions: Tests | MISSING | no workflow runs `pytest` |
| GitHub Actions: Security Scan | MISSING | no workflow; no `bandit`/`safety`/`pip-audit` dependency found either |
| GitHub Actions: Docker Build | MISSING | no workflow builds the image |
| GitHub Actions: Coverage Report | MISSING | no coverage tooling at all, see `06_TEST_REPORT.md` |
| GitHub Actions: Release | MISSING | no workflow, no versioning/tag automation found |

## 3. What this session changed operationally

- **Zero deployment-affecting changes.** `backend/registry/` adds pure-Python modules and JSON data files under `backend/`, which `COPY backend ./` in the existing `Dockerfile` already picks up with no changes needed to the Dockerfile or compose file.
- `jsonschema==4.26.0` (used by the new module) was **already** pinned in `backend/requirements.txt:58` before this session — no new runtime dependency was introduced.
- The only change to a file that affects the running app is the 3-line router registration in `backend/server.py` (see `08_NEXT_INTEGRATION.md` for the exact diff) — additive, same pattern as the other 30 router registrations already in that file.

## 4. Recommendation (not implemented this session)

1. Add `.github/workflows/ci.yml` covering lint (`flake8`, already a dependency) → typecheck (`mypy`, already a dependency) → `pytest` → `docker build`. This is the single highest-leverage gap identified across all 15 blocks (see `02_GAP_ANALYSIS.md` priority ranking) because it currently gates nothing.
2. Add `HEALTHCHECK` to the `Dockerfile` pointing at `/api/v1/health/live`.
3. Split `docker-compose.yml` into a base file + `docker-compose.override.yml` (dev) / `docker-compose.prod.yml`, per the Master Prompt's explicit ask.
4. Move `.env.example` to repo root (or add one there re-exporting `backend/.env.example`) so it is discoverable at the level `docker-compose.yml` lives.
