"""FREK Registry — API REST (Bloc 1, famille "Registry" du Bloc 8 / Phase 7).

The schema-catalog endpoints below (`/versions`, `/namespaces`, `/validate`,
`/events`) are stateless, no `set_db` required — as documented since Phase 1.

`/objects/{namespace}` (P1 backlog, `reports/08_NEXT_INTEGRATION.md` item 2
/ `reports/FREKCORE_COMPLETION_BACKLOG.md` P1 #7) is the Registry **instance
store**: it persists real objects, schema-validated before insert, into a
new `registry_objects` collection. This is the missing half of Bloc 1 that
every `docs/interfaces/*.md`'s "PROPOSED, NOT IMPLEMENTED" resolver
endpoint (e.g. KORA.md's `GET /registry/resolve/frek.artist/{frek_id}`)
depends on — `GET /objects/{namespace}/{frek_id}` below is that resolver in
substance (same lookup), kept under the `/objects` path rather than a
separate `/resolve` path since it's the same resource, not a new concept.

Deliberately does NOT publish any event on object creation: the FREK
Registry's `object.created` event (`backend/registry/events/event_registry.json`)
is catalogued with `producer: "fk"` — it is `.fk`'s own Cultural Object
Container creation path (`backend/fk/routes.py POST /fk/create`) that owns
that event, not this generic multi-namespace catalog. Emitting a
second, un-catalogued event type here would be inventing new vocabulary
the founder directive doesn't call for.
"""

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from frek_v1.auth import get_current_client
from identity_engine import service as identity_service

from . import service

registry_router = APIRouter(prefix="/registry", tags=["FREK Registry"])

db = None


def set_db(mongo_db):
    global db
    db = mongo_db


async def ensure_indexes():
    if db is None:
        return
    await db.registry_objects.create_index(
        [("namespace", 1), ("frek_id", 1)], unique=True
    )
    await db.registry_objects.create_index([("namespace", 1), ("owner_id", 1)])
    await db.registry_objects.create_index([("namespace", 1), ("status", 1)])
    await db.registry_objects.create_index([("namespace", 1), ("created_at", -1)])


def _require_db():
    """Narrows the nullable module-level `db` handle (for mypy, and for a
    clear 503 instead of a raw NoneType crash if `set_db()` was never
    called — e.g. this router mounted without server.py's startup wiring)."""
    if db is None:
        raise HTTPException(
            503, "Registry instance store not initialized (no database configured)"
        )
    return db


WRITE_PERMISSION = "registry:write"


def _generate_object_id() -> str:
    # "frek-" prefix (vs. identity_engine/frek_v1's "id-" prefix) to keep a
    # Registry catalog entry's own FREK-ID visibly distinct from a person's
    # identity FREK-ID — both are valid per _base.schema.json's
    # `^(id|frek)-[0-9a-f]{6,}-[0-9a-f]{2,}$` pattern, which anticipates
    # exactly this split.
    return f"frek-{secrets.token_hex(6)}-{secrets.token_hex(2)}"


async def _authorize_write(authorization: Optional[str], x_frek_session: Optional[str]):
    """Two live, already-established authority paths — no admin-key
    fallback invented for this route:

    - **ISSUER**: an OAuth2 client (frek_v1's client-credentials model,
      `backend/frek_v1/auth.py`) holding the `registry:write` permission —
      matches how external CVLN systems (KORA, LabelOS...) already
      integrate with FREKCORE elsewhere in this codebase.
    - **OWNER**: an identity_engine holder session (`X-FREK-Session`) — a
      person/org identity creating a registry object it will own itself
      (e.g. an artist publishing their own `frek.artist` entry).

    Returns (authority, actor) where authority is "issuer" | "owner".
    Raises 403 if neither validates.
    """
    if authorization:
        try:
            client = await get_current_client(authorization)
        except HTTPException:
            client = None
        if client and WRITE_PERMISSION in client.get("permissions", []):
            return "issuer", client["client_id"]

    if x_frek_session:
        frek_id = identity_service.verify_session_token(x_frek_session)
        if frek_id:
            return "owner", frek_id

    raise HTTPException(
        403,
        "Autorisation requise : client OAuth2 avec la permission "
        f"'{WRITE_PERMISSION}', ou session du titulaire (X-FREK-Session)",
    )


