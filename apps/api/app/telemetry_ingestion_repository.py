"""Composite persistence adapter for batch telemetry ingestion."""

from datetime import datetime

from sqlalchemy.orm import Session

from .buoy_location_repository import BuoyLocationRepository
from .domain.pressure import PressureTelemetrySnapshot
from .domain.temperature import TemperatureTelemetrySnapshot
from .domain.telemetry import (
    AcousticAltimeterTelemetrySnapshot,
    AirTemperatureTelemetrySnapshot,
    AmbientLightTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    BatteryTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    ImuTelemetrySnapshot,
    LocationTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    PHTelemetrySnapshot,
    RainfallTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    UnderwaterAcousticTelemetrySnapshot,
    WindTelemetrySnapshot,
)
from .domain.devices import DeviceSnapshot
from .entities import BuoyLocationReadingEntity
from .sensor_health_repository import SensorHealthRepository
from .battery_repository import BatteryRepository
from .buoy_registry_repository import BuoyRegistryRepository


class TelemetryIngestionRepository:
    """Compose per-sensor adapters for the batch-ingestion input port."""

    def __init__(self, db: Session) -> None:
        self.sensors = SensorHealthRepository(db)
        self.registry = BuoyRegistryRepository(db)
        self.locations = BuoyLocationRepository(db)
        self.battery = BatteryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def add_location(self, reading: LocationTelemetrySnapshot) -> BuoyLocationReadingEntity:
        return self.locations.add_location(reading)

    def list_locations(self, buoy_id: str, limit: int, since: datetime | None = None, until: datetime | None = None) -> list[LocationTelemetrySnapshot]:
        return self.locations.list_locations(buoy_id, limit, since, until)

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        return self.battery.get_device_snapshot(device_id)

    def mark_device_seen_by_id(self, device_id: str, seen_at: datetime) -> DeviceSnapshot | None:
        return self.battery.mark_device_seen_by_id(device_id, seen_at)

    def add_battery(self, reading: BatteryTelemetrySnapshot) -> BatteryTelemetrySnapshot:
        return self.battery.add_battery(reading)

    def list_batteries(self, buoy_id: str, limit: int, device_id: str | None = None, physical_device_id: str | None = None) -> list[BatteryTelemetrySnapshot]:
        return self.battery.list_batteries(buoy_id, limit, device_id, physical_device_id)

    def latest_battery(self, buoy_id: str, device_id: str | None = None, physical_device_id: str | None = None) -> BatteryTelemetrySnapshot | None:
        return self.battery.latest_battery(buoy_id, device_id, physical_device_id)

    def add_temperature(self, reading: TemperatureTelemetrySnapshot) -> TemperatureTelemetrySnapshot:
        return self.sensors.temperature.add_temperature(reading)

    def list_temperatures(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[TemperatureTelemetrySnapshot]:
        return self.sensors.list_temperatures(buoy_id, limit, sensor_channel)

    def add_pressure(self, reading: PressureTelemetrySnapshot) -> PressureTelemetrySnapshot:
        return self.sensors.pressure.add_pressure(reading)

    def list_pressures(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[PressureTelemetrySnapshot]:
        return self.sensors.list_pressures(buoy_id, limit, sensor_channel)

    def add_salinity(self, reading: SalinityTelemetrySnapshot) -> SalinityTelemetrySnapshot:
        return self.sensors.salinity.add_salinity(reading)

    def list_salinity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[SalinityTelemetrySnapshot]:
        return self.sensors.list_salinity(buoy_id, limit, sensor_channel)

    def add_imu(self, reading: ImuTelemetrySnapshot) -> ImuTelemetrySnapshot:
        return self.sensors.imu.add_imu(reading)

    def list_imu(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[ImuTelemetrySnapshot]:
        return self.sensors.list_imu(buoy_id, limit, sensor_channel)

    def add_ambient_light(self, reading: AmbientLightTelemetrySnapshot) -> AmbientLightTelemetrySnapshot:
        return self.sensors.ambient_light.add_ambient_light(reading)

    def list_ambient_light(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AmbientLightTelemetrySnapshot]:
        return self.sensors.list_ambient_light(buoy_id, limit, sensor_channel)

    def add_wind(self, reading: WindTelemetrySnapshot) -> WindTelemetrySnapshot:
        return self.sensors.wind.add_wind(reading)

    def list_wind(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[WindTelemetrySnapshot]:
        return self.sensors.list_wind(buoy_id, limit, sensor_channel)

    def add_marine_current(self, reading: MarineCurrentTelemetrySnapshot) -> MarineCurrentTelemetrySnapshot:
        return self.sensors.marine_current.add_marine_current(reading)

    def list_marine_current(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[MarineCurrentTelemetrySnapshot]:
        return self.sensors.list_marine_current(buoy_id, limit, sensor_channel)

    def add_turbidity(self, reading: TurbidityTelemetrySnapshot) -> TurbidityTelemetrySnapshot:
        return self.sensors.turbidity.add_turbidity(reading)

    def list_turbidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[TurbidityTelemetrySnapshot]:
        return self.sensors.list_turbidity(buoy_id, limit, sensor_channel)

    def add_dissolved_oxygen(self, reading: DissolvedOxygenTelemetrySnapshot) -> DissolvedOxygenTelemetrySnapshot:
        return self.sensors.dissolved_oxygen.add_dissolved_oxygen(reading)

    def list_dissolved_oxygen(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[DissolvedOxygenTelemetrySnapshot]:
        return self.sensors.list_dissolved_oxygen(buoy_id, limit, sensor_channel)

    def add_ph(self, reading: PHTelemetrySnapshot) -> PHTelemetrySnapshot:
        return self.sensors.ph.add_ph(reading)

    def list_ph(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[PHTelemetrySnapshot]:
        return self.sensors.list_ph(buoy_id, limit, sensor_channel)

    def add_conductivity(self, reading: ConductivityTelemetrySnapshot) -> ConductivityTelemetrySnapshot:
        return self.sensors.conductivity.add_conductivity(reading)

    def list_conductivity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[ConductivityTelemetrySnapshot]:
        return self.sensors.list_conductivity(buoy_id, limit, sensor_channel)

    def add_chlorophyll_a(self, reading: ChlorophyllATelemetrySnapshot) -> ChlorophyllATelemetrySnapshot:
        return self.sensors.chlorophyll_a.add_chlorophyll_a(reading)

    def list_chlorophyll_a(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[ChlorophyllATelemetrySnapshot]:
        return self.sensors.list_chlorophyll_a(buoy_id, limit, sensor_channel)

    def add_rainfall(self, reading: RainfallTelemetrySnapshot) -> RainfallTelemetrySnapshot:
        return self.sensors.rainfall.add_rainfall(reading)

    def list_rainfall(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[RainfallTelemetrySnapshot]:
        return self.sensors.list_rainfall(buoy_id, limit, sensor_channel)

    def add_humidity(self, reading: HumidityTelemetrySnapshot) -> HumidityTelemetrySnapshot:
        return self.sensors.humidity.add_humidity(reading)

    def list_humidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[HumidityTelemetrySnapshot]:
        return self.sensors.list_humidity(buoy_id, limit, sensor_channel)

    def add_air_temperature(self, reading: AirTemperatureTelemetrySnapshot) -> AirTemperatureTelemetrySnapshot:
        return self.sensors.air_temperature.add_air_temperature(reading)

    def list_air_temperature(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AirTemperatureTelemetrySnapshot]:
        return self.sensors.list_air_temperature(buoy_id, limit, sensor_channel)

    def add_atmospheric_pressure(self, reading: AtmosphericPressureTelemetrySnapshot) -> AtmosphericPressureTelemetrySnapshot:
        return self.sensors.atmospheric_pressure.add_atmospheric_pressure(reading)

    def list_atmospheric_pressure(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AtmosphericPressureTelemetrySnapshot]:
        return self.sensors.list_atmospheric_pressure(buoy_id, limit, sensor_channel)

    def add_acoustic_altimeter(self, reading: AcousticAltimeterTelemetrySnapshot) -> AcousticAltimeterTelemetrySnapshot:
        return self.sensors.acoustic_altimeter.add_acoustic_altimeter(reading)

    def list_acoustic_altimeter(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AcousticAltimeterTelemetrySnapshot]:
        return self.sensors.list_acoustic_altimeter(buoy_id, limit, sensor_channel)

    def add_underwater_acoustic(self, reading: UnderwaterAcousticTelemetrySnapshot) -> UnderwaterAcousticTelemetrySnapshot:
        return self.sensors.underwater_acoustic.add_underwater_acoustic(reading)

    def list_underwater_acoustic(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[UnderwaterAcousticTelemetrySnapshot]:
        return self.sensors.list_underwater_acoustic(buoy_id, limit, sensor_channel)
