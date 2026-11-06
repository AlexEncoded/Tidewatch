"""Humidity telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import (
    HUMIDITY_MAX_PERCENT,
    HUMIDITY_MIN_PERCENT,
    ReadingQuality,
    SensorChannel,
)


@dataclass(frozen=True)
class HumidityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one humidity sample."""

    buoy_id: str
    humidity_percent: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not HUMIDITY_MIN_PERCENT <= self.humidity_percent <= HUMIDITY_MAX_PERCENT:
            raise ValueError(
                f"Humidity must be between {HUMIDITY_MIN_PERCENT} and "
                f"{HUMIDITY_MAX_PERCENT} percent"
            )
