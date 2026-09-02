"""D4 -- ultrasonic watermark: historical intent preserved, never proof.

WATERMARK_EQUALS_PROOF=FALSE, enforced structurally, not just
documented: this module has no import anywhere in `offline_transport/`
outside itself, and nothing in `models.py`, `service.py`, or `routes.py`
reads a watermark's output to influence `LocalValidationStatus`,
`SyncStatus`, or `content_hash`/signature verification. A watermark
response is a dead end, by construction -- it cannot feed back into the
envelope's trust state even by accident.

Reuses the historical generator directly
(`frek.nodes.node07_transmission.node07.create_ultrasonic_watermark`) --
never reimplemented -- because the FSK-modulation logic itself is real,
working code; what was missing was never the generator, it was a reader.
No reader is added here either: `frek/nodes/node07_transmission.py`
never had a decode/extraction function (confirmed by reading the whole
file), and this state does not invent one -- IMPLEMENT_CULTURAL_
FINGERPRINT=FALSE-adjacent scope stays out of D4 too. The historical
`"inaudible": frequency_hz >= 17000` claim is preserved verbatim from
the source function -- not repeated as this module's own claim -- and
`validation_status` here is explicit and honest: `NOT_TESTED`.
"""

from __future__ import annotations

from typing import Any, Dict


def create_watermark_reference(frek_id: str) -> Dict[str, Any]:
    """Delegates to the real historical generator, then wraps the
    result with an explicit, honest validation-status annotation. The
    returned dict is intentionally NOT a `TransportEnvelope` field and
    is never persisted alongside one -- it may function as a locator,
    identifier, soft content binding, or transport carrier depending on
    a future implementation, but this function makes no claim about
    which, and none about inaudibility/unremovability/robustness/
    security/forensic validity beyond what the historical code itself
    already asserted (frequency band only)."""
    from frek.nodes.node07_transmission import node07

    watermark = node07.create_ultrasonic_watermark(frek_id)
    historical = watermark.to_dict()
    return {
        **historical,
        "proof": False,
        "validation_status": "NOT_TESTED",
        "decoder_exists": False,
        "note": (
            "Historical prototype-only generator, reused verbatim. No "
            "decode/extraction path exists in this codebase, so this "
            "watermark cannot be verified as present in any audio it is "
            "embedded into. WATERMARK_EQUALS_PROOF=FALSE."
        ),
    }
