"""HTTP contract for buoy telemetry quality summaries."""

from pydantic import BaseModel


class QualitySummary(BaseModel):
    buoy_id: str
    total_readings: int
    good_readings: int
    suspect_readings: int
    invalid_readings: int
