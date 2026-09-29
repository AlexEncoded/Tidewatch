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
)
from .application.device_listing import DeviceListingReader
from .application.device_registration import DeviceRegistry
from .application.device_status import DeviceStatusRegistry
from .database import get_db
from .repository import BuoyRepository


def get_quality_summary_reader(
    db: Session = Depends(get_db),
) -> QualitySummaryReader:
    """Compose the quality-summary input port with its SQL adapter."""
    return BuoyRepository(db)


def get_fleet_location_reader(
    db: Session = Depends(get_db),
) -> FleetLocationReader:
    """Compose fleet-location queries with the SQL repository adapter."""
    return BuoyRepository(db)


def get_movement_analysis_reader(
    db: Session = Depends(get_db),
) -> MovementAnalysisReader:
    """Compose movement analysis with the SQL repository adapter."""
    return BuoyRepository(db)


def get_buoy_location_history_reader(
    db: Session = Depends(get_db),
) -> BuoyLocationHistoryReader:
    """Compose buoy location-history queries with the SQL repository adapter."""
    return BuoyRepository(db)


def get_stale_buoy_reader(
    db: Session = Depends(get_db),
) -> StaleBuoyReader:
    """Compose stale-buoy evaluation with the SQL repository adapter."""
    return BuoyRepository(db)


def get_buoy_status_registry(
    db: Session = Depends(get_db),
) -> BuoyStatusRegistry:
    """Compose buoy status updates with the SQL repository adapter."""
    return BuoyRepository(db)


def get_buoy_location_updater(
    db: Session = Depends(get_db),
) -> BuoyLocationUpdater:
    """Compose buoy location writes with the SQL repository adapter."""
    return BuoyRepository(db)


def get_buoy_registrar(
    db: Session = Depends(get_db),
) -> BuoyRegistrar:
    """Compose buoy registration with the SQL repository adapter."""
    return BuoyRepository(db)


def get_battery_telemetry_reader(
    db: Session = Depends(get_db),
) -> BatteryTelemetryReader:
    """Compose battery telemetry operations with the SQL repository adapter."""
    return BuoyRepository(db)


def get_temperature_telemetry_gateway(
    db: Session = Depends(get_db),
) -> TemperatureTelemetryGateway:
    """Compose temperature telemetry reads and writes with the SQL adapter."""
    return BuoyRepository(db)


def get_pressure_telemetry_gateway(
    db: Session = Depends(get_db),
) -> PressureTelemetryGateway:
    """Compose pressure telemetry reads and writes with the SQL adapter."""
    return BuoyRepository(db)


def get_salinity_telemetry_gateway(
    db: Session = Depends(get_db),
) -> SalinityTelemetryGateway:
    """Compose salinity telemetry reads and writes with the SQL adapter."""
    return BuoyRepository(db)


def get_imu_telemetry_gateway(
    db: Session = Depends(get_db),
) -> ImuTelemetryGateway:
    """Compose IMU telemetry reads and writes with the SQL adapter."""
    return BuoyRepository(db)


def get_ambient_light_telemetry_gateway(
    db: Session = Depends(get_db),
) -> AmbientLightTelemetryGateway:
    """Compose ambient-light telemetry reads and writes with the SQL adapter."""
    return BuoyRepository(db)


def get_wind_telemetry_gateway(
    db: Session = Depends(get_db),
) -> WindTelemetryGateway:
    """Compose wind telemetry reads and writes with the SQL adapter."""
    return BuoyRepository(db)


def get_marine_current_telemetry_gateway(
    db: Session = Depends(get_db),
) -> MarineCurrentTelemetryGateway:
    """Compose marine-current telemetry operations with the SQL adapter."""
    return BuoyRepository(db)


def get_turbidity_telemetry_gateway(
    db: Session = Depends(get_db),
) -> TurbidityTelemetryGateway:
    """Compose turbidity telemetry operations with the SQL adapter."""
    return BuoyRepository(db)


def get_pressure_analysis_reader(
    db: Session = Depends(get_db),
) -> PressureAnalysisReader:
    """Compose pressure analysis with the SQL repository adapter."""
    return BuoyRepository(db)


def get_wave_analysis_reader(
    db: Session = Depends(get_db),
) -> WaveAnalysisReader:
    """Compose wave analysis with its location/IMU SQL reader."""
    return BuoyRepository(db)


def get_temperature_analysis_reader(
    db: Session = Depends(get_db),
) -> TemperatureAnalysisReader:
    """Compose temperature analysis with its SQL telemetry adapter."""
    return BuoyRepository(db)


def get_temperature_alerts_reader(
    db: Session = Depends(get_db),
) -> TemperatureAlertsReader:
    """Compose fleet temperature-alert queries with the SQL adapter."""
    return BuoyRepository(db)


def get_temperature_alert_store(
    db: Session = Depends(get_db),
) -> TemperatureAlertStore:
    """Compose temperature-alert use cases with the SQL repository adapter."""
    return BuoyRepository(db)


def get_device_registry(
    db: Session = Depends(get_db),
) -> DeviceRegistry:
    """Compose device registration with the SQL repository adapter."""
    return BuoyRepository(db)


def get_device_listing_reader(
    db: Session = Depends(get_db),
) -> DeviceListingReader:
    """Compose device listing with the SQL repository adapter."""
    return BuoyRepository(db)


def get_device_health_reader(
    db: Session = Depends(get_db),
) -> DeviceHealthReader:
    """Compose device health queries with the SQL repository adapter."""
    return BuoyRepository(db)


def get_device_status_registry(
    db: Session = Depends(get_db),
) -> DeviceStatusRegistry:
    """Compose device status changes with the SQL repository adapter."""
    return BuoyRepository(db)
