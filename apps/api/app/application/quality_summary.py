"""Application service for reading-quality summaries."""

from ..models import QualitySummary
from .ports import QualitySummaryReader


def summarize_quality(reader: QualitySummaryReader, buoy_id: str) -> QualitySummary:
    """Build a quality summary through the persistence port."""
    counts = reader.quality_counts(buoy_id)
    return QualitySummary(
        buoy_id=buoy_id,
        total_readings=sum(counts.values()),
        good_readings=counts["good"],
        suspect_readings=counts["suspect"],
        invalid_readings=counts["invalid"],
    )
