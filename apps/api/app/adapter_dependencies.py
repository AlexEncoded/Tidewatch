"""HTTP adapter dependency providers and infrastructure composition."""

from fastapi import Depends
from sqlalchemy.orm import Session

from .application.ports import (
    BuoyLocationHistoryReader,
    BuoyRegistrar,
    BuoyStatusRegistry,
    BuoyLocationUpdater,
    BatteryTelemetryReader,
    TemperatureTelemetryGateway,
    PressureTelemetryGateway,
    SalinityTelemetryGateway,
    ImuTelemetryGateway,
    AmbientLightTelemetryGateway,
    WindTelemetryGateway,
    MarineCurrentTelemetryGateway,
    TurbidityTelemetryGateway,
    DissolvedOxygenTelemetryGateway,
    PHTelemetryGateway,
    ConductivityTelemetryGateway,
    ChlorophyllATelemetryGateway,
    RainfallTelemetryGateway,
    HumidityTelemetryGateway,
    AirTemperatureTelemetryGateway,
    AtmosphericPressureTelemetryGateway,
    AcousticAltimeterTelemetryGateway,
    UnderwaterAcousticTelemetryGateway,
    StaleBuoyReader,
    DeviceHealthReader,
    FleetLocationReader,
    MovementAnalysisReader,
    PressureAnalysisReader,
    WaveAnalysisReader,
    TemperatureAnalysisReader,
    TemperatureAlertsReader,
    TemperatureAlertStore,
    QualitySummaryReader,
    SensorHealthReader,
    SensorHealthCheckGateway,
    TelemetryIngestionGateway,
    MaintenanceReader,
    DatabaseHealthReader,
    BuoySummaryReader,
)
from .application.device_listing import DeviceListingReader
from .application.device_registration import DeviceRegistry
from .application.device_status import DeviceStatusRegistry
from .database import get_db
from .database_health import SQLDatabaseHealthReader
from .device_repository import DeviceRepository
from .buoy_activity_repository import BuoyActivityRepository
from .buoy_location_repository import BuoyLocationRepository
from .buoy_registry_repository import BuoyRegistryRepository
from .buoy_summary_repository import BuoySummaryRepository
from .repository import BuoyRepository
from .temperature_alert_repository import TemperatureAlertRepository
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


def get_quality_summary_reader(
    db: Session = Depends(get_db),
) -> QualitySummaryReader:
    """Compose the quality-summary input port with its SQL adapter."""
    return BuoyRepository(db)


def get_sensor_health_reader(
    db: Session = Depends(get_db),
) -> SensorHealthReader:
    """Compose redundant sensor-health queries with the SQL adapter."""
    return BuoyRepository(db)


def get_sensor_health_check_gateway(
    db: Session = Depends(get_db),
) -> SensorHealthCheckGateway:
    """Compose sensor-health evaluation and persistence with the SQL adapter."""
    return BuoyRepository(db)


def get_telemetry_ingestion_gateway(
    db: Session = Depends(get_db),
) -> TelemetryIngestionGateway:
    """Compose batch telemetry writes with the SQL repository adapter."""
    return BuoyRepository(db)


def get_maintenance_reader(
    db: Session = Depends(get_db),
) -> MaintenanceReader:
    """Compose fleet maintenance queries with the SQL repository adapter."""
    return BuoyRepository(db)


def get_database_health_reader(
    db: Session = Depends(get_db),
) -> DatabaseHealthReader:
    """Compose database-health checks with the SQL adapter."""
    return SQLDatabaseHealthReader(db)


def get_buoy_summary_reader(
    db: Session = Depends(get_db),
) -> BuoySummaryReader:
    """Compose fleet overview queries from buoy and telemetry adapters."""
    return BuoySummaryRepository(db)


def get_fleet_location_reader(
    db: Session = Depends(get_db),
) -> FleetLocationReader:
    """Compose fleet-location queries with the location persistence adapter."""
    return BuoyLocationRepository(db)


def get_movement_analysis_reader(
    db: Session = Depends(get_db),
) -> MovementAnalysisReader:
    """Compose movement analysis with the location persistence adapter."""
    return BuoyLocationRepository(db)


def get_buoy_location_history_reader(
    db: Session = Depends(get_db),
) -> BuoyLocationHistoryReader:
    """Compose buoy location-history queries with the location adapter."""
    return BuoyLocationRepository(db)


def get_stale_buoy_reader(
    db: Session = Depends(get_db),
) -> StaleBuoyReader:
    """Compose stale-buoy evaluation with the fleet activity adapter."""
    return BuoyActivityRepository(db)


def get_buoy_status_registry(
    db: Session = Depends(get_db),
) -> BuoyStatusRegistry:
    """Compose buoy status updates with the fleet registry adapter."""
    return BuoyRegistryRepository(db)


def get_buoy_location_updater(
    db: Session = Depends(get_db),
) -> BuoyLocationUpdater:
    """Compose buoy location writes with the location persistence adapter."""
    return BuoyLocationRepository(db)


def get_buoy_registrar(
    db: Session = Depends(get_db),
) -> BuoyRegistrar:
    """Compose buoy registration with the fleet registry adapter."""
    return BuoyRegistryRepository(db)


def get_battery_telemetry_reader(
    db: Session = Depends(get_db),
) -> BatteryTelemetryReader:
    """Compose battery telemetry operations with the SQL repository adapter."""
    return BatteryRepository(db)


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


def get_pressure_analysis_reader(
    db: Session = Depends(get_db),
) -> PressureAnalysisReader:
    """Compose pressure analysis with its SQL telemetry adapter."""
    return PressureRepository(db)


def get_wave_analysis_reader(
    db: Session = Depends(get_db),
) -> WaveAnalysisReader:
    """Compose wave analysis through the compatibility telemetry facade."""
    return BuoyRepository(db)


def get_temperature_analysis_reader(
    db: Session = Depends(get_db),
) -> TemperatureAnalysisReader:
    """Compose temperature analysis with its SQL telemetry adapter."""
    return TemperatureRepository(db)


def get_temperature_alerts_reader(
    db: Session = Depends(get_db),
) -> TemperatureAlertsReader:
    """Compose fleet temperature-alert queries with the alert adapter."""
    return TemperatureAlertRepository(db)


def get_temperature_alert_store(
    db: Session = Depends(get_db),
) -> TemperatureAlertStore:
    """Compose temperature-alert use cases with the alert persistence adapter."""
    return TemperatureAlertRepository(db)


def get_device_registry(
    db: Session = Depends(get_db),
) -> DeviceRegistry:
    """Compose device registration with the SQL repository adapter."""
    return DeviceRepository(db)


def get_device_listing_reader(
    db: Session = Depends(get_db),
) -> DeviceListingReader:
    """Compose device listing with the SQL repository adapter."""
    return DeviceRepository(db)


def get_device_health_reader(
    db: Session = Depends(get_db),
) -> DeviceHealthReader:
    """Compose device health queries with the SQL repository adapter."""
    return DeviceRepository(db)


def get_device_status_registry(
    db: Session = Depends(get_db),
) -> DeviceStatusRegistry:
    """Compose device status changes with the SQL repository adapter."""
    return DeviceRepository(db)
