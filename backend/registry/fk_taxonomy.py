"""Reconciliation: `.fk`'s `object_type` taxonomy <-> FREK Registry namespaces.

P1 backlog item (`reports/FREKCORE_MASTER_REQUIREMENTS_MATRIX.md`, FREK
Registry section: "Reconciliation with historical object types" — was
**PARTIAL**). Full write-up: `docs/architecture/FK_OBJECT_TAXONOMY_RECONCILIATION.md`.

Pure, additive, no side effects: nothing in `backend/fk/` or
`backend/registry/routes.py` calls this module. It exists so a future
caller (a "publish this .fk to the Registry" endpoint, a backfill script,
step 3's `object.created` event payload) has one correct, tested mapping
to use instead of re-deriving it — and so this reconciliation is a checked
fact, not just a claim in a report. Does not change `.fk`'s or the
Registry's existing behavior in any way.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# `.fk`'s OBJECT_TYPES (backend/fk/models.py) that also have a namespace of
# their own for domain-specific consumers, beyond the always-available
# generic `frek.work` mirror — see the module docstring above.
FK_OBJECT_TYPE_TO_SPECIFIC_NAMESPACE: Dict[str, str] = {
    "song": "frek.track",
    "album": "frek.album",
    "event": "frek.event",
}

# frek.work.schema.json's own docstring: "superset de track/album/artwork/
# document — miroir registry de backend/fk/models.py OBJECT_TYPES." Its
# `work_type` enum is a deliberate, exact copy of `.fk`'s OBJECT_TYPES —
# verified, not just asserted, by
# backend/tests/test_registry_fk_taxonomy.py.
GENERIC_NAMESPACE = "frek.work"


def registry_namespaces_for_fk_object_type(object_type: str) -> List[str]:
    """Every Registry namespace a `.fk` object of this `object_type` could
    be mirrored into. `frek.work` (generic, `work_type=object_type`) is
    always a valid target — every `.fk` `object_type` value is also a
    valid `frek.work.work_type` value, by construction. `song`/`album`/
    `event` additionally have a specific namespace for consumers that only
    care about that shape (KORA for track/album, event listings for
    event) — `heritage`/`photo`/`captation`/`document`/`artwork`/`other`
    have no dedicated namespace and mirror to `frek.work` only.
    """
    namespaces = [GENERIC_NAMESPACE]
    specific = FK_OBJECT_TYPE_TO_SPECIFIC_NAMESPACE.get(object_type)
    if specific:
        namespaces.append(specific)
    return namespaces


def build_frek_work_mirror(
    *, frek_id: str, title: str, object_type: str, fk_object_ref: Optional[str] = None
) -> Dict[str, Any]:
    """Shape (never persist — the caller decides whether/when to actually
    `POST /api/v1/registry/objects/frek.work`) the namespace-specific
    payload for a `frek.work` mirror of a `.fk` object.

    `fk_object_ref` defaults to `frek_id` itself (the `.fk`'s own FREK-ID)
    when not given — `frek.work.schema.json`'s own field for "Reference to
    the FK container (.fk) proving this work, if any."

    Returns the `payload` half only, matching
    `registry/routes.RegistryObjectCreateRequest`'s own contract (base
    envelope fields — `frek_id`, `entity_type`, `status`, `created_at` —
    are filled in server-side by `create_registry_object`, not here; the
    mirror's own Registry `frek_id` is intentionally left for the server to
    generate, distinct from the `.fk`'s `frek_id`, which lives in
    `fk_object_ref` instead — the two are related objects, not the same
    object under two names).
    """
    return {
        "title": title,
        "work_type": object_type,
        "fk_object_ref": fk_object_ref or frek_id,
    }
