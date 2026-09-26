"""HTTP adapter dependency providers and infrastructure composition."""

from fastapi import Depends
from sqlalchemy.orm import Session

from .application.ports import QualitySummaryReader
from .database import get_db
from .repository import BuoyRepository


def get_quality_summary_reader(
    db: Session = Depends(get_db),
) -> QualitySummaryReader:
    """Compose the quality-summary input port with its SQL adapter."""
    return BuoyRepository(db)
