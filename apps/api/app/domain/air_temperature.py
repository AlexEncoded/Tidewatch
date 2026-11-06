"""Air-temperature telemetry domain model and physical bounds."""

from dataclasses import dataclass
from datetime import datetime

from .sensor_telemetry import SensorTelemetrySnapshot
from .telemetry_types import ReadingQuality, SensorChannel

AIR_TEMPERATURE_MIN_CELSIUS = -60
AIR_TEMPERATURE_MAX_CELSIUS = 60


@dataclass(frozen=True)
class AirTemperatureTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one air-temperature sample."""

    buoy_id: str
    air_temperature_celsius: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not AIR_TEMPERATURE_MIN_CELSIUS <= self.air_temperature_celsius <= AIR_TEMPERATURE_MAX_CELSIUS:
            raise ValueError(
                "Air temperature must be between "
                f"{AIR_TEMPERATURE_MIN_CELSIUS} and {AIR_TEMPERATURE_MAX_CELSIUS} °C"
            )
