"""Reading quality endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..adapter_dependencies import get_quality_summary_reader
from ..application.ports import QualitySummaryReader
from ..application.quality_summary import summarize_quality
from ..schemas.quality import QualitySummary

router = APIRouter()


@router.get(
    "/api/v1/buoys/{buoy_id}/quality-summary",
    response_model=QualitySummary,
    tags=["quality"],
)
def quality_summary(
    buoy_id: str,
    reader: QualitySummaryReader = Depends(get_quality_summary_reader),
) -> QualitySummary:
    summary = summarize_quality(reader, buoy_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    return QualitySummary.model_validate(summary, from_attributes=True)
