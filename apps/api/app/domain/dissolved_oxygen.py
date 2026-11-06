"""Dissolved-oxygen telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import (
    DISSOLVED_OXYGEN_MAX_MG_L,
    DISSOLVED_OXYGEN_MIN_MG_L,
    ReadingQuality,
    SensorChannel,
)


@dataclass(frozen=True)
class DissolvedOxygenTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one dissolved-oxygen sample."""

    buoy_id: str
    dissolved_oxygen_mg_l: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not DISSOLVED_OXYGEN_MIN_MG_L <= self.dissolved_oxygen_mg_l <= DISSOLVED_OXYGEN_MAX_MG_L:
            raise ValueError(
                "Dissolved oxygen must be between "
                f"{DISSOLVED_OXYGEN_MIN_MG_L} and "
                f"{DISSOLVED_OXYGEN_MAX_MG_L} mg/L"
            )
