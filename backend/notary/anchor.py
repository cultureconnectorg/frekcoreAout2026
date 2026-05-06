"""
FREK Notary — Ancrage Bitcoin via OpenTimestamps.

OpenTimestamps = standard open-source. Calendar servers publics agregent
les hashes via Merkle tree puis publient un OP_RETURN dans Bitcoin.
Cout pour FREK : 0 sats. Souverain : preuve verifiable hors-ligne.
"""
import asyncio
import base64
import logging
import os
from datetime import datetime, timezone

from opentimestamps.calendar import RemoteCalendar
from opentimestamps.core.serialize import (
    BytesSerializationContext,
    BytesDeserializationContext,
)
from opentimestamps.core.timestamp import Timestamp
from opentimestamps.core.notary import BitcoinBlockHeaderAttestation

logger = logging.getLogger("frek.notary.anchor")

# Calendars publics et gratuits (Peter Todd, Eternity Wall, Catallaxy)
DEFAULT_CALENDARS = [
    "https://a.pool.opentimestamps.org",
    "https://b.pool.opentimestamps.org",
    "https://alice.btc.calendar.opentimestamps.org",
    "https://bob.btc.calendar.opentimestamps.org",
    "https://finney.calendar.eternitywall.com",
]


def _get_calendars() -> list:
    raw = os.environ.get("OTS_CALENDARS")
    if raw:
        return [c.strip() for c in raw.split(",") if c.strip()]
    return DEFAULT_CALENDARS


def serialize_timestamp(ts: Timestamp) -> bytes:
    ctx = BytesSerializationContext()
    ts.serialize(ctx)
    return ctx.getbytes()


def deserialize_timestamp(data: bytes, msg: bytes) -> Timestamp:
    ctx = BytesDeserializationContext(data)
    return Timestamp.deserialize(ctx, msg)


def find_btc_attestation(ts: Timestamp):
    """Walk timestamp tree to find a BitcoinBlockHeaderAttestation, if any."""
    for att in ts.attestations:
        if isinstance(att, BitcoinBlockHeaderAttestation):
            return att
    for op, sub_ts in ts.ops.items():
        sub = find_btc_attestation(sub_ts)
        if sub:
            return sub
    return None


def _submit_to_calendar(url: str, digest: bytes) -> Timestamp:
    """Synchronous OTS submit (called via asyncio.to_thread)."""
    cal = RemoteCalendar(url)
    return cal.submit(digest)


def _upgrade_via_calendar(url: str, ts: Timestamp) -> Timestamp:
    """Try to upgrade a pending timestamp via a single calendar."""
    cal = RemoteCalendar(url)
    # ts.msg is the original digest, but for upgrade we need to query each
    # sub-timestamp. python-opentimestamps lib upgrades by getting the
    # commitment for each pending attestation.
    # Simpler: for each pending op result, call calendar.get_timestamp
    # Walk all timestamps and try to upgrade pending ones in place.
    return _walk_and_upgrade(ts, cal)


def _walk_and_upgrade(ts: Timestamp, cal: RemoteCalendar) -> Timestamp:
    """Walk the tree and upgrade any PendingAttestation against this calendar."""
    from opentimestamps.core.notary import PendingAttestation

    for att in list(ts.attestations):
        if isinstance(att, PendingAttestation):
            # If this pending attestation belongs to this calendar, try to upgrade
            if att.uri.rstrip("/") == cal.url.rstrip("/"):
                try:
                    upgraded_ts = cal.get_timestamp(ts.msg)
                    ts.merge(upgraded_ts)
                except Exception as e:
                    logger.debug(f"Upgrade pending failed on {cal.url}: {e}")
    for op, sub_ts in ts.ops.items():
        _walk_and_upgrade(sub_ts, cal)
    return ts


