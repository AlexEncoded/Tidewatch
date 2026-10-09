"""Application service for changing the operational state of a device."""

from typing import Protocol

from ..domain.devices import DeviceOwnershipError, DeviceSnapshot, DeviceStatusCommand


class DeviceStatusRegistry(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def update_device_status(
        self,
        buoy_id: str,
        device_id: str,
        update: DeviceStatusCommand,
    ) -> DeviceSnapshot | None:
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
    return device
