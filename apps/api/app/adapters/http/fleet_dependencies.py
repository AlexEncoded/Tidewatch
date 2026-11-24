"""Fleet HTTP dependency providers."""

from fastapi import Depends
from sqlalchemy.orm import Session

from ...application.device_ports import (
    DeviceHealthReader,
    DeviceListingReader,
    DeviceRegistry,
    DeviceStatusRegistry,
)
from ...application.fleet_ports import (
    BuoyLocationHistoryReader,
    BuoyLocationUpdater,
    BuoyRegistrar,
    BuoyStatusRegistry,
    BuoySummaryReader,
    FleetLocationReader,
    FleetMetrics,
    MovementAnalysisReader,
    StaleBuoyReader,
)
from ..postgres.buoy_activity_repository import BuoyActivityRepository
from ..postgres.buoy_location_repository import BuoyLocationRepository
from ..postgres.buoy_registry_repository import BuoyRegistryRepository
from ..postgres.buoy_summary_repository import BuoySummaryRepository
from ..postgres.database import get_db
from ..postgres.device_repository import DeviceRepository
from ..prometheus.fleet_metrics import PrometheusFleetMetrics


def get_buoy_summary_reader(db: Session = Depends(get_db)) -> BuoySummaryReader:
    """Compose fleet overview queries from buoy and telemetry adapters."""
    return BuoySummaryRepository(db)


def get_fleet_location_reader(db: Session = Depends(get_db)) -> FleetLocationReader:
    """Compose fleet-location queries with the location persistence adapter."""
    return BuoyLocationRepository(db)


def get_movement_analysis_reader(db: Session = Depends(get_db)) -> MovementAnalysisReader:
    """Compose movement analysis with the location persistence adapter."""
    return BuoyLocationRepository(db)


def get_buoy_location_history_reader(
    db: Session = Depends(get_db),
) -> BuoyLocationHistoryReader:
    """Compose buoy location-history queries with the location adapter."""
    return BuoyLocationRepository(db)


def get_stale_buoy_reader(db: Session = Depends(get_db)) -> StaleBuoyReader:
    """Compose stale-buoy evaluation with the fleet activity adapter."""
    return BuoyActivityRepository(db)


def get_buoy_status_registry(db: Session = Depends(get_db)) -> BuoyStatusRegistry:
    """Compose buoy status updates with the fleet registry adapter."""
    return BuoyRegistryRepository(db)


def get_buoy_location_updater(db: Session = Depends(get_db)) -> BuoyLocationUpdater:
    """Compose buoy location writes with the location persistence adapter."""
    return BuoyLocationRepository(db)


def get_buoy_registrar(db: Session = Depends(get_db)) -> BuoyRegistrar:
    """Compose buoy registration with the fleet registry adapter."""
    return BuoyRegistryRepository(db)


def get_fleet_metrics() -> FleetMetrics:
    """Compose fleet observability with its Prometheus adapter."""
    return PrometheusFleetMetrics()


def get_device_registry(db: Session = Depends(get_db)) -> DeviceRegistry:
    """Compose device registration with the SQL repository adapter."""
    return DeviceRepository(db)


def get_device_listing_reader(db: Session = Depends(get_db)) -> DeviceListingReader:
    """Compose device listing with the SQL repository adapter."""
    return DeviceRepository(db)


def get_device_health_reader(db: Session = Depends(get_db)) -> DeviceHealthReader:
    """Compose device health queries with the SQL repository adapter."""
    return DeviceRepository(db)


def get_device_status_registry(db: Session = Depends(get_db)) -> DeviceStatusRegistry:
    """Compose device status changes with the SQL repository adapter."""
    return DeviceRepository(db)
