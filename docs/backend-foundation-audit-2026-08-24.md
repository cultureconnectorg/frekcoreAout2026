# Backend foundation gate audit — 2026-08-24

## Environment diagnosis

| Check | Finding | Impact | Status |
| --- | --- | --- | --- |
| Runtime Python | Active interpreter is Python 3.14.4 with only `pip` and `pytest`; it has no FastAPI, Motor, PyMongo, Pydantic, or `python-dotenv`. | `pytest` stops while importing `backend/tests/conftest.py`. | Blocked in this runtime |
| Declared dependencies | `backend/requirements.txt` declares the missing dependencies with exact pins. There is no `pyproject.toml`, lockfile, virtualenv, Dockerfile, compose file, or documented bootstrap command. | The required environment cannot be recreated from the repository alone. | P1 remediation required |
| Dependency installation | `python -m pip install --user -r backend/requirements.txt` was attempted. The configured package proxy returned HTTP 403 before any package download. No cached wheels are present. | Dependencies cannot be installed in this isolated execution environment. | External environment block |
| MongoDB | No `mongod`, Docker executable, running MongoDB process, `MONGO_URL`, `DB_NAME`, or repository `.env` file is available. | The existing tests are live-service tests and cannot exercise persistence/integrity locally. | External environment block |
| Test architecture | `backend/tests/conftest.py` targets a real backend at `http://localhost:8001` and best-effort purges rate limits. Many suites also require real credentials and Mongo. | A reproducible service topology is required; unit and live integration concerns are currently mixed. | P1 remediation required |

## Backend P1 audit matrix

| ID | Component | Finding | Decision |
| --- | --- | --- | --- |
| BE-001 | Reproducibility | No container/compose/bootstrap documentation despite exact dependency requirements and live Mongo tests. | Add versioned Python 3.12 container configuration, Mongo service, explicit required env template, and test command. |
| BE-002 | OpenAPI | FastAPI only exposes the schema when `FREK_PUBLIC_DOCS=true`; no versioned artifact/drift command exists. | Add a deterministic offline export/check command. It must not enable production docs. |
| BE-003 | Unique indexes | `_ensure_unique_sparse_index` drops an incompatible index automatically, without duplicate inspection. | Remove automatic index drops. Add an explicit, idempotent duplicate preflight migration that never deletes documents. |
| BE-004 | Error paths | Optional anchor, key-permission, and webhook paths contain silent exception handling. | Log contextual non-critical failures; do not convert critical persistence failures to success. |
| BE-005 | Data integrity | FK/moment/identity/notary operations are coupled to Mongo and object storage but cannot be transaction-tested without Mongo. | Do not introduce untested transactions or alter historical records; validate with the new container topology before changes. |

## No-go decision

This audit does **not** mark the backend green. Until a Mongo-backed container run executes
the backend tests and exports the real FastAPI OpenAPI schema, OpenAPI, data-integrity and
E2E claims remain unvalidated. No FREK ecosystem contract, external branch, or production
data is modified by this audit.
