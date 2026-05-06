"""
Service interne pour notariser les evenements FREK depuis tout module backend.
Usage: `await notarize_event('identity_emit', frek_id, {...})`
La soumission OTS Bitcoin se fait en background.
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger("frek.notary.service")

_chain = None
_anchor = None


def init_service(chain, anchor):
    global _chain, _anchor
    _chain = chain
    _anchor = anchor


async def notarize_event(
    payload_type: str,
    payload_id: str,
    payload_data: dict,
    metadata: Optional[dict] = None,
    submit_now: bool = True,
) -> Optional[dict]:
    """Append a block to FREK-Chain. Submit to OTS in background. Never raises."""
    if _chain is None:
        logger.warning("Notary service not initialized; skipping notarize_event")
        return None
    try:
        blk = await _chain.append_block(
            payload_type=payload_type,
            payload_id=payload_id,
            payload_data=payload_data,
            metadata=metadata or {},
        )
        if submit_now and _anchor is not None:
            asyncio.create_task(_anchor.submit_block(blk["height"]))
        return blk
    except Exception as e:
        logger.exception(f"notarize_event failed ({payload_type}:{payload_id}): {e}")
        return None
