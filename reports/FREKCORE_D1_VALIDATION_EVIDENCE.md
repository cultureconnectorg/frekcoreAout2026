# FREKCORE — D1 Signal Fingerprint: Validation Evidence

Founder decision D1 (`reports/FREKCORE_HISTORICAL_CAPABILITY_RECONCILIATION.md`
§D, §Phase C/Validation Matrix): no property of the historical signal-
fingerprint algorithm may be asserted without evidence. This document
records exactly what was tested, on what fixtures, with what result — no
marketing interpretation, `UNKNOWN` stays `UNKNOWN` where it applies.

## 0. What ran, and where

`backend/content_binding/extraction.py:compute_signal_fingerprint()`
delegates to `backend/frek/nodes/node01_extraction.py`'s real 6-algorithm
pipeline (FFT/RMS/ZCR/MFCC/centroid/flux → 528D vector) **unmodified** —
this validation exercises that same, real algorithm, not a reimplementation.

**Environment note**: `librosa`/`soundfile` are not in
`requirements-ci.txt` (heavy native-code dependencies — `numba`, `scipy`,
`llvmlite`; adding them to the CI-blocking dependency set was judged out
of this state's scope, a decision for whoever owns CI cost/time budgets
next, not assumed here). They **are** available in this sandbox (`pip
install librosa soundfile` succeeded, network access for PyPI works here
even though Docker/MongoDB pulls do not) — this pass installed them
once, ran the validation script below directly against the real
algorithm, and records the results. CI's blocking unit tests
(`backend/tests/test_content_binding_unit.py`,
`test_content_binding_extraction_unit.py`) monkeypatch extraction out
entirely and test the surrounding logic (identity separation, hashing,
persistence, auth, idempotency, D6 semantics) — this document is the
DSP-algorithm evidence those tests deliberately do not attempt.

**Fixtures**: synthetic PCM16 WAV tones generated with `numpy`/
`soundfile` (a 440Hz fundamental + a quieter second harmonic, 2 seconds,
44100Hz) — not real-world recorded audio, not real musical content, not
real-recording-device noise. This is a real but narrow test surface;
see §4 for what remains genuinely untested.

Script: `d1_validation.py` (run manually this pass, not committed to the
repo — a one-off validation script, not a maintained test; its exact
commands are reproducible from this document's own descriptions if a
future pass wants to re-run or extend it).

## 1. Evidence table

| Property | Test | Fixture | Result | Status |
|---|---|---|---|---|
| Determinism (same input → same output) | Extract twice from identical bytes, compare vectors | 440Hz tone, 2s | max absolute difference across all 528 dimensions = **0.0** | **DEMONSTRATED** |
| Exact byte-identical match | SHA-256 over two separately-encoded-but-identical-sample WAV files | 440Hz tone, re-encoded twice from the same float array | SHA-256 hashes **matched**; cosine similarity = **1.0000** | **DEMONSTRATED** (for the exact-hash axis; expected and trivial — SHA-256 is deterministic by construction) |
| Fingerprint match on the *same signal, different container encoding* | Same float samples written as PCM16 vs. PCM24 | 440Hz tone | SHA-256 **differed** (different bytes, as expected — exact_hash is not claimed to survive this); signal fingerprint cosine similarity = **1.0000** | **DEMONSTRATED** — narrow: same in-memory samples, different bit-depth container only, not real transcoding |
| Robustness to a lossless-style round-trip (resample 44.1k→48k→44.1k) | `librosa.resample` round-trip on a pure tone | 440Hz tone | cosine similarity = **1.0000** | **PARTIALLY_DEMONSTRATED** — one narrow synthetic case (a pure sine + harmonic); NOT tested against real lossless codecs (FLAC/ALAC) or real musical content with transients/percussion, where resampling artifacts behave differently |
| Robustness to gain change | ±6dB gain applied directly to samples | 440Hz tone | cosine similarity = **0.9788 (+6dB)**, **0.9942 (−6dB)** | **PARTIALLY_DEMONSTRATED** — high similarity but not exact-invariant; only 2 gain levels tested, not a sweep, not clipping behavior at extreme gain |
| Robustness to additive noise | Gaussian noise, std 0.01 and 0.05, added to samples | 440Hz tone | cosine similarity = **0.9948 (std 0.01)**, **0.9718 (std 0.05)** | **PARTIALLY_DEMONSTRATED** — only 2 low noise levels tested on a synthetic tone; no real-world recording noise (room tone, mic self-noise, compression artifacts) tested |
| Robustness to lossy compression (MP3/AAC/Opus) | — | — | Not run — no codec encoder available/installed in this pass | **NOT_TESTED** |
| Robustness to re-recording (mic capture of a played-back signal) | — | — | Not run — requires physical playback/capture hardware this sandbox does not have | **NOT_TESTED** |
| False-positive discrimination (different content → low similarity) | Two different-frequency tones (880Hz, 220Hz) compared against the 440Hz base | Synthetic tones | cosine similarity = **0.4701** and **0.5168** — clearly separated from the ~0.97–1.0 range same-content variants scored, but **not near zero** | **PARTIALLY_DEMONSTRATED** — the algorithm discriminates on this narrow 3-tone set; the 0.45–0.55 range for "clearly different" synthetic tones is a real data point against ever treating similarity as binary, but this is nowhere near a rigorous false-positive-rate study (needs a real corpus of unrelated recordings, not 2 pure tones) |
| Collision resistance (two different real-world contents producing near-identical fingerprints) | — | — | Not run — needs a real audio corpus, not synthetic tones | **NOT_TESTED** |
| Perceptual uniqueness across genres/instrumentation | — | — | Not run | **NOT_TESTED** |
| Fails safely on malformed input | Extraction called on 27 bytes of non-audio garbage | Arbitrary non-WAV bytes | Raised `LibsndfileError` inside `node01`, caught and re-raised as `content_binding.extraction.FingerprintExtractionError` by this pass's own wrapping | **DEMONSTRATED** |
| Fails safely on too-short input | Extraction called on a 10ms (926-byte) WAV clip | 440Hz tone, 10ms | **Did not raise** — `node01`'s own MFCC/flux computation produced a `NaN` (confirmed: `numpy` `RuntimeWarning: Mean of empty slice` / `invalid value encountered in scalar divide`) instead of an error | **A REAL GAP, FOUND AND CLOSED THIS PASS** — see §2 |

