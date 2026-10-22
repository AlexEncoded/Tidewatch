"""Persistence adapter composing sensor histories for health evaluations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .ambient_light_repository import AmbientLightRepository
from .atmospheric_pressure_repository import AtmosphericPressureRepository
from .acoustic_altimeter_repository import AcousticAltimeterRepository
from .buoy_registry_repository import BuoyRegistryRepository
from .chlorophyll_a_repository import ChlorophyllARepository
from .conductivity_repository import ConductivityRepository
from .dissolved_oxygen_repository import DissolvedOxygenRepository
from .domain.sensor_health import (
    SensorHealthCheckSnapshot,
    SensorHealthSnapshot,
)
from .domain.pressure import PressureTelemetrySnapshot
from .domain.temperature import TemperatureTelemetrySnapshot
from .domain.telemetry import (
    AcousticAltimeterTelemetrySnapshot,
    AirTemperatureTelemetrySnapshot,
    AmbientLightTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    ImuTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    PHTelemetrySnapshot,
    RainfallTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    UnderwaterAcousticTelemetrySnapshot,
    WindTelemetrySnapshot,
)
from .sensor_entities import SensorHealthCheckEntity
from .temperature_repository import TemperatureRepository
from .humidity_repository import HumidityRepository
from .air_temperature_repository import AirTemperatureRepository
from .imu_repository import ImuRepository
from .marine_current_repository import MarineCurrentRepository
from .persistence_mappers import sensor_health_check_snapshot
from .ph_repository import PHRepository
from .pressure_repository import PressureRepository
from .rainfall_repository import RainfallRepository
from .salinity_repository import SalinityRepository
from .turbidity_repository import TurbidityRepository
from .underwater_acoustic_repository import UnderwaterAcousticRepository
from .wind_repository import WindRepository


class SensorHealthRepository:
    """Read sensor histories and persist redundant-health evaluations."""

    def __init__(self, db: Session) -> None:
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
        self.db = db

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def list_sensor_health_checks(
        self, buoy_id: str, limit: int
    ) -> list[SensorHealthCheckSnapshot]:
        query = (
            select(SensorHealthCheckEntity)
            .where(SensorHealthCheckEntity.buoy_id == buoy_id)
            .order_by(SensorHealthCheckEntity.checked_at.desc())
            .limit(limit)
        )
        return [
            sensor_health_check_snapshot(entity)
            for entity in self.db.scalars(query).all()
        ]

    def add_sensor_health_check(
        self, health: SensorHealthSnapshot
    ) -> SensorHealthCheckSnapshot:
        entity = SensorHealthCheckEntity(
            buoy_id=health.buoy_id,
            status=health.status,
            temperature_delta_celsius=health.temperature_delta_celsius,
            pressure_delta_kpa=health.pressure_delta_kpa,
            salinity_delta_psu=health.salinity_delta_psu,
            imu_acceleration_delta_mps2=health.imu_acceleration_delta_mps2,
            ambient_light_delta_lux=health.ambient_light_delta_lux,
            wind_speed_delta_mps=health.wind_speed_delta_mps,
            wind_direction_delta_degrees=health.wind_direction_delta_degrees,
            marine_current_speed_delta_mps=health.marine_current_speed_delta_mps,
            marine_current_direction_delta_degrees=health.marine_current_direction_delta_degrees,
            turbidity_delta_ntu=health.turbidity_delta_ntu,
            dissolved_oxygen_delta_mg_l=health.dissolved_oxygen_delta_mg_l,
            ph_delta=health.ph_delta,
            conductivity_delta_us_cm=health.conductivity_delta_us_cm,
            chlorophyll_a_delta_ug_l=health.chlorophyll_a_delta_ug_l,
            rainfall_delta_mm_h=health.rainfall_delta_mm_h,
            humidity_delta_percent=health.humidity_delta_percent,
            air_temperature_delta_celsius=health.air_temperature_delta_celsius,
            atmospheric_pressure_delta_kpa=health.atmospheric_pressure_delta_kpa,
            acoustic_altimeter_delta_meters=health.acoustic_altimeter_delta_meters,
            underwater_acoustic_delta_db=health.underwater_acoustic_delta_db,
            degraded_sensors=health.degraded_sensors,
            missing_sensors=health.missing_sensors,
            decisions=health.decisions,
            checked_at=health.checked_at,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return sensor_health_check_snapshot(entity)

    def list_temperatures(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[TemperatureTelemetrySnapshot]:
        return self.temperature.list_temperatures(buoy_id, limit, sensor_channel)

    def list_pressures(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[PressureTelemetrySnapshot]:
        return self.pressure.list_pressures(buoy_id, limit, sensor_channel)

    def list_salinity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[SalinityTelemetrySnapshot]:
        return self.salinity.list_salinity(buoy_id, limit, sensor_channel)

    def list_imu(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[ImuTelemetrySnapshot]:
        return self.imu.list_imu(buoy_id, limit, sensor_channel)

    def list_ambient_light(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AmbientLightTelemetrySnapshot]:
        return self.ambient_light.list_ambient_light(buoy_id, limit, sensor_channel)

    def list_wind(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[WindTelemetrySnapshot]:
        return self.wind.list_wind(buoy_id, limit, sensor_channel)

    def list_marine_current(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[MarineCurrentTelemetrySnapshot]:
        return self.marine_current.list_marine_current(buoy_id, limit, sensor_channel)

    def list_turbidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[TurbidityTelemetrySnapshot]:
        return self.turbidity.list_turbidity(buoy_id, limit, sensor_channel)

    def list_dissolved_oxygen(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[DissolvedOxygenTelemetrySnapshot]:
        return self.dissolved_oxygen.list_dissolved_oxygen(buoy_id, limit, sensor_channel)

    def list_ph(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[PHTelemetrySnapshot]:
        return self.ph.list_ph(buoy_id, limit, sensor_channel)

    def list_conductivity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[ConductivityTelemetrySnapshot]:
        return self.conductivity.list_conductivity(buoy_id, limit, sensor_channel)

    def list_chlorophyll_a(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[ChlorophyllATelemetrySnapshot]:
        return self.chlorophyll_a.list_chlorophyll_a(buoy_id, limit, sensor_channel)

    def list_rainfall(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[RainfallTelemetrySnapshot]:
        return self.rainfall.list_rainfall(buoy_id, limit, sensor_channel)

    def list_humidity(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[HumidityTelemetrySnapshot]:
        return self.humidity.list_humidity(buoy_id, limit, sensor_channel)

    def list_air_temperature(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AirTemperatureTelemetrySnapshot]:
        return self.air_temperature.list_air_temperature(buoy_id, limit, sensor_channel)

    def list_atmospheric_pressure(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AtmosphericPressureTelemetrySnapshot]:
        return self.atmospheric_pressure.list_atmospheric_pressure(buoy_id, limit, sensor_channel)

    def list_acoustic_altimeter(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[AcousticAltimeterTelemetrySnapshot]:
        return self.acoustic_altimeter.list_acoustic_altimeter(buoy_id, limit, sensor_channel)

    def list_underwater_acoustic(self, buoy_id: str, limit: int, sensor_channel: str | None = "A") -> list[UnderwaterAcousticTelemetrySnapshot]:
        return self.underwater_acoustic.list_underwater_acoustic(buoy_id, limit, sensor_channel)
