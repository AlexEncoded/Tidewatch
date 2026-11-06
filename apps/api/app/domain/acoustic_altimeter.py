"""Acoustic-altimeter telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import (
    ReadingQuality,
    SensorChannel,
)

ACOUSTIC_ALTIMETER_MIN_DEPTH_METERS = 0
ACOUSTIC_ALTIMETER_MAX_DEPTH_METERS = 20000


@dataclass(frozen=True)
class AcousticAltimeterTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one acoustic-altimeter sample."""

    buoy_id: str
    depth_meters: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not ACOUSTIC_ALTIMETER_MIN_DEPTH_METERS <= self.depth_meters <= ACOUSTIC_ALTIMETER_MAX_DEPTH_METERS:
            raise ValueError(
                "Acoustic-altimeter depth must be between "
                f"{ACOUSTIC_ALTIMETER_MIN_DEPTH_METERS} and "
                f"{ACOUSTIC_ALTIMETER_MAX_DEPTH_METERS} meters"
            )