class NamespaceSummary(BaseModel):
    namespace: str
    version: str
    title: str
    description: str
    schema_url: str


class ValidateRequest(BaseModel):
    namespace: str = Field(
        ..., description="Namespace FREK Registry, ex: 'frek.artist'."
    )
    payload: Dict[str, Any]
    schema_version: str = Field(
        default=service.DEFAULT_VERSION, description="Version du schema, ex: 'v1'."
    )


class ValidateResponse(BaseModel):
    valid: bool
    namespace: str
    schema_version: str
    errors: List[str] = Field(default_factory=list)


class RegistryObjectCreateRequest(BaseModel):
    """The namespace-specific fields only (e.g. `frek.artist`'s
    `display_name`, `isni`...). Base-envelope fields (`frek_id`,
    `entity_type`, `status`, `created_at`, `version`) are filled in
    server-side per the rules on `create_registry_object` below; any of
    them the caller does supply are honored if valid, never silently
    dropped."""

    payload: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(default=service.DEFAULT_VERSION)


@registry_router.get("/versions")
async def list_versions():
    return {
        "versions": service.available_schema_versions(),
        "default": service.DEFAULT_VERSION,
    }


@registry_router.get("/namespaces", response_model=List[NamespaceSummary])
async def list_namespaces(schema_version: str = service.DEFAULT_VERSION):
    try:
        entries = service.list_namespaces(schema_version)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"unknown registry schema version '{schema_version}'",
        )
    return [
        NamespaceSummary(
            namespace=e.namespace,
            version=e.version,
            title=e.title,
            description=e.description,
            schema_url=f"/api/v1/registry/namespaces/{e.namespace}?schema_version={schema_version}",
        )
        for e in entries
    ]


@registry_router.get("/namespaces/{namespace}")
async def get_namespace_schema(
    namespace: str, schema_version: str = service.DEFAULT_VERSION
):
    entry = service.get_namespace(namespace, schema_version)
    if entry is None:
        raise HTTPException(
            status_code=404, detail=f"unknown registry namespace '{namespace}'"
        )
    return entry.schema


@registry_router.post("/validate", response_model=ValidateResponse)
async def validate(request: ValidateRequest):
    try:
        errors = service.validate_payload(
            request.namespace, request.payload, request.schema_version
        )
    except service.UnknownNamespaceError:
        raise HTTPException(
            status_code=404, detail=f"unknown registry namespace '{request.namespace}'"
        )
    return ValidateResponse(
        valid=not errors,
        namespace=request.namespace,
        schema_version=request.schema_version,
        errors=errors,
    )


@registry_router.get("/events")
async def list_event_registry():
    """Bloc 7 — Event Registry catalog (contract + implementation status per event)."""
    return service.event_registry()


# ---------------- INSTANCE STORE (P1: registry_objects) ----------------
# reports/08_NEXT_INTEGRATION.md item 2 / reports/FREKCORE_COMPLETION_BACKLOG.md
# P1 #7 — the persisted half of Bloc 1, closing every documented
# "PROPOSED, NOT IMPLEMENTED" resolver gap in docs/interfaces/*.md.


