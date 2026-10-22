"""Application input ports for physical-device use cases."""

from typing import Protocol

from ..domain.devices import DeviceRegistrationCommand, DeviceSnapshot, DeviceStatusCommand


class DeviceListingReader(Protocol):
    """Read registered devices assigned to a buoy."""

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        ...

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


class DeviceHealthReader(Protocol):
    """Read the registered-device health summary."""

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        ...

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


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
