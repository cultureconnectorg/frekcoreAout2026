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

    # Instance store (P1, 2026-08-31) — persists real objects, not just
    # schema validation. create_object needs the same authority the server
    # itself requires: an OAuth2 client bearer_token (registry:write) or an
    # identity_engine holder session_token.
    artist = client.create_object(
        "frek.artist", {"display_name": "Luciole"}, bearer_token="..."
    )
    same = client.get_object("frek.artist", artist["frek_id"])
    page = client.list_objects("frek.artist", status="draft")
```

## Tests

```bash
PYTHONPATH=backend:sdk/python python3 -m pytest sdk/python/tests -v
```

These are real end-to-end tests: `FrekcoreRegistryClient` is bound directly
to the actual `registry_router` FastAPI app via `fastapi.testclient.TestClient`
(itself an `httpx.Client` subclass) — no live server, no mocking of the
SDK's own HTTP layer. The schema-catalog tests need no MongoDB (those
endpoints are stateless); the instance-store tests (`create_object`/
`list_objects`/`get_object`) use `mongomock_motor` the same way
`backend/tests/test_registry_objects_unit.py` does. 10/10 passing as of
this writing.
