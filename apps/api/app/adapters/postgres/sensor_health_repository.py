"""Persistence adapter composing sensor histories for health evaluations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...application.sensor_health_ports import SensorHealthCheckGateway
from .buoy_registry_repository import BuoyRegistryRepository
from ...domain.sensors.sensor_health import (
    SensorHealthCheckSnapshot,
    SensorHealthSnapshot,
)
from ...domain.sensors.pressure import PressureTelemetrySnapshot
from ...domain.sensors.temperature import TemperatureTelemetrySnapshot
from ...domain.sensors.imu import ImuTelemetrySnapshot
from ...domain.sensors.underwater_acoustic import UnderwaterAcousticTelemetrySnapshot
from ...domain.sensors.acoustic_altimeter import AcousticAltimeterTelemetrySnapshot
from ...domain.sensors.atmospheric_pressure import AtmosphericPressureTelemetrySnapshot
from ...domain.sensors.air_temperature import AirTemperatureTelemetrySnapshot
from ...domain.sensors.humidity import HumidityTelemetrySnapshot
from ...domain.sensors.rainfall import RainfallTelemetrySnapshot
from ...domain.sensors.chlorophyll_a import ChlorophyllATelemetrySnapshot
from ...domain.sensors.conductivity import ConductivityTelemetrySnapshot
from ...domain.sensors.ph import PHTelemetrySnapshot
from ...domain.sensors.dissolved_oxygen import DissolvedOxygenTelemetrySnapshot
from ...domain.sensors.turbidity import TurbidityTelemetrySnapshot
from ...domain.sensors.salinity import SalinityTelemetrySnapshot
from ...domain.sensors.marine_current import MarineCurrentTelemetrySnapshot
from ...domain.sensors.wind import WindTelemetrySnapshot
from ...domain.sensors.ambient_light import AmbientLightTelemetrySnapshot

from .sensor_entities import SensorHealthCheckEntity
from .sensor_telemetry_repositories import SensorTelemetryRepositories
from .persistence_mappers import sensor_health_check_snapshot
from ...domain.fleet.devices import SensorChannel


class SensorHealthRepository(SensorHealthCheckGateway):
    """Read sensor histories and persist redundant-health evaluations."""

    def __init__(self, db: Session) -> None:
        self.registry = BuoyRegistryRepository(db)
        self.sensors = SensorTelemetryRepositories(db)
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

    def list_temperatures(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[TemperatureTelemetrySnapshot]:
        return self.sensors.temperature.list_temperatures(buoy_id, limit, sensor_channel)

    def list_pressures(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[PressureTelemetrySnapshot]:
        return self.sensors.pressure.list_pressures(buoy_id, limit, sensor_channel)

    def list_salinity(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[SalinityTelemetrySnapshot]:
        return self.sensors.salinity.list_salinity(buoy_id, limit, sensor_channel)

    def list_imu(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[ImuTelemetrySnapshot]:
        return self.sensors.imu.list_imu(buoy_id, limit, sensor_channel)

    def list_ambient_light(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[AmbientLightTelemetrySnapshot]:
        return self.sensors.ambient_light.list_ambient_light(buoy_id, limit, sensor_channel)

    def list_wind(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[WindTelemetrySnapshot]:
        return self.sensors.wind.list_wind(buoy_id, limit, sensor_channel)

    def list_marine_current(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[MarineCurrentTelemetrySnapshot]:
        return self.sensors.marine_current.list_marine_current(buoy_id, limit, sensor_channel)

    def list_turbidity(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[TurbidityTelemetrySnapshot]:
        return self.sensors.turbidity.list_turbidity(buoy_id, limit, sensor_channel)

    def list_dissolved_oxygen(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[DissolvedOxygenTelemetrySnapshot]:
        return self.sensors.dissolved_oxygen.list_dissolved_oxygen(buoy_id, limit, sensor_channel)

    def list_ph(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[PHTelemetrySnapshot]:
        return self.sensors.ph.list_ph(buoy_id, limit, sensor_channel)

    def list_conductivity(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[ConductivityTelemetrySnapshot]:
        return self.sensors.conductivity.list_conductivity(buoy_id, limit, sensor_channel)

    def list_chlorophyll_a(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[ChlorophyllATelemetrySnapshot]:
        return self.sensors.chlorophyll_a.list_chlorophyll_a(buoy_id, limit, sensor_channel)

    def list_rainfall(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[RainfallTelemetrySnapshot]:
        return self.sensors.rainfall.list_rainfall(buoy_id, limit, sensor_channel)

    def list_humidity(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[HumidityTelemetrySnapshot]:
        return self.sensors.humidity.list_humidity(buoy_id, limit, sensor_channel)

    def list_air_temperature(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[AirTemperatureTelemetrySnapshot]:
        return self.sensors.air_temperature.list_air_temperature(buoy_id, limit, sensor_channel)

    def list_atmospheric_pressure(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[AtmosphericPressureTelemetrySnapshot]:
        return self.sensors.atmospheric_pressure.list_atmospheric_pressure(buoy_id, limit, sensor_channel)

    def list_acoustic_altimeter(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[AcousticAltimeterTelemetrySnapshot]:
        return self.sensors.acoustic_altimeter.list_acoustic_altimeter(buoy_id, limit, sensor_channel)

    def list_underwater_acoustic(self, buoy_id: str, limit: int, sensor_channel: SensorChannel | None = "A") -> list[UnderwaterAcousticTelemetrySnapshot]:
        return self.sensors.underwater_acoustic.list_underwater_acoustic(buoy_id, limit, sensor_channel)
