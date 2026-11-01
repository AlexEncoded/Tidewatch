"""Application service for registering physical buoy devices."""

from ..domain.devices import (
    DeviceRegistrationCommand,
    DeviceSnapshot,
    validate_device_registration,
)
from .device_ports import DeviceRegistry


def register_device(
    registry: DeviceRegistry, buoy_id: str, device: DeviceRegistrationCommand
) -> DeviceSnapshot:
    """Register a device after enforcing domain uniqueness rules."""
    registered_device = registry.get_device_snapshot(device.device_id)
    validate_device_registration(
        device.device_id,
        device.sensor_channel,
        registry.list_device_snapshots(buoy_id),
        existing_registered_device=registered_device,
    )
    return registry.create_device_snapshot(buoy_id, device)
