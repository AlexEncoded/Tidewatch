"""HTTP adapter dependency providers and infrastructure composition."""

from fastapi import Depends
from sqlalchemy.orm import Session

from .application.ports import (
    FleetLocationReader,
    MovementAnalysisReader,
    PressureAnalysisReader,
    WaveAnalysisReader,
    TemperatureAnalysisReader,
    TemperatureAlertsReader,
    QualitySummaryReader,
)
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
