"""Regression test for notary/anchor.py's `_CalendarCircuitBreaker`.

Root cause this guards against (reports/16_INTEGRATION_TEST_BASELINE.md,
Priority 3): OTSAnchor.submit_block() looped over all 5 DEFAULT_CALENDARS
on every call with no memory of prior failures. In an environment where
every calendar is unreachable (this sandbox's network policy: immediate
403 Forbidden on all five), every identity emission and every
`/anchor/sweep` call paid the full cost of 5 blocking `asyncio.to_thread`
round trips, run from a FastAPI background task on every single identity
creation across the test suite. That saturated the shared thread pool
and produced widespread ConnectionError/TimeoutError/JSONDecodeError on
unrelated concurrent requests (evidenced in the mongomock integration run
log — 89 errors and 50 failures, many with no relation to notary/anchor
at all).

This test exercises only the breaker's pure state machine — no network,
no asyncio, no database — so it is fast and unconditionally runnable in
CI regardless of network policy.
"""

import unittest

import pytest

from notary.anchor import _CalendarCircuitBreaker

pytestmark = pytest.mark.unit


class TestCalendarCircuitBreaker(unittest.TestCase):
    URL = "https://example.invalid/calendar"

    def test_starts_closed(self):
        breaker = _CalendarCircuitBreaker(threshold=3, cooldown_seconds=60)
        self.assertFalse(breaker.is_open(self.URL))

    def test_stays_closed_below_threshold(self):
        breaker = _CalendarCircuitBreaker(threshold=3, cooldown_seconds=60)
        breaker.record_failure(self.URL, now=0.0)
        breaker.record_failure(self.URL, now=1.0)
        self.assertFalse(breaker.is_open(self.URL, now=2.0))

    def test_opens_at_threshold(self):
        breaker = _CalendarCircuitBreaker(threshold=3, cooldown_seconds=60)
        breaker.record_failure(self.URL, now=0.0)
        breaker.record_failure(self.URL, now=1.0)
        breaker.record_failure(self.URL, now=2.0)
        self.assertTrue(breaker.is_open(self.URL, now=2.5))

    def test_stays_open_within_cooldown(self):
        breaker = _CalendarCircuitBreaker(threshold=2, cooldown_seconds=60)
        breaker.record_failure(self.URL, now=0.0)
        breaker.record_failure(self.URL, now=1.0)
        self.assertTrue(breaker.is_open(self.URL, now=30.0))
        self.assertTrue(breaker.is_open(self.URL, now=60.9))

    def test_half_opens_after_cooldown(self):
        breaker = _CalendarCircuitBreaker(threshold=2, cooldown_seconds=60)
        breaker.record_failure(self.URL, now=0.0)
        breaker.record_failure(self.URL, now=1.0)
        self.assertTrue(breaker.is_open(self.URL, now=30.0))
        # Cooldown elapsed (disabled_until = 1.0 + 60 = 61.0): the next
        # check must let a call through again.
        self.assertFalse(breaker.is_open(self.URL, now=61.0))

    def test_success_resets_failure_count(self):
        breaker = _CalendarCircuitBreaker(threshold=3, cooldown_seconds=60)
        breaker.record_failure(self.URL, now=0.0)
        breaker.record_failure(self.URL, now=1.0)
        breaker.record_success(self.URL)
        breaker.record_failure(self.URL, now=2.0)
        # Only 1 consecutive failure since the success reset the count.
        self.assertFalse(breaker.is_open(self.URL, now=2.5))

    def test_breaker_is_per_calendar(self):
        breaker = _CalendarCircuitBreaker(threshold=1, cooldown_seconds=60)
        breaker.record_failure("https://a.invalid", now=0.0)
        self.assertTrue(breaker.is_open("https://a.invalid", now=0.5))
        self.assertFalse(breaker.is_open("https://b.invalid", now=0.5))


if __name__ == "__main__":
    unittest.main()
