"""Unit tests for EmergentObjectStorageProvider (Phase 3, Priority 9).

Mocks `requests` — never calls the real integrations.emergentagent.com
service. Verifies the wire protocol matches backend/moment/storage.py's
real calls (same URL, same headers, same JSON shape).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from storage.emergent_object_storage import (  # noqa: E402
    EmergentObjectStorageProvider,
    ObjectStorageUnavailable,
    STORAGE_URL,
)

pytestmark = pytest.mark.unit


def test_is_available_false_without_key():
    provider = EmergentObjectStorageProvider(emergent_key=None)
    assert provider.is_available() is False


def test_put_raises_object_storage_unavailable_without_key():
    provider = EmergentObjectStorageProvider(emergent_key=None)
    with pytest.raises(ObjectStorageUnavailable):
        provider.put("frekcore/moments/id-x.jpg", b"data", "image/jpeg")


@patch("storage.emergent_object_storage.requests")
def test_put_matches_moment_storage_wire_protocol(mock_requests):
    init_resp = MagicMock()
    init_resp.json.return_value = {"storage_key": "sess-abc"}
    put_resp = MagicMock()
    put_resp.json.return_value = {"path": "frekcore/moments/id-x.jpg", "size": 4}
    mock_requests.post.return_value = init_resp
    mock_requests.put.return_value = put_resp

    provider = EmergentObjectStorageProvider(emergent_key="fake-key")
    result = provider.put("frekcore/moments/id-x.jpg", b"data", "image/jpeg")

    mock_requests.post.assert_called_once_with(
        f"{STORAGE_URL}/init", json={"emergent_key": "fake-key"}, timeout=30
    )
    mock_requests.put.assert_called_once_with(
        f"{STORAGE_URL}/objects/frekcore/moments/id-x.jpg",
        headers={"X-Storage-Key": "sess-abc", "Content-Type": "image/jpeg"},
        data=b"data",
        timeout=120,
    )
    assert result.path == "frekcore/moments/id-x.jpg"
    assert result.size == 4


@patch("storage.emergent_object_storage.requests")
def test_get_matches_moment_storage_wire_protocol(mock_requests):
    init_resp = MagicMock()
    init_resp.json.return_value = {"storage_key": "sess-abc"}
    get_resp = MagicMock()
    get_resp.content = b"payload"
    get_resp.headers = {"Content-Type": "audio/mpeg"}
    mock_requests.post.return_value = init_resp
    mock_requests.get.return_value = get_resp

    provider = EmergentObjectStorageProvider(emergent_key="fake-key")
    data, content_type = provider.get("frekcore/moments/id-x.mp3")

    mock_requests.get.assert_called_once_with(
        f"{STORAGE_URL}/objects/frekcore/moments/id-x.mp3",
        headers={"X-Storage-Key": "sess-abc"},
        timeout=60,
    )
    assert data == b"payload"
    assert content_type == "audio/mpeg"


def test_exists_raises_not_implemented_matching_real_api_limitation():
    provider = EmergentObjectStorageProvider(emergent_key="fake-key")
    with pytest.raises(NotImplementedError):
        provider.exists("frekcore/moments/id-x.jpg")


def test_session_key_is_cached_across_calls():
    provider = EmergentObjectStorageProvider(emergent_key="fake-key")
    with patch("storage.emergent_object_storage.requests") as mock_requests:
        init_resp = MagicMock()
        init_resp.json.return_value = {"storage_key": "sess-1"}
        mock_requests.post.return_value = init_resp

        provider._ensure_session()
        provider._ensure_session()

        mock_requests.post.assert_called_once()  # not called twice
