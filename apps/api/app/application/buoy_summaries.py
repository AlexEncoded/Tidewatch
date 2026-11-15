"""Application query for buoy fleet summaries."""

from ..domain.buoy import BuoySummarySnapshot
from .fleet_ports import BuoySummaryReader


def list_buoy_summaries(reader: BuoySummaryReader) -> list[BuoySummarySnapshot]:
    """Load fleet summary snapshots through the application input port."""
    return reader.list_buoy_summaries()
