"""Domain model for ambient-light sensor telemetry."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .reading_quality import ReadingQuality
from .devices import SensorChannel

AMBIENT_LIGHT_MIN_LUX = 0
AMBIENT_LIGHT_MAX_LUX = 150000


@dataclass(frozen=True)
class AmbientLightTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one ambient-light sample."""

    buoy_id: str
    illuminance_lux: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not AMBIENT_LIGHT_MIN_LUX <= self.illuminance_lux <= AMBIENT_LIGHT_MAX_LUX:
            raise ValueError(
                f"Ambient light must be between {AMBIENT_LIGHT_MIN_LUX} and "
                f"{AMBIENT_LIGHT_MAX_LUX} lux"
            )
