from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .entities import (
    BuoyEntity,
    DeviceEntity,
    BuoyLocationReadingEntity,
    BatteryReadingEntity,
    AmbientLightReadingEntity,
    WindReadingEntity,
    ChlorophyllAReadingEntity,
    RainfallReadingEntity,
    HumidityReadingEntity,
    AirTemperatureReadingEntity,
    AtmosphericPressureReadingEntity,
    AcousticAltimeterReadingEntity,
    UnderwaterAcousticReadingEntity,
    ImuReadingEntity,
    MarineCurrentReadingEntity,
    TurbidityReadingEntity,
    DissolvedOxygenReadingEntity,
    PHReadingEntity,
    ConductivityReadingEntity,
    PressureReadingEntity,
    SalinityReadingEntity,
    TemperatureReadingEntity,
)
from .domain.buoy import (
    BuoySnapshot,
)
from .domain.devices import DeviceSnapshot
from .domain.sensor_health import (
    SensorHealthCheckSnapshot,
    SensorHealthSnapshot as DomainSensorHealthSnapshot,
)
from .domain.pressure import PressureTelemetrySnapshot
from .domain.telemetry import (
    AmbientLightTelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    RainfallTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    AirTemperatureTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    AcousticAltimeterTelemetrySnapshot,
    UnderwaterAcousticTelemetrySnapshot,
    BatteryTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    ImuTelemetrySnapshot,
    LocationTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    PHTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    WindTelemetrySnapshot,
)
from .domain.temperature import TemperatureTelemetrySnapshot
from .persistence_mappers import (
    buoy_snapshot as _buoy_snapshot,
)
from .device_repository import DeviceRepository
from .buoy_location_repository import BuoyLocationRepository
from .buoy_registry_repository import BuoyRegistryRepository
from .temperature_repository import TemperatureRepository
from .pressure_repository import PressureRepository
from .salinity_repository import SalinityRepository
from .imu_repository import ImuRepository
from .ambient_light_repository import AmbientLightRepository
from .wind_repository import WindRepository
from .marine_current_repository import MarineCurrentRepository
from .turbidity_repository import TurbidityRepository
from .dissolved_oxygen_repository import DissolvedOxygenRepository
from .ph_repository import PHRepository
from .conductivity_repository import ConductivityRepository
from .chlorophyll_a_repository import ChlorophyllARepository
from .rainfall_repository import RainfallRepository
from .humidity_repository import HumidityRepository
from .air_temperature_repository import AirTemperatureRepository
from .atmospheric_pressure_repository import AtmosphericPressureRepository
from .acoustic_altimeter_repository import AcousticAltimeterRepository
from .underwater_acoustic_repository import UnderwaterAcousticRepository
from .battery_repository import BatteryRepository
from .sensor_health_repository import SensorHealthRepository
from .quality_summary_repository import QualitySummaryRepository
from .persistence_utils import is_newer_timestamp


