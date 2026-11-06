"""Underwater-acoustic telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import (
    UNDERWATER_ACOUSTIC_MAX_ECHO_INTENSITY_DB,
    UNDERWATER_ACOUSTIC_MIN_ECHO_INTENSITY_DB,
    ReadingQuality,
    SensorChannel,
)


@dataclass(frozen=True)
class UnderwaterAcousticTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one underwater-acoustic sample."""

    buoy_id: str
    echo_intensity_db: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not UNDERWATER_ACOUSTIC_MIN_ECHO_INTENSITY_DB <= self.echo_intensity_db <= UNDERWATER_ACOUSTIC_MAX_ECHO_INTENSITY_DB:
            raise ValueError(
                "Underwater acoustic echo intensity must be between "
                f"{UNDERWATER_ACOUSTIC_MIN_ECHO_INTENSITY_DB} and "
                f"{UNDERWATER_ACOUSTIC_MAX_ECHO_INTENSITY_DB} dB"
            )
