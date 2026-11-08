"""Salinity telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .reading_quality import ReadingQuality
from .devices import SensorChannel

SALINITY_MIN_PSU = 0
SALINITY_MAX_PSU = 45


@dataclass(frozen=True)
class SalinityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one salinity sample."""

    buoy_id: str
    salinity_psu: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not SALINITY_MIN_PSU <= self.salinity_psu <= SALINITY_MAX_PSU:
            raise ValueError(
                f"Salinity must be between {SALINITY_MIN_PSU} and "
                f"{SALINITY_MAX_PSU} PSU"
            )
