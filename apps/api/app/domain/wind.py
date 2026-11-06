"""Wind telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import (
    DIRECTION_MAX_DEGREES,
    DIRECTION_MIN_DEGREES,
    ReadingQuality,
    SensorChannel,
    WIND_SPEED_MAX_MPS,
    WIND_SPEED_MIN_MPS,
)


@dataclass(frozen=True)
class WindTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one wind speed and direction sample."""

    buoy_id: str
    wind_speed_mps: float
    wind_direction_degrees: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not WIND_SPEED_MIN_MPS <= self.wind_speed_mps <= WIND_SPEED_MAX_MPS:
            raise ValueError(
                f"Wind speed must be between {WIND_SPEED_MIN_MPS} and "
                f"{WIND_SPEED_MAX_MPS} m/s"
            )
        if not DIRECTION_MIN_DEGREES <= self.wind_direction_degrees < DIRECTION_MAX_DEGREES:
            raise ValueError(
                "Wind direction must be greater than or equal to "
                f"{DIRECTION_MIN_DEGREES} and less than {DIRECTION_MAX_DEGREES} degrees"
            )
