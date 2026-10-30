"""Domain result for telemetry quality aggregation."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class QualitySummarySnapshot:
    buoy_id: str
    total_readings: int
    good_readings: int
    suspect_readings: int
    invalid_readings: int

    def __post_init__(self) -> None:
        counts = (self.good_readings, self.suspect_readings, self.invalid_readings)
        if any(count < 0 for count in counts):
            raise ValueError("quality reading counts cannot be negative")
        if self.total_readings != sum(counts):
            raise ValueError("total readings must equal the sum of quality counts")


def summarize_quality_counts(
    buoy_id: str,
    counts: Mapping[str, int],
) -> QualitySummarySnapshot:
    """Build a summary from the three recognized quality categories."""
    good = counts["good"]
    suspect = counts["suspect"]
    invalid = counts["invalid"]
    return QualitySummarySnapshot(
        buoy_id=buoy_id,
        total_readings=good + suspect + invalid,
        good_readings=good,
        suspect_readings=suspect,
        invalid_readings=invalid,
    )
