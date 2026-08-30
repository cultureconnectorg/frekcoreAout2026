# FREKCORE Python SDK (Phase 2 — Priority 7)

**Scope**: wraps only `/api/v1/registry/*` (the FREK Registry API). See
`frekcore_sdk/__init__.py`'s docstring for why every other FREKCORE API
family is intentionally not wrapped yet, and
`reports/12_PHASE2_IMPLEMENTATION.md` for the reasoning.

## Install (editable, for development)

```bash
pip install -e sdk/python
```

## Usage

```python
from frekcore_sdk import FrekcoreRegistryClient

with FrekcoreRegistryClient(base_url="https://frekcore.example.com") as client:
    namespaces = client.list_namespaces()
    result = client.validate("frek.artist", {"frek_id": "...", "entity_type": "frek.artist", ...})
    print(result.valid, result.errors)
```

## Tests

```bash
PYTHONPATH=backend:sdk/python python3 -m pytest sdk/python/tests -v
```

These are real end-to-end tests: `FrekcoreRegistryClient` is bound directly
to the actual `registry_router` FastAPI app via `fastapi.testclient.TestClient`
(itself an `httpx.Client` subclass) — no live server, no MongoDB, no mocking
of the SDK's own HTTP layer. 5/5 passing as of this writing.
