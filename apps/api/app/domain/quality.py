"""Domain result for telemetry quality aggregation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QualitySummarySnapshot:
    buoy_id: str
    total_readings: int
    good_readings: int
    suspect_readings: int
    invalid_readings: int
