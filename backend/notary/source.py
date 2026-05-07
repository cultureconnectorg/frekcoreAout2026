"""FREK Notary — Dual-source anchor manager.

Strategie :
- Source primaire : nœud Bitcoin Core (capture chain tip via RPC, sans wallet)
- Source fallback silencieuse : OpenTimestamps (calendrier publics gratuits)

Un cache local (TTL configurable) evite de poller le nœud a chaque ancrage.
La bascule est silencieuse — pas de log warning sauf premiere transition.
"""
import asyncio
import logging
import os
import time
from typing import Optional

from .btc_node import BitcoinNodeClient, BitcoinNodeUnavailable

logger = logging.getLogger("frek.notary.source")

HEALTH_TTL = float(os.environ.get("BITCOIN_NODE_HEALTH_TTL", "30"))


class DualSourceManager:
    """Decide la source d'ancrage et expose l'etat pour le dashboard."""

    def __init__(self, node_client: Optional[BitcoinNodeClient] = None):
        self.node = node_client or BitcoinNodeClient()
        self._cached_health: Optional[dict] = None
        self._cached_at: float = 0.0
        self._last_source: Optional[str] = None  # "node" | "ots"
        self._lock = asyncio.Lock()

    async def get_health(self, force_refresh: bool = False) -> dict:
        """Retourne {connected, source, tip_height?, tip_hash?, reason?, configured}."""
        now = time.monotonic()
        if not force_refresh and self._cached_health and (now - self._cached_at) < HEALTH_TTL:
            return self._cached_health
        async with self._lock:
            # Re-check after lock (un autre coroutine peut avoir refresh)
            if not force_refresh and self._cached_health and (time.monotonic() - self._cached_at) < HEALTH_TTL:
                return self._cached_health
            h = await self.node.health()
            source = "node" if h.get("connected") else "ots"
            health = {
                "configured": self.node.is_configured(),
                "source": source,
                **h,
            }
            # Log silencieusement la premiere transition uniquement
            if self._last_source and self._last_source != source:
                logger.info(f"FREK Notary — source switched: {self._last_source} -> {source}")
            self._last_source = source
            self._cached_health = health
            self._cached_at = time.monotonic()
            return health

    async def capture_node_anchor(self) -> Optional[dict]:
        """Tente une capture de la chain tip Bitcoin via le nœud.

        Retourne None silencieusement si le nœud est indisponible.
        """
        if not self.node.is_configured():
            return None
        try:
            tip = await self.node.get_chain_tip()
            return {
                "btc_node_height": tip["height"],
                "btc_node_block_hash": tip["hash"],
                "btc_node_time": tip["time"],
                "anchor_source": "node",
            }
        except BitcoinNodeUnavailable:
            # Silence : la source de fallback (OTS) prend le relais
            return None
        except Exception as e:
            logger.debug(f"capture_node_anchor unexpected: {e}")
            return None


# Singleton — initialise au demarrage par notary.routes.set_db
_manager: Optional[DualSourceManager] = None


def get_manager() -> DualSourceManager:
    global _manager
    if _manager is None:
        _manager = DualSourceManager()
    return _manager


def set_manager(manager: DualSourceManager):
    global _manager
    _manager = manager
