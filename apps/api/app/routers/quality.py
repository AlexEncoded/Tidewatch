"""Reading quality endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import QualitySummary
from ..repository import BuoyRepository

router = APIRouter()


@router.get(
    "/api/v1/buoys/{buoy_id}/quality-summary",
    response_model=QualitySummary,
    tags=["quality"],
)
def quality_summary(buoy_id: str, db: Session = Depends(get_db)) -> QualitySummary:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    counts = repository.quality_counts(buoy_id)
    return QualitySummary(
        buoy_id=buoy_id,
        total_readings=sum(counts.values()),
        good_readings=counts["good"],
        suspect_readings=counts["suspect"],
        invalid_readings=counts["invalid"],
    )
