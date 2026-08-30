"""FREK Registry — API REST (Bloc 1, famille "Registry" du Bloc 8 / Phase 7).

Routeur additif, sans etat, sans dependance MongoDB : aucun `set_db` requis,
contrairement aux autres modules du backend.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import service

registry_router = APIRouter(prefix="/registry", tags=["FREK Registry"])


class NamespaceSummary(BaseModel):
    namespace: str
    version: str
    title: str
    description: str
    schema_url: str


class ValidateRequest(BaseModel):
    namespace: str = Field(..., description="Namespace FREK Registry, ex: 'frek.artist'.")
    payload: Dict[str, Any]
    schema_version: str = Field(default=service.DEFAULT_VERSION, description="Version du schema, ex: 'v1'.")


class ValidateResponse(BaseModel):
    valid: bool
    namespace: str
    schema_version: str
    errors: List[str] = Field(default_factory=list)


@registry_router.get("/versions")
async def list_versions():
    return {"versions": service.available_schema_versions(), "default": service.DEFAULT_VERSION}


@registry_router.get("/namespaces", response_model=List[NamespaceSummary])
async def list_namespaces(schema_version: str = service.DEFAULT_VERSION):
    try:
        entries = service.list_namespaces(schema_version)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"unknown registry schema version '{schema_version}'")
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
async def get_namespace_schema(namespace: str, schema_version: str = service.DEFAULT_VERSION):
    entry = service.get_namespace(namespace, schema_version)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown registry namespace '{namespace}'")
    return entry.schema


@registry_router.post("/validate", response_model=ValidateResponse)
async def validate(request: ValidateRequest):
    try:
        errors = service.validate_payload(request.namespace, request.payload, request.schema_version)
    except service.UnknownNamespaceError:
        raise HTTPException(status_code=404, detail=f"unknown registry namespace '{request.namespace}'")
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
