"""Domain model for battery telemetry owned by a physical buoy device."""

from dataclasses import dataclass
from datetime import datetime

from .telemetry_types import (
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
    SensorChannel,
    VALID_SENSOR_CHANNELS,
    validate_battery_percentage,
)


@dataclass(frozen=True)
class BatteryTelemetrySnapshot:
    """Domain representation of one device-battery sample."""

    buoy_id: str
    battery_percent: float
    device_id: SensorChannel
    measured_at: datetime
    physical_device_id: str | None = None

    def __post_init__(self) -> None:
        if self.physical_device_id is not None and not (
            DEVICE_ID_MIN_LENGTH
            <= len(self.physical_device_id)
            <= DEVICE_ID_MAX_LENGTH
        ):
            raise ValueError(
                f"Device ID must contain between {DEVICE_ID_MIN_LENGTH} "
                f"and {DEVICE_ID_MAX_LENGTH} characters"
            )
        if self.device_id not in VALID_SENSOR_CHANNELS:
            raise ValueError(f"Unsupported battery device channel {self.device_id!r}")
        validate_battery_percentage(self.battery_percent)
