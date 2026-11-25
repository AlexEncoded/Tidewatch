"""Application service for changing the operational state of a device."""

from ..domain.fleet.devices import DeviceSnapshot, DeviceStatusCommand
from .device_errors import DeviceNotFound
from .device_ports import DeviceStatusRegistry


def update_device_status(
    registry: DeviceStatusRegistry,
    buoy_id: str,
    device_id: str,
    update: DeviceStatusCommand,
) -> DeviceSnapshot:
    """Update a device state or reject an unknown/foreign device."""
    device = registry.update_device_status(buoy_id, device_id, update)
    if device is None:
        raise DeviceNotFound("Device not found")
    if device.buoy_id != buoy_id:
        raise DeviceNotFound("Device not found")
    return device


def update_device_status_for_buoy(
    registry: DeviceStatusRegistry,
    buoy_id: str,
    device_id: str,
    update: DeviceStatusCommand,
) -> DeviceSnapshot | None:
    """Check buoy existence before updating one of its device statuses."""
    if not registry.buoy_exists(buoy_id):
        return None
    return update_device_status(registry, buoy_id, device_id, update)
