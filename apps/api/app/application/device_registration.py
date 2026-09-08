"""Application service for registering physical buoy devices."""

from typing import Protocol

from ..domain.devices import DeviceRegistrationConflict, validate_device_registration
from ..models import DeviceCreate


class DeviceRegistry(Protocol):
    def get_device(self, device_id: str):
        ...

    def list_devices(self, buoy_id: str) -> list:
        ...

    def create_device(self, buoy_id: str, device: DeviceCreate):
        ...


def register_device(registry: DeviceRegistry, buoy_id: str, device: DeviceCreate):
    """Register a device after enforcing domain uniqueness rules."""
    if registry.get_device(device.device_id) is not None:
        raise DeviceRegistrationConflict("Device already registered")
    validate_device_registration(
        device.device_id,
        device.sensor_channel,
        registry.list_devices(buoy_id),
    )
    return registry.create_device(buoy_id, device)
