"""Turbidity telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .reading_quality import ReadingQuality
from .devices import SensorChannel

TURBIDITY_MIN_NTU = 0
TURBIDITY_MAX_NTU = 5000


@dataclass(frozen=True)
class TurbidityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one turbidity sample."""

    buoy_id: str
    turbidity_ntu: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not TURBIDITY_MIN_NTU <= self.turbidity_ntu <= TURBIDITY_MAX_NTU:
            raise ValueError(
                f"Turbidity must be between {TURBIDITY_MIN_NTU} and "
                f"{TURBIDITY_MAX_NTU} NTU"
            )
