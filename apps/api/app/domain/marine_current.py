"""Marine-current telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .directions import DIRECTION_MAX_DEGREES, DIRECTION_MIN_DEGREES
from .telemetry_types import (
    ReadingQuality,
    SensorChannel,
)

MARINE_CURRENT_SPEED_MIN_MPS = 0
MARINE_CURRENT_SPEED_MAX_MPS = 20


@dataclass(frozen=True)
class MarineCurrentTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one marine-current sample."""

    buoy_id: str
    current_speed_mps: float
    current_direction_degrees: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not MARINE_CURRENT_SPEED_MIN_MPS <= self.current_speed_mps <= MARINE_CURRENT_SPEED_MAX_MPS:
            raise ValueError(
                "Marine-current speed must be between "
                f"{MARINE_CURRENT_SPEED_MIN_MPS} and "
                f"{MARINE_CURRENT_SPEED_MAX_MPS} m/s"
            )
        if not DIRECTION_MIN_DEGREES <= self.current_direction_degrees < DIRECTION_MAX_DEGREES:
            raise ValueError(
                "Marine-current direction must be greater than or equal to "
                f"{DIRECTION_MIN_DEGREES} and less than {DIRECTION_MAX_DEGREES} degrees"
            )
