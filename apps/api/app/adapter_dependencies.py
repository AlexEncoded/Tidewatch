"""HTTP adapter dependency providers and infrastructure composition."""

from fastapi import Depends
from sqlalchemy.orm import Session

from .application.ports import (
    FleetLocationReader,
    MovementAnalysisReader,
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
