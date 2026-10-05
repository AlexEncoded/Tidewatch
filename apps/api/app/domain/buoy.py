"""Domain snapshots for buoy identity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, get_args

BuoyOperationalStatus = Literal["active", "maintenance", "inactive"]
BUOY_STATUSES = frozenset(get_args(BuoyOperationalStatus))
BUOY_NAME_MIN_LENGTH = 1
BUOY_NAME_MAX_LENGTH = 100
LATITUDE_MIN = -90
LATITUDE_MAX = 90
LONGITUDE_MIN = -180
LONGITUDE_MAX = 180


@dataclass(frozen=True)
class BuoyIdentitySnapshot:
    """Minimal buoy identity needed by fleet-level application queries."""

    buoy_id: str
    name: str


@dataclass(frozen=True)
class BuoyActivitySnapshot:
    """Operational fields used to evaluate whether a buoy has gone stale."""

    buoy_id: str
    name: str
    status: BuoyOperationalStatus
    last_seen_at: datetime | None


@dataclass(frozen=True)
class StaleBuoySnapshot:
    """A buoy whose latest activity exceeds its permitted age."""

    buoy_id: str
    name: str
    status: str
    last_seen_at: datetime
    age_seconds: float


@dataclass(frozen=True)
class BuoySnapshot:
    """Domain representation of buoy identity and current operational state."""

    buoy_id: str
    name: str
    latitude: float | None
    longitude: float | None
    status: str
    last_seen_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class BuoySummarySnapshot:
    """Fleet overview with latest telemetry grouped by family and channel."""

    buoy: BuoySnapshot
    latest_readings: dict[str, dict[str, object | None]]


@dataclass(frozen=True)
class BuoyStatusCommand:
    """Requested operational status for a buoy."""

    status: str

    def __post_init__(self) -> None:
        if self.status not in BUOY_STATUSES:
            allowed = ", ".join(sorted(BUOY_STATUSES))
            raise ValueError(f"Unsupported buoy status {self.status!r}; expected one of: {allowed}")


@dataclass(frozen=True)
class BuoyLocationCommand:
    """Requested coordinates for a buoy's latest location."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not LATITUDE_MIN <= self.latitude <= LATITUDE_MAX:
            raise ValueError(f"Latitude must be between {LATITUDE_MIN} and {LATITUDE_MAX} degrees")
        if not LONGITUDE_MIN <= self.longitude <= LONGITUDE_MAX:
            raise ValueError(
                f"Longitude must be between {LONGITUDE_MIN} and {LONGITUDE_MAX} degrees"
            )


@dataclass(frozen=True)
class BuoyRegistrationCommand:
    """Validated input for registering a new buoy."""

    name: str
    latitude: float | None = None
    longitude: float | None = None

    def __post_init__(self) -> None:
        if not BUOY_NAME_MIN_LENGTH <= len(self.name) <= BUOY_NAME_MAX_LENGTH:
            raise ValueError(
                f"Buoy name must contain between {BUOY_NAME_MIN_LENGTH} "
                f"and {BUOY_NAME_MAX_LENGTH} characters"
            )
        if self.latitude is not None and not LATITUDE_MIN <= self.latitude <= LATITUDE_MAX:
            raise ValueError(f"Latitude must be between {LATITUDE_MIN} and {LATITUDE_MAX} degrees")
        if self.longitude is not None and not LONGITUDE_MIN <= self.longitude <= LONGITUDE_MAX:
            raise ValueError(
                f"Longitude must be between {LONGITUDE_MIN} and {LONGITUDE_MAX} degrees"
            )