@registry_router.post("/objects/{namespace}", status_code=201)
async def create_registry_object(
    namespace: str,
    request: RegistryObjectCreateRequest,
    authorization: Optional[str] = Header(None),
    x_frek_session: Optional[str] = Header(None),
):
    """Persist a new instance in `namespace`, schema-validated before insert.

    Envelope fields not supplied by the caller are filled in: `frek_id`
    (generated, `frek-` prefix), `entity_type` (always the URL's namespace —
    a caller-supplied value is overridden, never trusted, since it would
    otherwise let a payload claim membership in a different namespace than
    the one it was validated and stored against), `status` ("draft"),
    `created_at` (now), `version` (1), `metadata` ({}).

    Authority: see `_authorize_write`. An OWNER-authority caller (holder
    session) can only create objects it owns — `owner_id`, if supplied,
    must equal the session's own frek_id; an ISSUER-authority caller
    (OAuth2 client) may set any `owner_id` (or none), matching how such
    clients already emit on behalf of arbitrary frek_ids elsewhere in this
    codebase (e.g. frek_v1's `emit`).
    """
    if service.get_namespace(namespace, request.schema_version) is None:
        raise HTTPException(404, f"unknown registry namespace '{namespace}'")

    authority, actor = await _authorize_write(authorization, x_frek_session)

    obj: Dict[str, Any] = dict(request.payload)
    obj.setdefault("frek_id", _generate_object_id())
    obj["entity_type"] = namespace
    obj.setdefault("status", "draft")
    obj.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    obj.setdefault("version", 1)
    obj.setdefault("metadata", {})

    if authority == "owner":
        if obj.get("owner_id") not in (None, actor):
            raise HTTPException(
                403,
                "owner_id doit correspondre a la session du titulaire, ou etre absent",
            )
        obj["owner_id"] = actor
    else:
        obj.setdefault("owner_id", None)

    errors = service.validate_payload(namespace, obj, request.schema_version)
    if errors:
        raise HTTPException(422, {"errors": errors})

    database = _require_db()
    existing = await database.registry_objects.find_one(
        {"namespace": namespace, "frek_id": obj["frek_id"]}, {"_id": 0, "frek_id": 1}
    )
    if existing:
        raise HTTPException(
            409, f"object '{obj['frek_id']}' already exists in namespace '{namespace}'"
        )

    doc = {
        **obj,
        "namespace": namespace,
        "schema_version": request.schema_version,
        "created_by": {"authority": authority, "actor": actor},
    }
    response_doc = dict(doc)
    await database.registry_objects.insert_one(doc)
    return response_doc


@registry_router.get("/objects/{namespace}")
async def list_registry_objects(
    namespace: str,
    schema_version: str = service.DEFAULT_VERSION,
    owner_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Public, no-auth read — matches this module's other catalog endpoints
    (`/namespaces`, `/validate`) and the read-only framing every
    `docs/interfaces/*.md` resolver already documents for this data."""
    if service.get_namespace(namespace, schema_version) is None:
        raise HTTPException(404, f"unknown registry namespace '{namespace}'")

    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    query: Dict[str, Any] = {"namespace": namespace}
    if owner_id is not None:
        query["owner_id"] = owner_id
    if status is not None:
        query["status"] = status

    database = _require_db()
    cursor = (
        database.registry_objects.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    objects = await cursor.to_list(limit)
    total = await database.registry_objects.count_documents(query)
    return {
        "namespace": namespace,
        "count": len(objects),
        "total": total,
        "objects": objects,
    }


@registry_router.get("/objects/{namespace}/{frek_id}")
async def get_registry_object(
    namespace: str, frek_id: str, schema_version: str = service.DEFAULT_VERSION
):
    """The resolver every `docs/interfaces/*.md` file names as
    "PROPOSED, NOT IMPLEMENTED" (e.g. KORA.md's
    `GET /registry/resolve/frek.artist/{frek_id}`) — same lookup, kept
    under `/objects` since it's the same resource. Public, no-auth."""
    if service.get_namespace(namespace, schema_version) is None:
        raise HTTPException(404, f"unknown registry namespace '{namespace}'")

    database = _require_db()
    doc = await database.registry_objects.find_one(
        {"namespace": namespace, "frek_id": frek_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(
            404, f"object '{frek_id}' not found in namespace '{namespace}'"
        )
    return doc
