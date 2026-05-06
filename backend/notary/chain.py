"""
FREK-Chain — Couche locale (Merkle/Hash chain)
Tamper-evident, real-time, zero-cost.

Each block links to previous via SHA256.
Genesis: prev_hash = '0' * 64.
block_hash = SHA256(height || prev_hash || payload_hash || payload_type || payload_id || timestamp || event_id || spec_version)
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("frek.notary.chain")

GENESIS_PREV_HASH = "0" * 64
STATE_DOC_ID = "frek_chain_state"
FREK_SPEC_VERSION = "1.0.0"


def _canonical_json(data: dict) -> str:
    """Deterministic JSON serialization (sorted keys, no whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def hash_payload(payload_data: dict) -> str:
    """SHA256 hex of canonical JSON payload."""
    canonical = _canonical_json(payload_data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_block_hash(
    height: int,
    prev_hash: str,
    payload_hash: str,
    payload_type: str,
    payload_id: str,
    timestamp: str,
    event_id: Optional[str] = None,
    spec_version: str = FREK_SPEC_VERSION,
) -> str:
    """Deterministic block hash (incluant event_id + spec_version)."""
    eid = event_id or ""
    s = f"{height}|{prev_hash}|{payload_hash}|{payload_type}|{payload_id}|{timestamp}|{eid}|{spec_version}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FrekChain:
    """Manage the local FREK-Chain backed by MongoDB."""

    def __init__(self, db):
        self.db = db
        self.blocks = db.notary_blocks
        self.state = db.notary_chain_state

    async def ensure_indexes(self):
        await self.blocks.create_index("height", unique=True)
        await self.blocks.create_index("block_hash", unique=True)
        await self.blocks.create_index("payload_id")
        await self.blocks.create_index("payload_type")
        await self.blocks.create_index([("btc_anchored", 1), ("height", 1)])
        await self.blocks.create_index("event_id", sparse=True)
        await self.blocks.create_index("spec_version")

    async def _get_state(self) -> dict:
        st = await self.state.find_one({"_id": STATE_DOC_ID}, {"_id": 0})
        if not st:
            st = {
                "height": 0,
                "last_block_hash": GENESIS_PREV_HASH,
                "genesis_at": None,
                "last_block_at": None,
                "total_anchored": 0,
                "total_btc_confirmed": 0,
                "last_anchor_at": None,
            }
            await self.state.insert_one({"_id": STATE_DOC_ID, **st})
        return st

    async def append_block(
        self,
        payload_type: str,
        payload_id: str,
        payload_data: dict,
        metadata: Optional[dict] = None,
        event_id: Optional[str] = None,
        spec_version: str = FREK_SPEC_VERSION,
    ) -> dict:
        """Append a new block to the chain. Returns the inserted block dict."""
        st = await self._get_state()
        height = int(st["height"]) + 1
        prev_hash = st["last_block_hash"]
        ts = now_iso()
        p_hash = hash_payload(payload_data)
        b_hash = compute_block_hash(
            height, prev_hash, p_hash, payload_type, payload_id, ts, event_id, spec_version,
        )

        block = {
            "height": height,
            "prev_hash": prev_hash,
            "payload_type": payload_type,
            "payload_id": payload_id,
            "payload_hash": p_hash,
            "payload_data": payload_data,
            "metadata": metadata or {},
            "timestamp": ts,
            "block_hash": b_hash,
            "event_id": event_id,
            "spec_version": spec_version,
            "ots_submitted": False,
            "ots_calendars": [],
            "ots_proof": None,
            "btc_anchored": False,
            "btc_block_height": None,
            "btc_attestation_time": None,
        }
        await self.blocks.insert_one(block)

        update = {
            "height": height,
            "last_block_hash": b_hash,
            "last_block_at": ts,
        }
        if height == 1:
            update["genesis_at"] = ts
        await self.state.update_one(
            {"_id": STATE_DOC_ID}, {"$set": update}, upsert=True
        )
        logger.info(f"FREK-Chain block #{height} appended ({payload_type}:{payload_id} event:{event_id})")
        block.pop("_id", None)
        return block

    async def get_block(self, height: int) -> Optional[dict]:
        return await self.blocks.find_one({"height": height}, {"_id": 0})

    async def get_block_by_hash(self, block_hash: str) -> Optional[dict]:
        return await self.blocks.find_one({"block_hash": block_hash}, {"_id": 0})

    async def get_blocks_for_payload(self, payload_id: str) -> list:
        return (
            await self.blocks.find({"payload_id": payload_id}, {"_id": 0})
            .sort("height", 1)
            .to_list(1000)
        )

    async def verify_chain(self, limit: Optional[int] = None) -> dict:
        """Walk the chain and verify each block's hash + linkage.
        Backwards compat: blocks anciens (sans event_id/spec_version) verifies en mode v0.
        """
        cursor = self.blocks.find({}, {"_id": 0}).sort("height", 1)
        if limit:
            cursor = cursor.limit(limit)
        prev = GENESIS_PREV_HASH
        checked = 0
        async for blk in cursor:
            # Recompute with current schema (event_id + spec_version present)
            recomputed = compute_block_hash(
                blk["height"],
                blk["prev_hash"],
                blk["payload_hash"],
                blk["payload_type"],
                blk["payload_id"],
                blk["timestamp"],
                blk.get("event_id"),
                blk.get("spec_version", FREK_SPEC_VERSION),
            )
            if blk["prev_hash"] != prev:
                return {
                    "valid": False,
                    "blocks_checked": checked,
                    "first_invalid_height": blk["height"],
                    "reason": "prev_hash_mismatch",
                }
            if recomputed != blk["block_hash"]:
                # Backwards-compat : try legacy v0 hash (no event_id, no spec_version)
                legacy = hashlib.sha256(
                    f"{blk['height']}|{blk['prev_hash']}|{blk['payload_hash']}|{blk['payload_type']}|{blk['payload_id']}|{blk['timestamp']}".encode("utf-8")
                ).hexdigest()
                if legacy != blk["block_hash"]:
                    return {
                        "valid": False,
                        "blocks_checked": checked,
                        "first_invalid_height": blk["height"],
                        "reason": "block_hash_mismatch",
                    }
            prev = blk["block_hash"]
            checked += 1
        return {"valid": True, "blocks_checked": checked, "first_invalid_height": None}

    async def chain_proof(self, height: int) -> dict:
        """Return a minimal proof: block + linkage chain back to genesis (compact)."""
        blk = await self.get_block(height)
        if not blk:
            return {}
        # For compactness, return block + its prev_hash (caller can walk if needed)
        return {
            "height": blk["height"],
            "prev_hash": blk["prev_hash"],
            "payload_hash": blk["payload_hash"],
            "block_hash": blk["block_hash"],
            "timestamp": blk["timestamp"],
            "linkage": "SHA256(height|prev_hash|payload_hash|payload_type|payload_id|timestamp)",
        }
