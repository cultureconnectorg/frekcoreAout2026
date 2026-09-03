"""content_binding/extraction.py -- unit tests for the pure functions
(exact_hash, compute_signal_fingerprint's wiring/guards), independent of
whether librosa/soundfile are actually installed (they are not in
requirements-ci.txt -- see reports/FREKCORE_D1_VALIDATION_EVIDENCE.md for
the separate, real-librosa validation pass this module's NaN guard was
written in direct response to).
"""

import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from content_binding.extraction import (  # noqa: E402
    FingerprintExtractionError,
    compute_signal_fingerprint,
    exact_hash,
)

pytestmark = pytest.mark.unit


class TestExactHash:
    def test_matches_hashlib_directly(self):
        data = b"some audio bytes"
        assert exact_hash(data) == hashlib.sha256(data).hexdigest()

    def test_different_content_different_hash(self):
        assert exact_hash(b"A") != exact_hash(b"B")

    def test_deterministic(self):
        data = b"same content twice"
        assert exact_hash(data) == exact_hash(data)


class TestComputeSignalFingerprint:
    @pytest.fixture(autouse=True)
    def _patch_node01(self, monkeypatch):
        """Isolates this file from the real librosa/soundfile-backed
        node01 entirely -- these tests exercise compute_signal_fingerprint's
        own wiring and guards, not the DSP algorithm."""
        self._fake_module = SimpleNamespace(node01=SimpleNamespace())
        monkeypatch.setitem(
            sys.modules, "frek.nodes.node01_extraction", self._fake_module
        )

    async def test_wraps_extraction_exception(self):
        async def _boom(audio_bytes):
            raise RuntimeError("libsndfile: file contains data in an unknown format")

        self._fake_module.node01.extract_from_bytes = _boom
        with pytest.raises(FingerprintExtractionError):
            await compute_signal_fingerprint(b"not really audio")

    async def test_rejects_non_finite_vector(self):
        """The real finding from this state's validation pass
        (reports/FREKCORE_D1_VALIDATION_EVIDENCE.md item J): a too-short
        clip makes node01's own MFCC/flux math divide-by-zero into NaN
        instead of raising. This guard turns that into a safe 400
        upstream instead of a silently-stored, structurally-useless
        fingerprint."""
        vector = np.zeros(528, dtype=np.float32)
        vector[10] = np.nan

        async def _nan_result(audio_bytes):
            return SimpleNamespace(vector_528d=vector, sample_rate=44100, duration=0.01)

        self._fake_module.node01.extract_from_bytes = _nan_result
        with pytest.raises(FingerprintExtractionError, match="non-finite"):
            await compute_signal_fingerprint(b"short clip bytes")

    async def test_rejects_infinite_vector(self):
        vector = np.ones(528, dtype=np.float32)
        vector[0] = np.inf

        async def _inf_result(audio_bytes):
            return SimpleNamespace(vector_528d=vector, sample_rate=44100, duration=1.0)

        self._fake_module.node01.extract_from_bytes = _inf_result
        with pytest.raises(FingerprintExtractionError, match="non-finite"):
            await compute_signal_fingerprint(b"clip bytes")

    async def test_accepts_finite_vector(self):
        vector = np.linspace(-1, 1, 528, dtype=np.float32)

        async def _ok_result(audio_bytes):
            return SimpleNamespace(vector_528d=vector, sample_rate=44100, duration=2.0)

        self._fake_module.node01.extract_from_bytes = _ok_result
        result = await compute_signal_fingerprint(b"a real-length clip")
        assert result.dimensions == 528
        assert result.sample_rate == 44100
        assert result.duration_seconds == 2.0
        assert len(result.vector) == 528
