"""Read adapter composing fleet, device, battery and sensor-health data."""

from datetime import datetime

from sqlalchemy.orm import Session

from .battery_repository import BatteryRepository
from .buoy_location_repository import BuoyLocationRepository
from .buoy_registry_repository import BuoyRegistryRepository
from .domain.buoy import BuoySnapshot
from .domain.devices import DeviceSnapshot
from .domain.telemetry import BatteryTelemetrySnapshot, LocationTelemetrySnapshot
from .sensor_health_repository import SensorHealthRepository


class MaintenanceRepository(SensorHealthRepository):
    """Compose sensor-health history with fleet and device maintenance reads."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.locations = BuoyLocationRepository(db)
        self.battery = BatteryRepository(db)
        self.devices = self.battery.devices
        self.registry = BuoyRegistryRepository(db)

    def list_locations(
        self,
        buoy_id: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        return self.locations.list_locations(buoy_id, limit, since, until)

    def latest_battery(
        self,
        buoy_id: str,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> BatteryTelemetrySnapshot | None:
        return self.battery.latest_battery(
            buoy_id, device_id, physical_device_id
        )

    def add_battery(
        self, reading: BatteryTelemetrySnapshot
    ) -> BatteryTelemetrySnapshot:
        return self.battery.add_battery(reading)

    def list_batteries(
        self,
        buoy_id: str,
        limit: int,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> list[BatteryTelemetrySnapshot]:
        return self.battery.list_batteries(
            buoy_id, limit, device_id, physical_device_id
        )

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        return self.devices.get_device_snapshot(device_id)

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        return self.devices.mark_device_seen_by_id(device_id, seen_at)

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        return self.devices.list_device_snapshots(buoy_id)

    def list_buoy_snapshots(self) -> list[BuoySnapshot]:
        return self.registry.list_buoy_snapshots()