class OTSAnchor:
    """Anchor service: submits block hashes to OTS and upgrades to Bitcoin proofs."""

    def __init__(self, db, chain):
        self.db = db
        self.chain = chain
        self.blocks = db.notary_blocks
        self.state = db.notary_chain_state
        self.calendars = _get_calendars()
        self._upgrade_task = None
        self._stop = False

    async def submit_block(self, height: int) -> dict:
        """Submit a block's hash to all configured OTS calendars."""
        blk = await self.chain.get_block(height)
        if not blk:
            return {"ok": False, "error": "block_not_found"}

        digest = bytes.fromhex(blk["block_hash"])
        merged_ts = Timestamp(digest)
        success_cals = []
        errors = []

        for url in self.calendars:
            try:
                ts = await asyncio.to_thread(_submit_to_calendar, url, digest)
                merged_ts.merge(ts)
                success_cals.append(url)
            except Exception as e:
                errors.append({"calendar": url, "error": str(e)})
                logger.warning(f"OTS submit failed on {url}: {e}")

        if not success_cals:
            return {"ok": False, "errors": errors}

        ots_bytes = serialize_timestamp(merged_ts)
        await self.blocks.update_one(
            {"height": height},
            {
                "$set": {
                    "ots_submitted": True,
                    "ots_calendars": success_cals,
                    "ots_proof": ots_bytes,
                    "ots_submitted_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        await self.state.update_one(
            {"_id": "frek_chain_state"},
            {
                "$inc": {"total_anchored": 1},
                "$set": {"last_anchor_at": datetime.now(timezone.utc).isoformat()},
            },
            upsert=True,
        )
        return {
            "ok": True,
            "height": height,
            "calendars": success_cals,
            "errors": errors,
            "ots_size": len(ots_bytes),
        }

    async def submit_pending_blocks(self, max_blocks: int = 50) -> dict:
        """Submit any blocks not yet anchored (background sweep)."""
        cursor = (
            self.blocks.find({"ots_submitted": False}, {"_id": 0, "height": 1})
            .sort("height", 1)
            .limit(max_blocks)
        )
        heights = [b["height"] async for b in cursor]
        results = []
        for h in heights:
            try:
                res = await self.submit_block(h)
                results.append(res)
            except Exception as e:
                logger.exception(f"submit_block({h}) failed: {e}")
                results.append({"ok": False, "height": h, "error": str(e)})
        return {"submitted": len(results), "results": results}

    async def upgrade_block(self, height: int) -> dict:
        """Try to upgrade a block's OTS proof to a full Bitcoin attestation."""
        blk = await self.blocks.find_one({"height": height}, {"_id": 0})
        if not blk or not blk.get("ots_proof"):
            return {"ok": False, "error": "no_ots_proof"}
        if blk.get("btc_anchored"):
            return {"ok": True, "already": True}

        digest = bytes.fromhex(blk["block_hash"])
        ts = deserialize_timestamp(blk["ots_proof"], digest)

        for url in self.calendars:
            try:
                await asyncio.to_thread(_upgrade_via_calendar, url, ts)
            except Exception as e:
                logger.debug(f"upgrade via {url} failed: {e}")

        att = find_btc_attestation(ts)
        if att is None:
            # Save merged (possibly newer pending state)
            await self.blocks.update_one(
                {"height": height},
                {"$set": {"ots_proof": serialize_timestamp(ts)}},
            )
            return {"ok": False, "btc_anchored": False, "message": "still_pending"}

        btc_height = att.height
        await self.blocks.update_one(
            {"height": height},
            {
                "$set": {
                    "ots_proof": serialize_timestamp(ts),
                    "btc_anchored": True,
                    "btc_block_height": btc_height,
                    "btc_attestation_time": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        await self.state.update_one(
            {"_id": "frek_chain_state"},
            {"$inc": {"total_btc_confirmed": 1}},
            upsert=True,
        )
        return {"ok": True, "btc_anchored": True, "btc_block_height": btc_height}

    async def upgrade_pending(self, max_blocks: int = 100) -> dict:
        """Background sweep: try to upgrade pending OTS to Bitcoin attestations."""
        cursor = (
            self.blocks.find(
                {"ots_submitted": True, "btc_anchored": False},
                {"_id": 0, "height": 1},
            )
            .sort("height", 1)
            .limit(max_blocks)
        )
        heights = [b["height"] async for b in cursor]
        upgraded = 0
        results = []
        for h in heights:
            try:
                res = await self.upgrade_block(h)
                if res.get("btc_anchored"):
                    upgraded += 1
                results.append({"height": h, **res})
            except Exception as e:
                logger.exception(f"upgrade_block({h}) failed: {e}")
                results.append({"height": h, "ok": False, "error": str(e)})
        return {"checked": len(heights), "upgraded": upgraded, "results": results}

    async def get_proof_b64(self, height: int) -> dict:
        blk = await self.blocks.find_one({"height": height}, {"_id": 0})
        if not blk:
            return {}
        ots = blk.get("ots_proof")
        return {
            "height": height,
            "block_hash": blk["block_hash"],
            "ots_proof_b64": base64.b64encode(ots).decode("ascii") if ots else None,
            "btc_anchored": blk.get("btc_anchored", False),
            "btc_block_height": blk.get("btc_block_height"),
            "btc_attestation_time": blk.get("btc_attestation_time"),
            "ots_calendars": blk.get("ots_calendars", []),
        }

    # --- Background loop ---
    async def background_loop(self, submit_interval: int = 30, upgrade_interval: int = 1800):
        """Run periodic submit + upgrade. Cooperative cancel via self._stop."""
        logger.info(
            f"FREK Notary background loop started (submit={submit_interval}s, upgrade={upgrade_interval}s)"
        )
        last_upgrade = 0.0
        loop = asyncio.get_event_loop()
        while not self._stop:
            try:
                await self.submit_pending_blocks(max_blocks=50)
                now = loop.time()
                if now - last_upgrade > upgrade_interval:
                    await self.upgrade_pending(max_blocks=100)
                    last_upgrade = now
            except Exception as e:
                logger.exception(f"Notary background loop error: {e}")
            await asyncio.sleep(submit_interval)

    def start(self):
        if self._upgrade_task is None or self._upgrade_task.done():
            self._stop = False
            self._upgrade_task = asyncio.create_task(self.background_loop())

    def stop(self):
        self._stop = True
        if self._upgrade_task:
            self._upgrade_task.cancel()
