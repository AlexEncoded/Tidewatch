"""Rainfall telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .reading_quality import ReadingQuality
from .devices import SensorChannel

RAINFALL_MIN_MM_H = 0
RAINFALL_MAX_MM_H = 500


@dataclass(frozen=True)
class RainfallTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one rainfall sample."""

    buoy_id: str
    rainfall_mm_h: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not RAINFALL_MIN_MM_H <= self.rainfall_mm_h <= RAINFALL_MAX_MM_H:
            raise ValueError(
                f"Rainfall must be between {RAINFALL_MIN_MM_H} and "
                f"{RAINFALL_MAX_MM_H} mm/h"
            )
