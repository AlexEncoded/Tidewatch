"""Domain model for inertial measurement unit telemetry."""

from dataclasses import dataclass
from datetime import datetime

from .telemetry import SensorTelemetrySnapshot
from .telemetry_types import (
    IMU_ACCELERATION_MAX_MPS2,
    IMU_ACCELERATION_MIN_MPS2,
    IMU_ANGULAR_VELOCITY_MAX_DPS,
    IMU_ANGULAR_VELOCITY_MIN_DPS,
    ReadingQuality,
    SensorChannel,
)


@dataclass(frozen=True)
class ImuTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one inertial measurement sample."""

    buoy_id: str
    acceleration_x_mps2: float
    acceleration_y_mps2: float
    acceleration_z_mps2: float
    angular_velocity_x_dps: float
    angular_velocity_y_dps: float
    angular_velocity_z_dps: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        acceleration = (
            self.acceleration_x_mps2,
            self.acceleration_y_mps2,
            self.acceleration_z_mps2,
        )
        if any(
            not IMU_ACCELERATION_MIN_MPS2 <= value <= IMU_ACCELERATION_MAX_MPS2
            for value in acceleration
        ):
            raise ValueError(
                "IMU acceleration components must be between "
                f"{IMU_ACCELERATION_MIN_MPS2} and {IMU_ACCELERATION_MAX_MPS2} m/s²"
            )

        angular_velocity = (
            self.angular_velocity_x_dps,
            self.angular_velocity_y_dps,
            self.angular_velocity_z_dps,
        )
        if any(
            not IMU_ANGULAR_VELOCITY_MIN_DPS
            <= value
            <= IMU_ANGULAR_VELOCITY_MAX_DPS
            for value in angular_velocity
        ):
            raise ValueError(
                "IMU angular-velocity components must be between "
                f"{IMU_ANGULAR_VELOCITY_MIN_DPS} and "
                f"{IMU_ANGULAR_VELOCITY_MAX_DPS} degrees per second"
            )
