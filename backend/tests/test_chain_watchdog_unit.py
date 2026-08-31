"""notary/chain_watchdog.py — unit tests.

Historical P1 finding (memory/RESILIENCE_REPORT_v1.0.md, Sprint G, test 3
section 5.2 + section 7 P1#4): FrekChain.verify_chain() was only ever
invoked on demand; a corrupted block raised no alert unless someone
happened to call /notary/chain/verify. This file tests the watchdog in
isolation: a fake `chain` object with a scripted `verify_chain()` (no real
FrekChain/Mongo needed) and a recording stub for `record_anomaly`
(matching security/policies.py's real signature), verifying:
- a clean chain produces no anomaly;
- a corrupted chain (`valid: False`) produces exactly one
  `chain_integrity_violation` anomaly at `severity="critical"`, carrying
  the verify_chain() result (including first_invalid_height) in details;
- an exception from verify_chain() is caught, never propagates, and is
  itself reported as a `chain_watchdog_check_failed` critical anomaly;
- `watchdog_loop` calls `check_once` repeatedly, sleeping `interval_seconds`
  between iterations, and keeps running past a single failed iteration.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from notary.chain_watchdog import check_once, watchdog_loop  # noqa: E402

pytestmark = pytest.mark.unit


class _FakeChain:
    def __init__(self, results=None, raise_on=None):
        self._results = list(results or [])
        self._raise_on = raise_on or set()
        self.calls = 0

    async def verify_chain(self, limit=None):
        idx = self.calls
        self.calls += 1
        if idx in self._raise_on:
            raise RuntimeError("simulated verify_chain failure")
        return self._results[idx]


class _AnomalyRecorder:
    def __init__(self):
        self.calls = []

    async def __call__(self, kind, scope, severity="info", details=None):
        self.calls.append(
            {"kind": kind, "scope": scope, "severity": severity, "details": details}
        )


class TestCheckOnce:
    @pytest.mark.asyncio
    async def test_valid_chain_reports_no_anomaly(self):
        chain = _FakeChain(results=[{"valid": True, "blocks_checked": 42}])
        recorder = _AnomalyRecorder()
        result = await check_once(chain, recorder)
        assert result == {"valid": True, "blocks_checked": 42}
        assert recorder.calls == []

    @pytest.mark.asyncio
    async def test_invalid_chain_reports_critical_anomaly_with_details(self):
        bad_result = {
            "valid": False,
            "blocks_checked": 654,
            "first_invalid_height": 654,
            "reason": "block_hash_mismatch",
        }
        chain = _FakeChain(results=[bad_result])
        recorder = _AnomalyRecorder()
        result = await check_once(chain, recorder)
        assert result == bad_result
        assert len(recorder.calls) == 1
        anomaly = recorder.calls[0]
        assert anomaly["kind"] == "chain_integrity_violation"
        assert anomaly["scope"] == "frek_chain"
        assert anomaly["severity"] == "critical"
        assert anomaly["details"] == bad_result

    @pytest.mark.asyncio
    async def test_verify_chain_exception_is_caught_and_reported(self):
        chain = _FakeChain(results=[None], raise_on={0})
        recorder = _AnomalyRecorder()
        result = await check_once(chain, recorder)  # must not raise
        assert result["valid"] is False
        assert result["reason"] == "verify_chain_exception"
        assert len(recorder.calls) == 1
        anomaly = recorder.calls[0]
        assert anomaly["kind"] == "chain_watchdog_check_failed"
        assert anomaly["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_limit_forwarded_to_verify_chain(self):
        seen = {}

        class _Chain:
            async def verify_chain(self, limit=None):
                seen["limit"] = limit
                return {"valid": True, "blocks_checked": 0}

        recorder = _AnomalyRecorder()
        await check_once(_Chain(), recorder, limit=200)
        assert seen["limit"] == 200


class _StopLoop(Exception):
    """Sentinel used to break out of watchdog_loop's `while True` in tests."""


class TestWatchdogLoop:
    @pytest.mark.asyncio
    async def test_loop_runs_multiple_iterations_and_survives_a_failure(
        self, monkeypatch
    ):
        chain = _FakeChain(
            results=[
                {"valid": True, "blocks_checked": 1},
                None,  # this iteration raises
                {"valid": True, "blocks_checked": 3},
            ],
            raise_on={1},
        )
        recorder = _AnomalyRecorder()
        sleeps = []

        import notary.chain_watchdog as watchdog_module

        async def _fake_sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) >= len(chain._results):
                raise _StopLoop()

        monkeypatch.setattr(watchdog_module.asyncio, "sleep", _fake_sleep)

        with pytest.raises(_StopLoop):
            await watchdog_loop(chain, recorder, interval_seconds=99)

        assert chain.calls == len(chain._results)
        assert sleeps == [99, 99, 99]
        # One critical anomaly for the exception iteration; none for the two OKs.
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["kind"] == "chain_watchdog_check_failed"
