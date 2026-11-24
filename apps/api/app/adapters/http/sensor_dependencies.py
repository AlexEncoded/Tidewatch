"""Sensors HTTP dependency providers."""

from fastapi import Depends
from sqlalchemy.orm import Session
from ...application.battery_ports import BatteryMetrics, BatteryTelemetryReader
from ...application.sensor_health_ports import (
    SensorHealthCheckGateway,
    SensorHealthMetrics,
    SensorHealthReader,
)
from ...application.ambient_light_ports import AmbientLightTelemetryGateway
from ...application.motion_ports import ImuTelemetryGateway
from ...application.flow_ports import MarineCurrentTelemetryGateway, WindTelemetryGateway
from ...application.marine_water_ports import (
    PressureTelemetryGateway,
    SalinityTelemetryGateway,
    TemperatureTelemetryGateway,
)
from ...application.acoustic_sensor_ports import (
    AcousticAltimeterTelemetryGateway,
    UnderwaterAcousticTelemetryGateway,
)
from ...application.weather_ports import (
    AirTemperatureTelemetryGateway,
    AtmosphericPressureTelemetryGateway,
    HumidityTelemetryGateway,
    RainfallTelemetryGateway,
)
from ...application.water_quality_ports import (
    ChlorophyllATelemetryGateway,
    ConductivityTelemetryGateway,
    DissolvedOxygenTelemetryGateway,
    PHTelemetryGateway,
    TurbidityTelemetryGateway,
)
from ..postgres.database import get_db
from ..postgres.temperature_repository import TemperatureRepository
from ..postgres.pressure_repository import PressureRepository
from ..postgres.salinity_repository import SalinityRepository
from ..postgres.imu_repository import ImuRepository
from ..postgres.ambient_light_repository import AmbientLightRepository
from ..postgres.wind_repository import WindRepository
from ..postgres.marine_current_repository import MarineCurrentRepository
from ..postgres.turbidity_repository import TurbidityRepository
from ..postgres.dissolved_oxygen_repository import DissolvedOxygenRepository
from ..postgres.ph_repository import PHRepository
from ..postgres.conductivity_repository import ConductivityRepository
from ..postgres.chlorophyll_a_repository import ChlorophyllARepository
from ..postgres.rainfall_repository import RainfallRepository
from ..postgres.humidity_repository import HumidityRepository
from ..postgres.air_temperature_repository import AirTemperatureRepository
from ..postgres.atmospheric_pressure_repository import AtmosphericPressureRepository
from ..postgres.acoustic_altimeter_repository import AcousticAltimeterRepository
from ..postgres.underwater_acoustic_repository import UnderwaterAcousticRepository
from ..postgres.battery_repository import BatteryRepository
from ..postgres.sensor_health_repository import SensorHealthRepository
from ..prometheus.battery_metrics import PrometheusBatteryMetrics
from ..prometheus.sensor_health_metrics import PrometheusSensorHealthMetrics



def get_sensor_health_reader(
    db: Session = Depends(get_db),
) -> SensorHealthReader:
    """Compose redundant sensor-health queries with the SQL adapter."""
    return SensorHealthRepository(db)


def get_sensor_health_metrics() -> SensorHealthMetrics:
    """Compose sensor-health observability with its Prometheus adapter."""
    return PrometheusSensorHealthMetrics()


def get_sensor_health_check_gateway(
    db: Session = Depends(get_db),
) -> SensorHealthCheckGateway:
    """Compose sensor-health evaluation and persistence with the SQL adapter."""
    return SensorHealthRepository(db)


def get_battery_telemetry_reader(
    db: Session = Depends(get_db),
) -> BatteryTelemetryReader:
    """Compose battery telemetry operations with the SQL repository adapter."""
    return BatteryRepository(db)


def get_battery_metrics() -> BatteryMetrics:
    """Compose battery observability with its Prometheus adapter."""
    return PrometheusBatteryMetrics()


def get_temperature_telemetry_gateway(
    db: Session = Depends(get_db),
) -> TemperatureTelemetryGateway:
    """Compose temperature telemetry reads and writes with its SQL adapter."""
    return TemperatureRepository(db)


