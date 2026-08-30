"""FREK Registry — service (Bloc 1).

Charge les JSON Schemas versionnes de chaque namespace FREK depuis
backend/registry/schemas/<version>/ et expose list / get / validate.

Aucune base de donnees requise : le Registry est un catalogue de contrats
(Registry family, Bloc 8 / Phase 7), pas un store d'instances.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

SCHEMAS_ROOT = Path(__file__).parent / "schemas"
EVENTS_ROOT = Path(__file__).parent / "events"
BASE_SCHEMA_FILENAME = "_base.schema.json"
DEFAULT_VERSION = "v1"


class UnknownNamespaceError(KeyError):
    """Raised when a namespace/version pair is not present in the registry."""


@dataclass(frozen=True)
class RegistryEntry:
    namespace: str
    version: str
    title: str
    description: str
    schema: Dict[str, Any]


def available_schema_versions() -> List[str]:
    if not SCHEMAS_ROOT.exists():
        return []
    return sorted(p.name for p in SCHEMAS_ROOT.iterdir() if p.is_dir())


def _load_raw(version: str, filename: str) -> Dict[str, Any]:
    path = SCHEMAS_ROOT / version / filename
    if not path.exists():
        raise FileNotFoundError(f"registry schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_base_refs(schema: Dict[str, Any], base_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Inline the shared `_base.schema.json` $ref.

    Every namespace schema declares `allOf: [{"$ref": "_base.schema.json"}, {...}]`.
    Inlining avoids needing an external $ref resolver registered with jsonschema.
    """
    resolved = copy.deepcopy(schema)
    all_of = resolved.get("allOf")
    if isinstance(all_of, list):
        resolved["allOf"] = [
            copy.deepcopy(base_schema) if item.get("$ref") == BASE_SCHEMA_FILENAME else item
            for item in all_of
        ]
    return resolved


@lru_cache(maxsize=None)
def _namespaces_for_version(version: str) -> Dict[str, RegistryEntry]:
    base_schema = _load_raw(version, BASE_SCHEMA_FILENAME)
    entries: Dict[str, RegistryEntry] = {}
    version_dir = SCHEMAS_ROOT / version
    for path in sorted(version_dir.glob("*.schema.json")):
        if path.name == BASE_SCHEMA_FILENAME:
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        namespace = raw.get("x-frek-namespace") or path.stem.replace(".schema", "")
        resolved = _resolve_base_refs(raw, base_schema)
        Draft202012Validator.check_schema(resolved)
        entries[namespace] = RegistryEntry(
            namespace=namespace,
            version=raw.get("x-frek-schema-version", "1.0.0"),
            title=raw.get("title", namespace),
            description=raw.get("description", ""),
            schema=resolved,
        )
    return entries


def list_namespaces(version: str = DEFAULT_VERSION) -> List[RegistryEntry]:
    return sorted(_namespaces_for_version(version).values(), key=lambda e: e.namespace)


def get_namespace(namespace: str, version: str = DEFAULT_VERSION) -> Optional[RegistryEntry]:
    return _namespaces_for_version(version).get(namespace)


def validate_payload(namespace: str, payload: Dict[str, Any], version: str = DEFAULT_VERSION) -> List[str]:
    """Valide `payload` contre le schema du namespace.

    Retourne une liste d'erreurs lisibles (vide = valide).
    Leve UnknownNamespaceError si le couple namespace/version n'existe pas.
    """
    entry = get_namespace(namespace, version)
    if entry is None:
        raise UnknownNamespaceError(f"unknown registry namespace '{namespace}' (version={version})")
    validator = Draft202012Validator(entry.schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    return [f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in errors]


@lru_cache(maxsize=1)
def event_registry() -> Dict[str, Any]:
    """Catalogue Bloc 7 (Event Registry) — voir backend/registry/events/event_registry.json."""
    path = EVENTS_ROOT / "event_registry.json"
    return json.loads(path.read_text(encoding="utf-8"))
