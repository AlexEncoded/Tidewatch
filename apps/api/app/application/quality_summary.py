"""Application service for reading-quality summaries."""

from ..domain.quality import QualitySummarySnapshot, summarize_quality_counts
from .quality_ports import QualitySummaryReader


def summarize_quality(
    reader: QualitySummaryReader,
    buoy_id: str,
) -> QualitySummarySnapshot | None:
    """Build a quality summary through the persistence port."""
    if not reader.buoy_exists(buoy_id):
        return None
    return summarize_quality_counts(buoy_id, reader.quality_counts(buoy_id))
