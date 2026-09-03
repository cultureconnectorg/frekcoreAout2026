"""D1 — the two content-binding computations, kept pure (no I/O, no
storage, no FastAPI) so they are trivially unit-testable and so
`routes.py` cannot accidentally couple algorithm logic to persistence.

`exact_hash()` is a one-line SHA-256 — no scientific claim needed, it is
a standard cryptographic primitive.

`compute_signal_fingerprint()` REUSES `backend/frek/nodes/node01_extraction
.py`'s real, working 6-algorithm pipeline verbatim (FFT/RMS/ZCR/MFCC/
centroid/flux -> 528D vector) rather than reimplementing it — per the
founder's explicit REUSE_EXISTING_PRIMITIVES_FIRST instruction and the
reconciliation report's own point 10 ("node01_extraction.py's 6-algorithm
extraction pipeline is real, self-contained signal-processing code with
no storage dependency -- directly reusable as the extraction step").
`backend/frek/` itself is NOT modified by this module.

IMPORTANT — what this file does NOT claim: no property of the resulting
vector (robustness to compression/noise/gain/re-recording, collision
rate, perceptual uniqueness) is asserted here. See
reports/FREKCORE_D1_VALIDATION_EVIDENCE.md for exactly what was tested,
on what fixtures, with what result, and NOT_TESTED for the rest. Per the
founder's explicit rule: UNKNOWN never silently becomes TRUE, and this
module never uses the words "infalsifiable" or "irrefutable".
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from .models import (
    EXACT_HASH_ALGORITHM_ID,
    SIGNAL_ALGORITHM_ID,
    SIGNAL_ALGORITHM_VERSION,
    SignalFingerprintData,
)

if TYPE_CHECKING:
    pass


def exact_hash(raw_bytes: bytes) -> str:
    """SHA-256 hex digest over the raw content bytes — the exact-integrity
    axis. Identical convention to `.fk`'s `MediaItem.sha256` and every
    other hash in this codebase; not a new primitive."""
    return hashlib.sha256(raw_bytes).hexdigest()


class FingerprintExtractionError(Exception):
    """Raised when the underlying signal-processing pipeline cannot
    produce a fingerprint (malformed/unreadable audio, unsupported
    format, too short). Callers turn this into a 400, never a 500 —
    'fail safely on malformed input' per the D1 mission's validation
    matrix item J."""


async def compute_signal_fingerprint(audio_bytes: bytes) -> SignalFingerprintData:
    """Extract the 528D perceptual/signal vector from raw audio bytes.

    Delegates to `frek.nodes.node01_extraction.node01` — the real,
    pre-existing, storage-free extraction engine. That module lazy-
    imports `librosa`/`soundfile` only inside this call, exactly as it
    already did for the historical `/certify` routes; nothing about that
    dependency boundary changes here.
    """
    from frek.nodes.node01_extraction import node01

    try:
        result = await node01.extract_from_bytes(audio_bytes)
    except FingerprintExtractionError:
        raise
    except Exception as e:
        raise FingerprintExtractionError(f"signal extraction failed: {e}") from e

    # Real finding from this state's validation pass
    # (reports/FREKCORE_D1_VALIDATION_EVIDENCE.md, item J): an audio clip
    # short enough that a spectral window has no samples to average over
    # produces a silent NaN in node01's own MFCC/flux computation instead
    # of raising -- confirmed against real librosa, not hypothetical.
    # `content_binding/routes.py`'s MIN_AUDIO_BYTES floor happens to
    # reject the specific case found (a ~926-byte clip), but that is a
    # byte-size proxy for duration, not a guarantee across every sample
    # rate/format -- fail safely here too, explicitly, rather than
    # persisting a fingerprint no comparison could ever trust.
    import math

    vector = result.vector_528d.tolist()
    if not all(math.isfinite(x) for x in vector):
        raise FingerprintExtractionError(
            "extraction produced a non-finite value (NaN/inf) -- input audio "
            "is likely too short or silent for a stable fingerprint"
        )

    return SignalFingerprintData(
        algorithm=SIGNAL_ALGORITHM_ID,
        algorithm_version=SIGNAL_ALGORITHM_VERSION,
        dimensions=len(vector),
        vector=[float(x) for x in vector],
        sample_rate=result.sample_rate,
        duration_seconds=round(result.duration, 3),
    )


__all__ = [
    "exact_hash",
    "compute_signal_fingerprint",
    "FingerprintExtractionError",
    "EXACT_HASH_ALGORITHM_ID",
]
