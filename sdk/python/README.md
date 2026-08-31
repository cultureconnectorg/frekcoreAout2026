# FREKCORE Python SDK (Phase 2/3 — Priority 7)

**Scope**: two clients, each wrapping one API family with strong,
reproducible evidence it's stable enough to commit to as a client
contract. See `frekcore_sdk/__init__.py`'s docstring for the full
reasoning, and `reports/12_PHASE2_IMPLEMENTATION.md`.

- `FrekcoreRegistryClient` — the full FREK Registry API
  (`/api/v1/registry/*`): schema catalog + the instance store.
- `FrekcoreIdentityClient` — `identity_engine`'s public-**read** surface
  only (`/api/v1/identity/*`). See `frekcore_sdk/identity_client.py`'s
  docstring for exactly why the write/lifecycle surface isn't wrapped.

## Install (editable, for development)

```bash
pip install -e sdk/python
```

## Usage

```python
from frekcore_sdk import FrekcoreRegistryClient, FrekcoreIdentityClient

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

# Identity Engine — public read surface (P2, 2026-08-31)
with FrekcoreIdentityClient(base_url="https://frekcore.example.com") as identity_client:
    public_view = identity_client.get_identity(artist["owner_id"] or "id-...")
    me = identity_client.get_me(session_token="...")               # holder-authenticated
    objects = identity_client.get_linked_objects(me["frek_id"], session_token="...")
    results = identity_client.search_identities(admin_key="...", display_name="Luciole")
```

## Tests

```bash
PYTHONPATH=backend:sdk/python python3 -m pytest sdk/python/tests -v
```

These are real end-to-end tests: both clients are bound directly to the
actual `registry_router`/`identity_router` FastAPI apps via
`fastapi.testclient.TestClient` (itself an `httpx.Client` subclass) — no
live server, no mocking of the SDK's own HTTP layer. The schema-catalog
tests need no MongoDB (those endpoints are stateless); the instance-store
and identity tests use `mongomock_motor`, the same way
`backend/tests/test_registry_objects_unit.py` does. 18/18 passing as of
this writing (10 Registry + 8 Identity).
