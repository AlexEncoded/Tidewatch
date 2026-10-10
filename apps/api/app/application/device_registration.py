"""Application service for registering physical buoy devices."""

from typing import Protocol

from ..domain.devices import (
    DeviceRegistrationCommand,
    DeviceRegistrationConflict,
    DeviceSnapshot,
    validate_device_registration,
)


class DeviceRegistry(Protocol):
    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        ...

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        ...

    def create_device_snapshot(
        self, buoy_id: str, device: DeviceRegistrationCommand
    ) -> DeviceSnapshot:
        ...


def register_device(
    registry: DeviceRegistry, buoy_id: str, device: DeviceRegistrationCommand
) -> DeviceSnapshot:
    """Register a device after enforcing domain uniqueness rules."""
    if registry.get_device_snapshot(device.device_id) is not None:
        raise DeviceRegistrationConflict("Device already registered")
    validate_device_registration(
        device.device_id,
        device.sensor_channel,
        registry.list_device_snapshots(buoy_id),
    )
    return registry.create_device_snapshot(buoy_id, device)
