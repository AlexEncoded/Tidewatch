"""Application service for listing devices assigned to a buoy."""

from ..domain.devices import DeviceSnapshot
from .device_ports import DeviceHealthReader, DeviceListingReader


def list_devices_for_buoy(
    reader: DeviceListingReader, buoy_id: str
) -> list[DeviceSnapshot]:
    """Return registered device snapshots for one buoy."""
    return reader.list_device_snapshots(buoy_id)
