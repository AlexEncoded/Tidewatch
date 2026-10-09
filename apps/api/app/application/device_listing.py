"""Application service for listing devices assigned to a buoy."""

from typing import Protocol

from ..domain.devices import DeviceSnapshot


class DeviceListingReader(Protocol):
    """Input port for reading registered devices."""

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        ...

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


def list_devices_for_buoy(
    reader: DeviceListingReader, buoy_id: str
) -> list[DeviceSnapshot]:
    """Return registered device snapshots for one buoy."""
    return reader.list_device_snapshots(buoy_id)
