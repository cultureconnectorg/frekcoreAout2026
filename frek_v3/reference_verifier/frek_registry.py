"""
FREK Attestation Protocol — Device Registry & State Management
Reference Implementation v0.1

The verifier maintains per-device state:
- AK_pub (known public key)
- last_counter (for replay detection)
- firmware whitelist (optional)
- status (ACTIVE, REVOKED, SUSPENDED)
"""

from typing import Dict, Optional, Set
from frek_types import DeviceState


class DeviceRegistry:
    """In-memory device registry for the reference verifier."""

    def __init__(self):
        self._devices: Dict[bytes, DeviceState] = {}

    def register(
        self,
        device_id: bytes,
        ak_pub: bytes,
        trusted_firmware_hashes: Optional[Set[bytes]] = None,
    ) -> DeviceState:
        """Register a new device."""
        state = DeviceState(
            device_id=device_id,
            ak_pub=ak_pub,
            last_counter=0,  # 0 means "no proof seen yet"
            trusted_firmware_hashes=trusted_firmware_hashes,
            status="ACTIVE",
        )
        self._devices[device_id] = state
        return state

    def get(self, device_id: bytes) -> Optional[DeviceState]:
        """Get device state by ID."""
        return self._devices.get(device_id)

    def revoke(self, device_id: bytes, reason: str = "") -> bool:
        """Revoke a device."""
        state = self._devices.get(device_id)
        if state is None:
            return False
        state.status = "REVOKED"
        return True

    def update_counter(self, device_id: bytes, new_counter: int) -> bool:
        """Update last known counter for a device."""
        state = self._devices.get(device_id)
        if state is None:
            return False
        state.last_counter = new_counter
        return True

    def list_devices(self) -> Dict[bytes, DeviceState]:
        """Return all registered devices."""
        return dict(self._devices)
