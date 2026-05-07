"""FREK Notary — Bitcoin Core RPC client.

Connecte un nœud Bitcoin Core (typiquement pruned) via JSON-RPC sur HTTP.
Aucun wallet ni UTXO n'est requis : on capture la chain tip (hauteur, hash,
timestamp du block) comme temoin temporel cryptographique.

Variables d'environnement :
    BITCOIN_RPC_URL       — URL JSON-RPC, ex http://127.0.0.1:8332
                            ou https://bitcoin.example.com (Cloudflare Tunnel)
    BITCOIN_RPC_USER      — utilisateur RPC
    BITCOIN_RPC_PASSWORD  — mot de passe RPC

L'echec de connexion (timeout, auth, dns) leve BitcoinNodeUnavailable ;
le DualSourceManager bascule alors silencieusement sur OpenTimestamps.
"""
import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("frek.notary.btc_node")

DEFAULT_TIMEOUT = float(os.environ.get("BITCOIN_RPC_TIMEOUT", "5.0"))


class BitcoinNodeUnavailable(Exception):
    pass


class BitcoinNodeClient:
    def __init__(
        self,
        url: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.url = url or os.environ.get("BITCOIN_RPC_URL")
        self.user = user or os.environ.get("BITCOIN_RPC_USER")
        self.password = password or os.environ.get("BITCOIN_RPC_PASSWORD")
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.url and self.user and self.password)

    async def _rpc(self, method: str, params: Optional[list] = None):
        if not self.is_configured():
            raise BitcoinNodeUnavailable("rpc_not_configured")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as c:
                r = await c.post(
                    self.url,
                    auth=(self.user, self.password),
                    json={"jsonrpc": "1.0", "id": "frek", "method": method, "params": params or []},
                )
                r.raise_for_status()
                data = r.json()
                if data.get("error"):
                    raise BitcoinNodeUnavailable(f"rpc_error:{data['error']}")
                return data["result"]
        except BitcoinNodeUnavailable:
            raise
        except (httpx.HTTPError, ValueError, asyncio.TimeoutError) as e:
            raise BitcoinNodeUnavailable(str(e))

    async def get_chain_tip(self) -> dict:
        """Capture la chain tip Bitcoin (hauteur + hash + timestamp).

        getblockcount + getblockhash + getblockheader. Fonctionne sur node pruned.
        """
        height = await self._rpc("getblockcount")
        block_hash = await self._rpc("getblockhash", [height])
        header = await self._rpc("getblockheader", [block_hash, True])
        return {
            "height": int(height),
            "hash": block_hash,
            "time": int(header.get("time", 0)),
            "merkleroot": header.get("merkleroot"),
        }

    async def health(self) -> dict:
        if not self.is_configured():
            return {"connected": False, "reason": "not_configured"}
        try:
            tip = await self.get_chain_tip()
            return {"connected": True, "tip_height": tip["height"], "tip_hash": tip["hash"], "tip_time": tip["time"]}
        except BitcoinNodeUnavailable as e:
            return {"connected": False, "reason": str(e)[:120]}
        except Exception as e:
            return {"connected": False, "reason": f"unexpected:{e}"[:120]}
