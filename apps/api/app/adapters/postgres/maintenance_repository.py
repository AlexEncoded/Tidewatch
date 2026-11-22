"""Read adapter composing fleet, device, battery and sensor-health data."""

from datetime import datetime

from sqlalchemy.orm import Session

from .battery_repository import BatteryRepository
from .buoy_location_repository import BuoyLocationRepository
from .buoy_registry_repository import BuoyRegistryRepository
from ...domain.buoy import BuoySnapshot
from ...domain.devices import DeviceSnapshot, SensorChannel
from ...domain.battery import BatteryTelemetrySnapshot
from ...domain.location import LocationTelemetrySnapshot
from .sensor_health_repository import SensorHealthRepository
from ...application.maintenance_ports import MaintenanceReader
from ...domain.acoustic_altimeter import AcousticAltimeterTelemetrySnapshot
from ...domain.air_temperature import AirTemperatureTelemetrySnapshot
from ...domain.ambient_light import AmbientLightTelemetrySnapshot
from ...domain.atmospheric_pressure import AtmosphericPressureTelemetrySnapshot
from ...domain.chlorophyll_a import ChlorophyllATelemetrySnapshot
from ...domain.conductivity import ConductivityTelemetrySnapshot
from ...domain.dissolved_oxygen import DissolvedOxygenTelemetrySnapshot
from ...domain.humidity import HumidityTelemetrySnapshot
from ...domain.imu import ImuTelemetrySnapshot
from ...domain.marine_current import MarineCurrentTelemetrySnapshot
from ...domain.ph import PHTelemetrySnapshot
from ...domain.pressure import PressureTelemetrySnapshot
from ...domain.rainfall import RainfallTelemetrySnapshot
from ...domain.salinity import SalinityTelemetrySnapshot
from ...domain.sensor_health import SensorHealthCheckSnapshot
from ...domain.temperature import TemperatureTelemetrySnapshot
from ...domain.turbidity import TurbidityTelemetrySnapshot
from ...domain.underwater_acoustic import UnderwaterAcousticTelemetrySnapshot
from ...domain.wind import WindTelemetrySnapshot


class MaintenanceRepository(MaintenanceReader):
    """Compose sensor-health history with fleet and device maintenance reads."""

    def __init__(self, db: Session) -> None:
        self.sensor_health = SensorHealthRepository(db)
        self.locations = BuoyLocationRepository(db)
        self.battery = BatteryRepository(db)
        self.devices = self.battery.devices
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def list_sensor_health_checks(
        self, buoy_id: str, limit: int
    ) -> list[SensorHealthCheckSnapshot]:
        return self.sensor_health.list_sensor_health_checks(buoy_id, limit)

    def list_temperatures(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[TemperatureTelemetrySnapshot]:
        return self.sensor_health.list_temperatures(buoy_id, limit, sensor_channel)

    def list_pressures(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[PressureTelemetrySnapshot]:
        return self.sensor_health.list_pressures(buoy_id, limit, sensor_channel)

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        return self.sensor_health.list_salinity(buoy_id, limit, sensor_channel)

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ImuTelemetrySnapshot]:
        return self.sensor_health.list_imu(buoy_id, limit, sensor_channel)

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        return self.sensor_health.list_ambient_light(buoy_id, limit, sensor_channel)

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        return self.sensor_health.list_wind(buoy_id, limit, sensor_channel)

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[MarineCurrentTelemetrySnapshot]:
        return self.sensor_health.list_marine_current(buoy_id, limit, sensor_channel)

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        return self.sensor_health.list_turbidity(buoy_id, limit, sensor_channel)

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[DissolvedOxygenTelemetrySnapshot]:
        return self.sensor_health.list_dissolved_oxygen(buoy_id, limit, sensor_channel)

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[PHTelemetrySnapshot]:
        return self.sensor_health.list_ph(buoy_id, limit, sensor_channel)

    def list_conductivity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ConductivityTelemetrySnapshot]:
        return self.sensor_health.list_conductivity(buoy_id, limit, sensor_channel)

    def list_chlorophyll_a(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[ChlorophyllATelemetrySnapshot]:
        return self.sensor_health.list_chlorophyll_a(buoy_id, limit, sensor_channel)

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        return self.sensor_health.list_rainfall(buoy_id, limit, sensor_channel)

    def list_humidity(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[HumidityTelemetrySnapshot]:
        return self.sensor_health.list_humidity(buoy_id, limit, sensor_channel)

    def list_air_temperature(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AirTemperatureTelemetrySnapshot]:
        return self.sensor_health.list_air_temperature(buoy_id, limit, sensor_channel)

    def list_atmospheric_pressure(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AtmosphericPressureTelemetrySnapshot]:
        return self.sensor_health.list_atmospheric_pressure(buoy_id, limit, sensor_channel)

    def list_acoustic_altimeter(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[AcousticAltimeterTelemetrySnapshot]:
        return self.sensor_health.list_acoustic_altimeter(buoy_id, limit, sensor_channel)

    def list_underwater_acoustic(
        self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A"
    ) -> list[UnderwaterAcousticTelemetrySnapshot]:
        return self.sensor_health.list_underwater_acoustic(buoy_id, limit, sensor_channel)

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