def get_pressure_telemetry_gateway(
    db: Session = Depends(get_db),
) -> PressureTelemetryGateway:
    """Compose pressure telemetry reads and writes with its SQL adapter."""
    return PressureRepository(db)


def get_salinity_telemetry_gateway(
    db: Session = Depends(get_db),
) -> SalinityTelemetryGateway:
    """Compose salinity telemetry reads and writes with its SQL adapter."""
    return SalinityRepository(db)


def get_imu_telemetry_gateway(
    db: Session = Depends(get_db),
) -> ImuTelemetryGateway:
    """Compose IMU telemetry reads and writes with its SQL adapter."""
    return ImuRepository(db)


def get_ambient_light_telemetry_gateway(
    db: Session = Depends(get_db),
) -> AmbientLightTelemetryGateway:
    """Compose ambient-light reads and writes with their SQL adapter."""
    return AmbientLightRepository(db)


def get_wind_telemetry_gateway(
    db: Session = Depends(get_db),
) -> WindTelemetryGateway:
    """Compose wind telemetry reads and writes with its SQL adapter."""
    return WindRepository(db)


def get_marine_current_telemetry_gateway(
    db: Session = Depends(get_db),
) -> MarineCurrentTelemetryGateway:
    """Compose marine-current telemetry operations with its SQL adapter."""
    return MarineCurrentRepository(db)


def get_turbidity_telemetry_gateway(
    db: Session = Depends(get_db),
) -> TurbidityTelemetryGateway:
    """Compose turbidity telemetry operations with its SQL adapter."""
    return TurbidityRepository(db)


def get_dissolved_oxygen_telemetry_gateway(
    db: Session = Depends(get_db),
) -> DissolvedOxygenTelemetryGateway:
    """Compose dissolved-oxygen telemetry operations with its SQL adapter."""
    return DissolvedOxygenRepository(db)


def get_ph_telemetry_gateway(
    db: Session = Depends(get_db),
) -> PHTelemetryGateway:
    """Compose pH telemetry operations with their SQL adapter."""
    return PHRepository(db)


def get_conductivity_telemetry_gateway(
    db: Session = Depends(get_db),
) -> ConductivityTelemetryGateway:
    """Compose conductivity telemetry operations with the SQL adapter."""
    return ConductivityRepository(db)


def get_chlorophyll_a_telemetry_gateway(
    db: Session = Depends(get_db),
) -> ChlorophyllATelemetryGateway:
    """Compose chlorophyll-a telemetry operations with the SQL adapter."""
    return ChlorophyllARepository(db)


def get_rainfall_telemetry_gateway(
    db: Session = Depends(get_db),
) -> RainfallTelemetryGateway:
    """Compose rainfall telemetry operations with the SQL adapter."""
    return RainfallRepository(db)


def get_humidity_telemetry_gateway(
    db: Session = Depends(get_db),
) -> HumidityTelemetryGateway:
    """Compose humidity telemetry operations with the SQL adapter."""
    return HumidityRepository(db)


def get_air_temperature_telemetry_gateway(
    db: Session = Depends(get_db),
) -> AirTemperatureTelemetryGateway:
    """Compose air-temperature telemetry operations with the SQL adapter."""
    return AirTemperatureRepository(db)


def get_atmospheric_pressure_telemetry_gateway(
    db: Session = Depends(get_db),
) -> AtmosphericPressureTelemetryGateway:
    """Compose atmospheric-pressure telemetry operations with the SQL adapter."""
    return AtmosphericPressureRepository(db)


def get_acoustic_altimeter_telemetry_gateway(
    db: Session = Depends(get_db),
) -> AcousticAltimeterTelemetryGateway:
    """Compose acoustic-altimeter telemetry operations with the SQL adapter."""
    return AcousticAltimeterRepository(db)


def get_underwater_acoustic_telemetry_gateway(
    db: Session = Depends(get_db),
) -> UnderwaterAcousticTelemetryGateway:
    """Compose underwater-acoustic telemetry operations with the SQL adapter."""
    return UnderwaterAcousticRepository(db)
