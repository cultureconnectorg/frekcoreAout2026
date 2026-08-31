"""Reconciliation checks: backend/registry/fk_taxonomy.py against the two
real, independent source-of-truth lists it maps between — .fk's
OBJECT_TYPES (backend/fk/models.py) and frek.work's `work_type` enum
(backend/registry/schemas/v1/frek.work.schema.json). No live server, no
MongoDB — pure Python + on-disk JSON Schema.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fk.models import OBJECT_TYPES  # noqa: E402
from registry import fk_taxonomy  # noqa: E402
from registry import service as registry_service  # noqa: E402

pytestmark = pytest.mark.unit


def _frek_work_type_enum():
    entry = registry_service.get_namespace("frek.work")
    props = entry.schema["allOf"][1]["properties"]
    return props["work_type"]["enum"]


def test_frek_work_type_enum_is_an_exact_mirror_of_fk_object_types():
    """The empirical proof behind fk_taxonomy.py's module docstring claim:
    frek.work.work_type's enum is not just "similar to" but IDENTICAL to
    .fk's OBJECT_TYPES — same values, same set. If this ever drifts (either
    file edited without the other), this test catches it immediately."""
    assert set(_frek_work_type_enum()) == set(OBJECT_TYPES)


@pytest.mark.parametrize("object_type", OBJECT_TYPES)
def test_every_fk_object_type_has_a_generic_namespace_target(object_type):
    namespaces = fk_taxonomy.registry_namespaces_for_fk_object_type(object_type)
    assert fk_taxonomy.GENERIC_NAMESPACE in namespaces


def test_generic_namespace_is_always_first():
    for object_type in OBJECT_TYPES:
        namespaces = fk_taxonomy.registry_namespaces_for_fk_object_type(object_type)
        assert namespaces[0] == fk_taxonomy.GENERIC_NAMESPACE


@pytest.mark.parametrize(
    "object_type,expected_specific",
    [("song", "frek.track"), ("album", "frek.album"), ("event", "frek.event")],
)
def test_song_album_event_also_get_their_specific_namespace(
    object_type, expected_specific
):
    namespaces = fk_taxonomy.registry_namespaces_for_fk_object_type(object_type)
    assert expected_specific in namespaces
    assert len(namespaces) == 2


@pytest.mark.parametrize(
    "object_type", ["heritage", "photo", "captation", "document", "artwork", "other"]
)
def test_the_remaining_object_types_get_only_the_generic_namespace(object_type):
    namespaces = fk_taxonomy.registry_namespaces_for_fk_object_type(object_type)
    assert namespaces == [fk_taxonomy.GENERIC_NAMESPACE]


def test_every_specific_namespace_target_actually_exists_in_the_registry():
    """Guards against fk_taxonomy.py naming a namespace that doesn't (or no
    longer) exists as a real schema file."""
    for namespace in fk_taxonomy.FK_OBJECT_TYPE_TO_SPECIFIC_NAMESPACE.values():
        assert registry_service.get_namespace(namespace) is not None, namespace
    assert registry_service.get_namespace(fk_taxonomy.GENERIC_NAMESPACE) is not None


class TestBuildFrekWorkMirror:
    def test_shapes_the_namespace_specific_fields_only(self):
        mirror = fk_taxonomy.build_frek_work_mirror(
            frek_id="id-abc123def456-0001", title="Test Song", object_type="song"
        )
        assert mirror == {
            "title": "Test Song",
            "work_type": "song",
            "fk_object_ref": "id-abc123def456-0001",
        }

    def test_explicit_fk_object_ref_overrides_the_default(self):
        mirror = fk_taxonomy.build_frek_work_mirror(
            frek_id="id-abc123def456-0001",
            title="X",
            object_type="other",
            fk_object_ref="frek-different-ref",
        )
        assert mirror["fk_object_ref"] == "frek-different-ref"

    def test_output_validates_against_the_real_frek_work_schema(self):
        """Not just shape-correct by eye — actually schema-valid, base
        envelope fields merged in the same way registry/routes.py's
        create_registry_object fills them."""
        mirror = fk_taxonomy.build_frek_work_mirror(
            frek_id="id-abc123def456-0001", title="Test Artwork", object_type="artwork"
        )
        full_object = {
            **mirror,
            "frek_id": "frek-abcdef012345-0001",
            "entity_type": "frek.work",
            "status": "draft",
            "created_at": "2026-08-31T00:00:00+00:00",
            "version": 1,
            "metadata": {},
        }
        errors = registry_service.validate_payload("frek.work", full_object)
        assert errors == []
