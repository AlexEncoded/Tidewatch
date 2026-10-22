"""Composite input ports for maintenance use cases."""

from typing import Protocol, runtime_checkable

from ..domain.buoy import BuoySnapshot
from .device_ports import DeviceHealthReader
from .fleet_ports import LocationTelemetryReader
from .sensor_ports import BatteryTelemetryReader, SensorHealthReader


@runtime_checkable
class MaintenanceReader(
    LocationTelemetryReader,
    BatteryTelemetryReader,
    SensorHealthReader,
    DeviceHealthReader,
    Protocol,
):
    """Read-only queries required by the maintenance application service."""

    def list_buoy_snapshots(self) -> list[BuoySnapshot]:
        ...
