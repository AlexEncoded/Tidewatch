from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class LocationTelemetrySnapshot:
    """Domain representation of one buoy position telemetry sample."""

    buoy_id: str
    latitude: float
    longitude: float
    measured_at: datetime
    altitude_meters: float | None = None
    speed_mps: float | None = None
    hdop: float | None = None
    satellites: int | None = None
    device_id: str | None = None


@dataclass(frozen=True)
class SalinityTelemetrySnapshot:
    """Domain representation of one salinity sample."""

    buoy_id: str
    salinity_psu: float
    measured_at: datetime
    sensor_channel: str = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: str = "good"


@dataclass(frozen=True)
class ImuTelemetrySnapshot:
    """Domain representation of one inertial measurement sample."""

    buoy_id: str
    acceleration_x_mps2: float
    acceleration_y_mps2: float
    acceleration_z_mps2: float
    angular_velocity_x_dps: float
    angular_velocity_y_dps: float
    angular_velocity_z_dps: float
    measured_at: datetime
    sensor_channel: str = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: str = "good"


@dataclass(frozen=True)
class AmbientLightTelemetrySnapshot:
    """Domain representation of one ambient-light sample."""

    buoy_id: str
    illuminance_lux: float
    measured_at: datetime
    sensor_channel: str = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: str = "good"


@dataclass(frozen=True)
class WindTelemetrySnapshot:
    """Domain representation of one wind speed and direction sample."""

    buoy_id: str
    wind_speed_mps: float
    wind_direction_degrees: float
    measured_at: datetime
    sensor_channel: str = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: str = "good"


def latest_usable_reading(
    readings: list,
    max_age_seconds: float | None = None,
    now: datetime | None = None,
) -> list:
    """Return the newest valid reading within the optional age window."""
    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    for reading in readings:
        if reading.quality == "invalid":
            continue
        if max_age_seconds is not None:
            measured_at = reading.measured_at
            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=timezone.utc)
            if (reference_time - measured_at).total_seconds() > max_age_seconds:
                continue
        return [reading]
    return []
