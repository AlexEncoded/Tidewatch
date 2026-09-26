"""Application service for reading-quality summaries."""

from ..domain.quality import QualitySummarySnapshot
from .ports import QualitySummaryReader


def summarize_quality(
    reader: QualitySummaryReader,
    buoy_id: str,
) -> QualitySummarySnapshot | None:
    """Build a quality summary through the persistence port."""
    if not reader.buoy_exists(buoy_id):
        return None
    counts = reader.quality_counts(buoy_id)
    return QualitySummarySnapshot(
        buoy_id=buoy_id,
        total_readings=sum(counts.values()),
        good_readings=counts["good"],
        suspect_readings=counts["suspect"],
        invalid_readings=counts["invalid"],
    )
