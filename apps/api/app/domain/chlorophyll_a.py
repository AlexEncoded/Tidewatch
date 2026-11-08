"""Chlorophyll-a telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .reading_quality import ReadingQuality
from .devices import SensorChannel

CHLOROPHYLL_A_MIN_UG_L = 0
CHLOROPHYLL_A_MAX_UG_L = 1000


@dataclass(frozen=True)
class ChlorophyllATelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one chlorophyll-a sample."""

    buoy_id: str
    chlorophyll_a_ug_l: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not CHLOROPHYLL_A_MIN_UG_L <= self.chlorophyll_a_ug_l <= CHLOROPHYLL_A_MAX_UG_L:
            raise ValueError(
                f"Chlorophyll-a must be between {CHLOROPHYLL_A_MIN_UG_L} and "
                f"{CHLOROPHYLL_A_MAX_UG_L} µg/L"
            )
