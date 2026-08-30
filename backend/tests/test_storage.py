"""Unit tests for the Storage abstraction (Phase 2, Priority 13).

Real local disk I/O under pytest's tmp_path — no MongoDB, no live server,
no network.
"""

import hashlib
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from storage import LocalFilesystemStorageProvider  # noqa: E402

pytestmark = pytest.mark.unit


def test_put_then_get_round_trips(tmp_path):
    provider = LocalFilesystemStorageProvider(root=str(tmp_path))
    data = b"hello frekcore"

    stored = provider.put("moments/abc.bin", data, "application/octet-stream")
    assert stored.size == len(data)
    assert stored.sha256 == hashlib.sha256(data).hexdigest()

    got_data, got_content_type = provider.get("moments/abc.bin")
    assert got_data == data
    assert got_content_type == "application/octet-stream"


def test_exists(tmp_path):
    provider = LocalFilesystemStorageProvider(root=str(tmp_path))
    assert provider.exists("nope.bin") is False
    provider.put("nope.bin", b"x", "text/plain")
    assert provider.exists("nope.bin") is True


def test_get_missing_raises_file_not_found(tmp_path):
    provider = LocalFilesystemStorageProvider(root=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        provider.get("missing.bin")


def test_path_traversal_is_rejected(tmp_path):
    provider = LocalFilesystemStorageProvider(root=str(tmp_path))
    with pytest.raises(ValueError):
        provider.put("../escape.bin", b"x", "text/plain")


def test_two_providers_with_different_roots_are_isolated(tmp_path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    provider_a = LocalFilesystemStorageProvider(root=str(root_a))
    provider_b = LocalFilesystemStorageProvider(root=str(root_b))

    provider_a.put("x.bin", b"only in a", "text/plain")
    assert provider_a.exists("x.bin") is True
    assert provider_b.exists("x.bin") is False
