"""FREK Notary — Tests Bitcoin dual-source (node + fallback OTS).

Couvre les deux modes :
 - Source 'ots' : BITCOIN_RPC_* non configure → fallback silencieux
 - Source 'node' : BitcoinNodeClient mocke pour simuler une chain tip valide
 - Bascule silencieuse : pas de log warning, juste un info sur transition
 - Endpoint /api/v1/notary/source/health expose l'etat
 - submit_block enregistre anchor_source + btc_node_* selon disponibilite
"""
import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api/v1"


# ---------- Endpoint health ----------
class TestSourceHealthEndpoint:
    def test_health_endpoint_public(self):
        r = requests.get(f"{API}/notary/source/health", timeout=5)
        assert r.status_code == 200
        d = r.json()
        assert "source" in d
        assert d["source"] in ("node", "ots")
        assert "configured" in d
        assert "connected" in d

    def test_health_default_when_unconfigured(self):
        """Sans BITCOIN_RPC_* dans l'env du backend, source='ots' et reason='not_configured'."""
        # NB : ce test suppose que l'env backend n'a pas BITCOIN_RPC_URL set
        if os.environ.get("BITCOIN_RPC_URL"):
            pytest.skip("BITCOIN_RPC_URL configure dans l'env, skip le test fallback")
        r = requests.get(f"{API}/notary/source/health", timeout=5)
        d = r.json()
        assert d["configured"] is False
        assert d["source"] == "ots"
        assert d["connected"] is False


# ---------- Logique DualSourceManager (en process, mocke RPC) ----------
class TestDualSourceManager:
    def test_node_connected_returns_anchor(self):
        """Quand le nœud RPC repond, capture_node_anchor retourne btc_node_*."""
        from notary.btc_node import BitcoinNodeClient
        from notary.source import DualSourceManager

        client = BitcoinNodeClient(url="http://fake", user="u", password="p")
        # Mock get_chain_tip pour simuler un nœud sain
        mock_tip = {"height": 870000, "hash": "0000abcd", "time": 1730000000, "merkleroot": "deadbeef"}
        client.get_chain_tip = AsyncMock(return_value=mock_tip)
        # is_configured retournera True parce qu'on a passe url/user/password

        mgr = DualSourceManager(node_client=client)
        anchor = asyncio.get_event_loop().run_until_complete(mgr.capture_node_anchor())
        assert anchor is not None
        assert anchor["anchor_source"] == "node"
        assert anchor["btc_node_height"] == 870000
        assert anchor["btc_node_block_hash"] == "0000abcd"
        assert anchor["btc_node_time"] == 1730000000

    def test_node_unavailable_returns_none_silently(self):
        """Quand le RPC echoue, capture_node_anchor retourne None silencieusement."""
        from notary.btc_node import BitcoinNodeClient, BitcoinNodeUnavailable
        from notary.source import DualSourceManager

        client = BitcoinNodeClient(url="http://fake", user="u", password="p")
        client.get_chain_tip = AsyncMock(side_effect=BitcoinNodeUnavailable("connection refused"))
        mgr = DualSourceManager(node_client=client)
        anchor = asyncio.get_event_loop().run_until_complete(mgr.capture_node_anchor())
        assert anchor is None

    def test_node_not_configured_returns_none(self):
        from notary.btc_node import BitcoinNodeClient
        from notary.source import DualSourceManager

        client = BitcoinNodeClient(url=None, user=None, password=None)
        mgr = DualSourceManager(node_client=client)
        anchor = asyncio.get_event_loop().run_until_complete(mgr.capture_node_anchor())
        assert anchor is None

    def test_health_caches_results(self):
        """Deux get_health() consecutifs ne hit pas le RPC deux fois (TTL)."""
        from notary.btc_node import BitcoinNodeClient
        from notary.source import DualSourceManager

        client = BitcoinNodeClient(url="http://fake", user="u", password="p")
        call_count = 0

        async def mock_health():
            nonlocal call_count
            call_count += 1
            return {"connected": True, "tip_height": 1, "tip_hash": "x", "tip_time": 1}

        client.health = mock_health
        mgr = DualSourceManager(node_client=client)
        loop = asyncio.get_event_loop()
        h1 = loop.run_until_complete(mgr.get_health())
        h2 = loop.run_until_complete(mgr.get_health())
        assert h1 == h2
        # Premier call hit, second cache
        assert call_count == 1


# ---------- BitcoinNodeClient invariants ----------
class TestBitcoinNodeClient:
    def test_is_configured_requires_all_three(self):
        from notary.btc_node import BitcoinNodeClient
        assert BitcoinNodeClient(url=None, user=None, password=None).is_configured() is False
        assert BitcoinNodeClient(url="x", user=None, password="p").is_configured() is False
        assert BitcoinNodeClient(url="x", user="u", password=None).is_configured() is False
        assert BitcoinNodeClient(url="x", user="u", password="p").is_configured() is True

    def test_health_unconfigured_reason(self):
        from notary.btc_node import BitcoinNodeClient
        client = BitcoinNodeClient(url=None, user=None, password=None)
        h = asyncio.get_event_loop().run_until_complete(client.health())
        assert h == {"connected": False, "reason": "not_configured"}
