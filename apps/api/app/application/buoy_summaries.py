"""Application query for buoy fleet summaries."""

from ..domain.buoy import BuoySummarySnapshot
from ..domain.sensor_selection import select_summary_reading
from .fleet_ports import BuoySummaryReader


def list_buoy_summaries(reader: BuoySummaryReader) -> list[BuoySummarySnapshot]:
    """Load summaries and select the best-quality channel for each latest field."""
    summaries = reader.list_buoy_summaries()
    return [
        BuoySummarySnapshot(
            buoy=summary.buoy,
            latest_readings={
                family: {
                    **channels,
                    "latest": select_summary_reading(
                        channels.get("A"), channels.get("B")
                    ),
                }
                for family, channels in summary.latest_readings.items()
            },
        )
        for summary in summaries
    ]
