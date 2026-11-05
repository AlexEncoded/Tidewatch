"""Conductivity telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .telemetry import SensorTelemetrySnapshot
from .telemetry_types import (
    CONDUCTIVITY_MAX_US_CM,
    CONDUCTIVITY_MIN_US_CM,
    ReadingQuality,
    SensorChannel,
)


@dataclass(frozen=True)
class ConductivityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one conductivity sample."""

    buoy_id: str
    conductivity_us_cm: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not CONDUCTIVITY_MIN_US_CM <= self.conductivity_us_cm <= CONDUCTIVITY_MAX_US_CM:
            raise ValueError(
                f"Conductivity must be between {CONDUCTIVITY_MIN_US_CM} and "
                f"{CONDUCTIVITY_MAX_US_CM} µS/cm"
            )
