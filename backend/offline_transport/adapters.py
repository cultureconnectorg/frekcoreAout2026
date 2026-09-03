"""D4 -- transport adapter boundary.

Core responsibility (encode/decode) lives here, transport-independent.
Adapters only attach `transport_metadata` (a framing tag) -- they never
touch the envelope's signed core, and they cannot override the
canonical verification result computed elsewhere (`routes.py` recomputes
integrity/signature from the envelope's own fields on every receive,
ignoring whatever an adapter claims about itself).

`ADAPTER_INFO` reuses `frek.nodes.node07_transmission.Node07Transmission.
PROTOCOL_CONFIG` directly for the 5 historical protocols (range/power/
latency/offline-capability facts, not reimplemented) and adds honest
entries for the 4 protocols new this state. No entry claims
`hardware_verified=True` -- this sandbox has no real BLE/NFC/QR/
ultrasonic hardware, so none of them are (mission's explicit
REAL-OFFLINE VALIDATION instruction: DO NOT CLAIM HARDWARE VERIFIED).
"""

from __future__ import annotations

import json
from typing import Any, Dict

from .canonical import canonical_json
from .models import TransportEnvelope, TransportProtocol

_NEW_ADAPTER_CONFIG: Dict[TransportProtocol, Dict[str, Any]] = {
    TransportProtocol.QR: {
        "offline_capable": True,
        "carrier": "printed/displayed 2D barcode",
    },
    TransportProtocol.LOCAL_FILE: {
        "offline_capable": True,
        "carrier": "filesystem",
    },
    TransportProtocol.LOCAL_NETWORK: {
        "offline_capable": True,
        "carrier": "LAN (no internet egress required)",
    },
    TransportProtocol.DEVICE_TO_DEVICE: {
        "offline_capable": True,
        "carrier": "direct peer link, protocol-agnostic",
    },
}


def _historical_protocol_config() -> Dict[str, Dict[str, Any]]:
    from frek.nodes.node07_transmission import Node07Transmission

    # Historical enum values match this module's own historical-subset
    # values verbatim (both "bluetooth_ble", "nfc", ... -- confirmed).
    return {p.value: cfg for p, cfg in Node07Transmission.PROTOCOL_CONFIG.items()}


def adapter_info() -> Dict[str, Dict[str, Any]]:
    """Per-protocol metadata + honest software/hardware evidence level."""
    historical = _historical_protocol_config()
    out: Dict[str, Dict[str, Any]] = {}
    for proto in TransportProtocol:
        base = dict(historical.get(proto.value, _NEW_ADAPTER_CONFIG.get(proto, {})))
        out[proto.value] = {
            **base,
            "software_status": (
                "ADAPTED" if proto == TransportProtocol.ULTRASONIC else "IMPLEMENTED"
            ),
            "hardware_verified": False,
        }
    return out


def encode_envelope(
    envelope: TransportEnvelope, *, protocol: TransportProtocol
) -> bytes:
    """Transport-independent encode: the full envelope (not just the
    signable core) as canonical JSON bytes, with a protocol tag
    attached to `transport_metadata` first. The SAME bytes-producing
    logic runs regardless of `protocol` -- proving transport-
    independence is exactly "encode(e, BLE) and encode(e, QR) carry an
    identical signable core", checked by test."""
    tagged = envelope.model_copy(deep=True)
    tagged.transport_metadata = {
        **tagged.transport_metadata,
        "protocol": protocol.value,
    }
    return canonical_json(tagged.model_dump(mode="json")).encode("utf-8")


def decode_envelope(data: bytes) -> TransportEnvelope:
    """Inverse of `encode_envelope` -- adapter-agnostic; the caller
    never needs to know which adapter produced `data`."""
    return TransportEnvelope.model_validate(json.loads(data.decode("utf-8")))
