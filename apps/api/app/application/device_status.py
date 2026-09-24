"""Application service for changing the operational state of a device."""

from typing import Protocol

from ..domain.devices import DeviceOwnershipError, DeviceSnapshot, DeviceStatusCommand
from .device_snapshots import to_device_snapshot


class DeviceStatusRegistry(Protocol):
    def update_device_status(
        self,
        buoy_id: str,
        device_id: str,
        update: DeviceStatusCommand,
    ):
        ...


def update_device_status(
    registry: DeviceStatusRegistry,
    buoy_id: str,
    device_id: str,
    update: DeviceStatusCommand,
) -> DeviceSnapshot:
    """Update a device state or reject an unknown/foreign device."""
    device = registry.update_device_status(buoy_id, device_id, update)
    if device is None:
        raise DeviceOwnershipError("Device not found")
    return to_device_snapshot(device)
