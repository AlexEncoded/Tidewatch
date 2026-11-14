"""Application service for registering physical buoy devices."""

from ..domain.devices import (
    DeviceRegistrationCommand,
    DeviceSnapshot,
    validate_device_registration,
)
from .device_ports import DeviceRegistry
from .fleet_ports import FleetMetrics


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


def register_device_for_buoy(
    registry: DeviceRegistry,
    metrics: FleetMetrics,
    buoy_id: str,
    device: DeviceRegistrationCommand,
) -> DeviceSnapshot | None:
    """Validate buoy existence, register its device, and publish its heartbeat."""
    if not registry.buoy_exists(buoy_id):
        return None

    result = register_device(registry, buoy_id, device)
    metrics.record_device_heartbeat(
        buoy_id, result.device_id, result.sensor_channel, result.last_seen_at
    )
    return result
