"""Atmospheric-pressure telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import ReadingQuality, SensorChannel

ATMOSPHERIC_PRESSURE_MIN_KPA = 80
ATMOSPHERIC_PRESSURE_MAX_KPA = 120


@dataclass(frozen=True)
class AtmosphericPressureTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one atmospheric-pressure sample."""

    buoy_id: str
    atmospheric_pressure_kpa: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not ATMOSPHERIC_PRESSURE_MIN_KPA <= self.atmospheric_pressure_kpa <= ATMOSPHERIC_PRESSURE_MAX_KPA:
            raise ValueError(
                "Atmospheric pressure must be between "
                f"{ATMOSPHERIC_PRESSURE_MIN_KPA} and "
                f"{ATMOSPHERIC_PRESSURE_MAX_KPA} kPa"
            )