class BuoyRepository:
    """Legacy aggregate adapter retained while use cases migrate by context."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.devices = DeviceRepository(db)
        self.locations = BuoyLocationRepository(db)
        self.registry = BuoyRegistryRepository(db)
        self.temperature = TemperatureRepository(db)
        self.pressure = PressureRepository(db)
        self.salinity = SalinityRepository(db)
        self.imu = ImuRepository(db)
        self.ambient_light = AmbientLightRepository(db)
        self.wind = WindRepository(db)
        self.marine_current = MarineCurrentRepository(db)
        self.turbidity = TurbidityRepository(db)
        self.dissolved_oxygen = DissolvedOxygenRepository(db)
        self.ph = PHRepository(db)
        self.conductivity = ConductivityRepository(db)
        self.chlorophyll_a = ChlorophyllARepository(db)
        self.rainfall = RainfallRepository(db)
        self.humidity = HumidityRepository(db)
        self.air_temperature = AirTemperatureRepository(db)
        self.atmospheric_pressure = AtmosphericPressureRepository(db)
        self.acoustic_altimeter = AcousticAltimeterRepository(db)
        self.underwater_acoustic = UnderwaterAcousticRepository(db)
        self.battery = BatteryRepository(db)
        self.sensor_health = SensorHealthRepository(db)
        self.quality_summary = QualitySummaryRepository(db)

    def get_device(self, device_id: str) -> DeviceEntity | None:
        """Delegate battery ownership lookups to the device persistence adapter."""
        return self.devices.get_device(device_id)

    def get_device_snapshot(self, device_id: str) -> DeviceSnapshot | None:
        """Delegate device snapshot reads required by battery ingestion."""
        return self.devices.get_device_snapshot(device_id)

    def list_device_snapshots(self, buoy_id: str) -> list[DeviceSnapshot]:
        """Delegate device snapshots required by legacy maintenance queries."""
        return self.devices.list_device_snapshots(buoy_id)

    def mark_device_seen_by_id(
        self, device_id: str, seen_at: datetime
    ) -> DeviceSnapshot | None:
        """Delegate battery-ingestion heartbeats to the device adapter."""
        return self.devices.mark_device_seen_by_id(device_id, seen_at)

    def add_location(self, reading: LocationTelemetrySnapshot) -> BuoyLocationReadingEntity:
        return self.locations.add_location(reading)

    def list_locations(
        self,
        buoy_id: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        return self.locations.list_locations(buoy_id, limit, since, until)

    def list_all_locations(
        self,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[LocationTelemetrySnapshot]:
        return self.locations.list_all_locations(limit, since, until)

    def get_buoy(self, buoy_id: str) -> BuoyEntity | None:
        return self.registry.get_buoy(buoy_id)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def list_buoy_snapshots(self) -> list[BuoySnapshot]:
        return self.registry.list_buoy_snapshots()

    def add_temperature(
        self, reading: TemperatureTelemetrySnapshot
    ) -> TemperatureTelemetrySnapshot:
        return self.temperature.add_temperature(reading)

    def list_temperatures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TemperatureTelemetrySnapshot]:
        return self.temperature.list_temperatures(buoy_id, limit, sensor_channel)

    def latest_temperature(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> TemperatureTelemetrySnapshot | None:
        return self.temperature.latest_temperature(buoy_id, sensor_channel)

    def add_pressure(
        self, reading: PressureTelemetrySnapshot
    ) -> PressureTelemetrySnapshot:
        return self.pressure.add_pressure(reading)

    def list_pressures(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PressureTelemetrySnapshot]:
        return self.pressure.list_pressures(buoy_id, limit, sensor_channel)

    def latest_pressure(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> PressureReadingEntity | None:
        return self.pressure.latest_pressure(buoy_id, sensor_channel)

    def add_salinity(
        self, reading: SalinityTelemetrySnapshot
    ) -> SalinityTelemetrySnapshot:
        return self.salinity.add_salinity(reading)

    def list_salinity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[SalinityTelemetrySnapshot]:
        return self.salinity.list_salinity(buoy_id, limit, sensor_channel)

    def latest_salinity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> SalinityTelemetrySnapshot | None:
        return self.salinity.latest_salinity(buoy_id, sensor_channel)

    def add_imu(self, reading: ImuTelemetrySnapshot) -> ImuTelemetrySnapshot:
        return self.imu.add_imu(reading)

    def list_imu(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ImuTelemetrySnapshot]:
        return self.imu.list_imu(buoy_id, limit, sensor_channel)

    def latest_imu(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ImuTelemetrySnapshot | None:
        return self.imu.latest_imu(buoy_id, sensor_channel)

    def add_ambient_light(
        self, reading: AmbientLightTelemetrySnapshot
    ) -> AmbientLightTelemetrySnapshot:
        return self.ambient_light.add_ambient_light(reading)

    def list_ambient_light(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[AmbientLightTelemetrySnapshot]:
        return self.ambient_light.list_ambient_light(buoy_id, limit, sensor_channel)

    def latest_ambient_light(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> AmbientLightTelemetrySnapshot | None:
        return self.ambient_light.latest_ambient_light(buoy_id, sensor_channel)

    def add_wind(self, reading: WindTelemetrySnapshot) -> WindTelemetrySnapshot:
        return self.wind.add_wind(reading)

    def list_wind(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[WindTelemetrySnapshot]:
        return self.wind.list_wind(buoy_id, limit, sensor_channel)

    def latest_wind(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> WindTelemetrySnapshot | None:
        return self.wind.latest_wind(buoy_id, sensor_channel)

    def add_marine_current(
        self, reading: MarineCurrentTelemetrySnapshot
    ) -> MarineCurrentTelemetrySnapshot:
        return self.marine_current.add_marine_current(reading)

    def list_marine_current(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[MarineCurrentTelemetrySnapshot]:
        return self.marine_current.list_marine_current(
            buoy_id, limit, sensor_channel
        )

    def latest_marine_current(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> MarineCurrentTelemetrySnapshot | None:
        return self.marine_current.latest_marine_current(buoy_id, sensor_channel)

    def add_turbidity(
        self, reading: TurbidityTelemetrySnapshot
    ) -> TurbidityTelemetrySnapshot:
        return self.turbidity.add_turbidity(reading)

    def list_turbidity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[TurbidityTelemetrySnapshot]:
        return self.turbidity.list_turbidity(buoy_id, limit, sensor_channel)

    def latest_turbidity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> TurbidityTelemetrySnapshot | None:
        return self.turbidity.latest_turbidity(buoy_id, sensor_channel)

    def add_dissolved_oxygen(
        self, reading: DissolvedOxygenTelemetrySnapshot
    ) -> DissolvedOxygenTelemetrySnapshot:
        return self.dissolved_oxygen.add_dissolved_oxygen(reading)

    def list_dissolved_oxygen(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[DissolvedOxygenTelemetrySnapshot]:
        return self.dissolved_oxygen.list_dissolved_oxygen(
            buoy_id, limit, sensor_channel
        )

    def latest_dissolved_oxygen(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> DissolvedOxygenTelemetrySnapshot | None:
        return self.dissolved_oxygen.latest_dissolved_oxygen(buoy_id, sensor_channel)

    def add_ph(self, reading: PHTelemetrySnapshot) -> PHTelemetrySnapshot:
        return self.ph.add_ph(reading)

    def list_ph(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[PHTelemetrySnapshot]:
        return self.ph.list_ph(buoy_id, limit, sensor_channel)

    def latest_ph(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> PHTelemetrySnapshot | None:
        return self.ph.latest_ph(buoy_id, sensor_channel)

    def add_conductivity(
        self, reading: ConductivityTelemetrySnapshot
    ) -> ConductivityTelemetrySnapshot:
        return self.conductivity.add_conductivity(reading)

    def list_conductivity(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ConductivityTelemetrySnapshot]:
        return self.conductivity.list_conductivity(
            buoy_id, limit, sensor_channel
        )

    def latest_conductivity(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ConductivityTelemetrySnapshot | None:
        return self.conductivity.latest_conductivity(buoy_id, sensor_channel)

    def add_chlorophyll_a(
        self, reading: ChlorophyllATelemetrySnapshot
    ) -> ChlorophyllATelemetrySnapshot:
        return self.chlorophyll_a.add_chlorophyll_a(reading)

    def list_chlorophyll_a(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[ChlorophyllATelemetrySnapshot]:
        return self.chlorophyll_a.list_chlorophyll_a(
            buoy_id, limit, sensor_channel
        )

    def latest_chlorophyll_a(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> ChlorophyllATelemetrySnapshot | None:
        return self.chlorophyll_a.latest_chlorophyll_a(buoy_id, sensor_channel)

    def add_rainfall(
        self, reading: RainfallTelemetrySnapshot
    ) -> RainfallTelemetrySnapshot:
        return self.rainfall.add_rainfall(reading)

    def list_rainfall(
        self, buoy_id: str, limit: int, sensor_channel: str | None = "A"
    ) -> list[RainfallTelemetrySnapshot]:
        return self.rainfall.list_rainfall(buoy_id, limit, sensor_channel)

    def latest_rainfall(
        self, buoy_id: str, sensor_channel: str = "A"
    ) -> RainfallTelemetrySnapshot | None:
        return self.rainfall.latest_rainfall(buoy_id, sensor_channel)

    def add_humidity(
        self, reading: HumidityTelemetrySnapshot
    ) -> HumidityTelemetrySnapshot:
        return self.humidity.add_humidity(reading)

    def list_humidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[HumidityTelemetrySnapshot]:
        return self.humidity.list_humidity(buoy_id, limit, sensor_channel)

    def latest_humidity(self, buoy_id: str, sensor_channel: str = "A") -> HumidityTelemetrySnapshot | None:
        return self.humidity.latest_humidity(buoy_id, sensor_channel)

    def add_air_temperature(
        self, reading: AirTemperatureTelemetrySnapshot
    ) -> AirTemperatureTelemetrySnapshot:
        return self.air_temperature.add_air_temperature(reading)

    def list_air_temperature(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AirTemperatureTelemetrySnapshot]:
        return self.air_temperature.list_air_temperature(
            buoy_id, limit, sensor_channel
        )

    def latest_air_temperature(self, buoy_id: str, sensor_channel: str = "A") -> AirTemperatureTelemetrySnapshot | None:
        return self.air_temperature.latest_air_temperature(buoy_id, sensor_channel)

    def add_atmospheric_pressure(
        self, reading: AtmosphericPressureTelemetrySnapshot
    ) -> AtmosphericPressureTelemetrySnapshot:
        return self.atmospheric_pressure.add_atmospheric_pressure(reading)

    def list_atmospheric_pressure(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AtmosphericPressureTelemetrySnapshot]:
        return self.atmospheric_pressure.list_atmospheric_pressure(
            buoy_id, limit, sensor_channel
        )

    def latest_atmospheric_pressure(self, buoy_id: str, sensor_channel: str = "A") -> AtmosphericPressureTelemetrySnapshot | None:
        return self.atmospheric_pressure.latest_atmospheric_pressure(
            buoy_id, sensor_channel
        )

    def add_acoustic_altimeter(
        self, reading: AcousticAltimeterTelemetrySnapshot
    ) -> AcousticAltimeterTelemetrySnapshot:
        return self.acoustic_altimeter.add_acoustic_altimeter(reading)

    def list_acoustic_altimeter(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AcousticAltimeterTelemetrySnapshot]:
        return self.acoustic_altimeter.list_acoustic_altimeter(
            buoy_id, limit, sensor_channel
        )

    def add_underwater_acoustic(
        self, reading: UnderwaterAcousticTelemetrySnapshot
    ) -> UnderwaterAcousticTelemetrySnapshot:
        return self.underwater_acoustic.add_underwater_acoustic(reading)

    def list_underwater_acoustic(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[UnderwaterAcousticTelemetrySnapshot]:
        return self.underwater_acoustic.list_underwater_acoustic(
            buoy_id, limit, sensor_channel
        )

    def add_battery(
        self, reading: BatteryTelemetrySnapshot
    ) -> BatteryTelemetrySnapshot:
        return self.battery.add_battery(reading)

    def add_sensor_health_check(
        self, health: DomainSensorHealthSnapshot
    ) -> SensorHealthCheckSnapshot:
        return self.sensor_health.add_sensor_health_check(health)

    def list_sensor_health_checks(
        self, buoy_id: str, limit: int
    ) -> list[SensorHealthCheckSnapshot]:
        return self.sensor_health.list_sensor_health_checks(buoy_id, limit)

    def latest_battery(
        self,
        buoy_id: str,
        device_id: str | None = None,
        physical_device_id: str | None = None,
    ) -> BatteryReadingEntity | None:
        return self.battery.latest_battery(
            buoy_id, device_id, physical_device_id
        )

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

    def quality_counts(self, buoy_id: str) -> dict[str, int]:
        return self.quality_summary.quality_counts(buoy_id)
