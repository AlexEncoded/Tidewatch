"""Composite input ports for maintenance use cases."""

from typing import Protocol, runtime_checkable

from ..domain.battery_health import BatteryHealthSnapshot
from ..domain.buoy import BuoySnapshot
from .battery_ports import BatteryTelemetryReader
from .device_ports import DeviceHealthReader
from .fleet_ports import LocationTelemetryReader
from .sensor_health_ports import SensorHealthReader


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


class MaintenanceMetrics(Protocol):
    """Publish operational maintenance values for one buoy evaluation."""

    def record_evaluation(
        self,
        buoy_id: str,
        battery_health: BatteryHealthSnapshot,
        average_speed_mps: float | None,
    ) -> None:
        ...
