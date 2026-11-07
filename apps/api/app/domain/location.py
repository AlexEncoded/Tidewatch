"""Domain model for buoy position and GNSS telemetry."""

from dataclasses import dataclass
from datetime import datetime

from .buoy import LATITUDE_MAX, LATITUDE_MIN, LONGITUDE_MAX, LONGITUDE_MIN
from .telemetry_types import (
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
)

GNSS_ALTITUDE_MIN_METERS = -1000
GNSS_ALTITUDE_MAX_METERS = 20000
GNSS_SPEED_MIN_MPS = 0
GNSS_SPEED_MAX_MPS = 100
GNSS_HDOP_MIN = 0
GNSS_HDOP_MAX = 100
GNSS_SATELLITES_MIN = 0
GNSS_SATELLITES_MAX = 100


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

    def __post_init__(self) -> None:
        if self.device_id is not None and not (
            DEVICE_ID_MIN_LENGTH <= len(self.device_id) <= DEVICE_ID_MAX_LENGTH
        ):
            raise ValueError(
                f"Device ID must contain between {DEVICE_ID_MIN_LENGTH} "
                f"and {DEVICE_ID_MAX_LENGTH} characters"
            )
        if not LATITUDE_MIN <= self.latitude <= LATITUDE_MAX:
            raise ValueError(
                f"Latitude must be between {LATITUDE_MIN} and {LATITUDE_MAX} degrees"
            )
        if not LONGITUDE_MIN <= self.longitude <= LONGITUDE_MAX:
            raise ValueError(
                f"Longitude must be between {LONGITUDE_MIN} and {LONGITUDE_MAX} degrees"
            )
        if self.altitude_meters is not None and not (
            GNSS_ALTITUDE_MIN_METERS
            <= self.altitude_meters
            <= GNSS_ALTITUDE_MAX_METERS
        ):
            raise ValueError(
                f"GNSS altitude must be between {GNSS_ALTITUDE_MIN_METERS} and "
                f"{GNSS_ALTITUDE_MAX_METERS} meters"
            )
        if self.speed_mps is not None and not (
            GNSS_SPEED_MIN_MPS <= self.speed_mps <= GNSS_SPEED_MAX_MPS
        ):
            raise ValueError(
                f"GNSS speed must be between {GNSS_SPEED_MIN_MPS} and "
                f"{GNSS_SPEED_MAX_MPS} m/s"
            )
        if self.hdop is not None and not GNSS_HDOP_MIN < self.hdop <= GNSS_HDOP_MAX:
            raise ValueError(
                f"GNSS HDOP must be greater than {GNSS_HDOP_MIN} and at most {GNSS_HDOP_MAX}"
            )
        if self.satellites is not None and not (
            GNSS_SATELLITES_MIN <= self.satellites <= GNSS_SATELLITES_MAX
        ):
            raise ValueError(
                f"GNSS satellite count must be between {GNSS_SATELLITES_MIN} and "
                f"{GNSS_SATELLITES_MAX}"
            )