## 2. A real finding, fixed during this validation pass

The "too-short input" result above is not a documentation footnote — it
is a genuine defect this pass found via real testing (not assumed, not
theoretical) and closed:

- **Before**: `compute_signal_fingerprint()` returned whatever `node01`
  computed, unchecked. A short-enough clip silently produced a vector
  containing `NaN`, which would have been stored, notarized, and served
  back as if it were a valid fingerprint — a `NaN`-poisoned fingerprint
  is meaningless for any future comparison, silently.
- **Fix** (`content_binding/extraction.py`): after extraction, every
  value in the 528-dimension vector is checked with `math.isfinite()`;
  a `NaN`/`inf` anywhere raises `FingerprintExtractionError`, which
  `content_binding/routes.py` turns into an HTTP 400 (`"Audio illisible"`)
  — the same fail-safely contract as malformed input, not a 500.
- **Verified twice**: (1) a mocked unit test
  (`tests/test_content_binding_extraction_unit.py::TestComputeSignalFingerprint
  ::test_rejects_non_finite_vector`, no librosa needed, CI-blocking) proves
  the guard logic; (2) re-running the exact 926-byte fixture that
  originally slipped through, this time through the real
  `compute_signal_fingerprint()` with real librosa installed, confirms it
  is now correctly rejected end-to-end (this pass's own manual
  reproduction, not asserted from the unit test alone).
- **Why `MIN_AUDIO_BYTES = 1000` in `routes.py` does not make this
  guard redundant**: that floor is a byte-size proxy for duration and
  happens to reject this specific 926-byte fixture, but byte size does
  not uniquely determine duration across sample rates/bit-depths/channel
  counts — the finite-value guard is the actual, algorithm-level
  correctness check; the byte floor is a cheap, separate DoS-shaped
  bound (payload size), not a substitute for it.

## 3. What this evidence supports saying about D1 — and what it does not

**Supported** (DEMONSTRATED or PARTIALLY_DEMONSTRATED above):
- The algorithm is deterministic on identical input.
- It correctly distinguishes exact-byte-identical content (trivially,
  via SHA-256) from perceptually-similar-but-differently-encoded content
  (via the signal fingerprint).
- On narrow synthetic fixtures, it shows meaningfully higher similarity
  for the same underlying signal under gain/noise/resample perturbation
  (~0.97–1.0) than for genuinely different content (~0.45–0.55).
- It fails safely (raises, does not silently corrupt) on both malformed
  and too-short input, the latter closed by this pass's own fix.

**Explicitly NOT supported, and not claimed anywhere in this codebase**:
- "Robust to lossy compression" — NOT_TESTED, no codec tooling run.
- "Robust to re-recording/microphone capture" — NOT_TESTED, no hardware.
- Any collision-rate or false-positive-rate number — the 0.45–0.55
  separation observed is 2 data points on synthetic tones, not a
  statistically meaningful rate over a real corpus.
- The words **"infalsifiable"** or **"irrefutable"** — the historical
  `/certify` PDF certificate used exactly this language
  (`backend/frek/routes.py:get_certificat_pdf`, unchanged, still live);
  this document and `content_binding/`'s own code deliberately never use
  either word, per the founder's explicit `NO_OVERCLAIM_RULE`.

## 4. Recommended follow-up (not executed this pass — out of D1's scope)

- A real-audio-corpus false-positive/collision study (needs licensed or
  public-domain recordings, not synthetic tones).
- Lossy-codec robustness testing (needs `ffmpeg`/`lame` or similar,
  not installed/verified available in any environment this session has
  had access to).
- Re-recording robustness (needs physical playback/capture, or a
  simulated room-impulse-response + mic-noise model as a proxy).
- A decision on whether `librosa`/`soundfile` should move from
  `backend/requirements.txt`-only into `requirements-ci.txt`, so this
  validation could run as a real (slower) CI-blocking or scheduled job
  instead of a manual one-off — a CI-cost/time tradeoff for whoever owns
  that budget, not decided here.
