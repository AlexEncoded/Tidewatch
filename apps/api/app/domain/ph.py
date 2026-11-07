"""pH telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import ReadingQuality, SensorChannel

PH_MIN = 0
PH_MAX = 14


@dataclass(frozen=True)
class PHTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one pH sample."""

    buoy_id: str
    ph: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not PH_MIN <= self.ph <= PH_MAX:
            raise ValueError(f"pH must be between {PH_MIN} and {PH_MAX}")
