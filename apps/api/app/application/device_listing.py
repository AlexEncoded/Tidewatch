"""Application service for listing devices assigned to a buoy."""

from typing import Protocol

from ..domain.devices import DeviceSnapshot
from .device_snapshots import to_device_snapshot


class DeviceListingReader(Protocol):
    """Input port for reading registered devices."""

    def list_devices(self, buoy_id: str) -> list:
        ...


def list_devices_for_buoy(
    reader: DeviceListingReader, buoy_id: str
) -> list[DeviceSnapshot]:
    """Return registered device snapshots for one buoy."""
    return [
        to_device_snapshot(device)
        for device in reader.list_devices(buoy_id)
    ]
