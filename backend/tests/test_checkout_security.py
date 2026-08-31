"""FREK Payments (Stripe checkout) — P0 security review regression
(docs/decisions/0001-founder-decisions-2026-08-31.md).

POST /api/v1/checkout is deliberately left reachable without a credential —
CC2026 participants have no account/session system, so authenticating this
route would break the real self-service top-up flow. The documented residual
risk (low-entropy, guessable badge_id) is mitigated with a per-badge_id rate
limit instead. This file proves: the route still behaves correctly for a
normal request (a bad pack_id still 400s, an unknown badge still 404s), and
that the new rate limit actually triggers rather than being decorative.
"""

import os
import secrets

import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
# Real mount path (server.py: app.include_router(stripe_router, prefix="/api"),
# stripe_router itself prefix="/payments") — NOT /api/v1/checkout, which is
# what docs/PERMISSION_MATRIX.md's original FLAG table said; corrected here
# and in the matrix (docs/decisions/0001-founder-decisions-2026-08-31.md).
API = f"{BASE_URL}/api/payments"

CHECKOUT_RATE_LIMIT = int(os.environ.get("FREK_RATE_CHECKOUT_PER_HOUR", "20"))


def _checkout_body(badge_id):
    return {
        "pack_id": "decouverte",
        "badge_id": badge_id,
        "success_url": "https://example.test/ok",
        "cancel_url": "https://example.test/cancel",
    }


class TestCheckoutRemainsPublic:
    """Documented decision: no credential required."""

    def test_invalid_pack_still_400s_without_any_credential(self):
        r = requests.post(
            f"{API}/checkout",
            json={
                "pack_id": "not-a-real-pack",
                "badge_id": "CC26-BNV-0000",
                "success_url": "https://example.test/ok",
                "cancel_url": "https://example.test/cancel",
            },
            timeout=5,
        )
        assert r.status_code == 400

    def test_unknown_badge_404s_without_any_credential(self):
        badge_id = f"CC26-BNV-{secrets.token_hex(4).upper()}"
        r = requests.post(f"{API}/checkout", json=_checkout_body(badge_id), timeout=5)
        assert r.status_code == 404


class TestCheckoutRateLimit:
    def test_repeated_requests_for_same_badge_eventually_429(self):
        # One badge_id, hammered past the configured per-hour limit. All
        # 404 on the badge lookup (no real badge needed) until the rate
        # limiter kicks in first and returns 429 instead.
        badge_id = f"CC26-BNV-{secrets.token_hex(4).upper()}"
        statuses = []
        for _ in range(CHECKOUT_RATE_LIMIT + 3):
            r = requests.post(
                f"{API}/checkout", json=_checkout_body(badge_id), timeout=5
            )
            statuses.append(r.status_code)
            if r.status_code == 429:
                break
        assert (
            429 in statuses
        ), f"never rate-limited after {len(statuses)} requests: {statuses}"

    def test_different_badge_ids_are_independent(self):
        # A fresh badge_id must not inherit another badge_id's rate-limit
        # count (scope = badge_id, not global).
        badge_id = f"CC26-BNV-{secrets.token_hex(4).upper()}"
        r = requests.post(f"{API}/checkout", json=_checkout_body(badge_id), timeout=5)
        assert r.status_code == 404  # not 429
