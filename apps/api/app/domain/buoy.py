"""Domain snapshots for buoy identity."""

from dataclasses import dataclass
from datetime import datetime

BUOY_STATUSES = frozenset({"active", "maintenance", "inactive"})


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
    status: str
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
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")


@dataclass(frozen=True)
class BuoyRegistrationCommand:
    """Validated input for registering a new buoy."""

    name: str
    latitude: float | None = None
    longitude: float | None = None

    def __post_init__(self) -> None:
        if not 1 <= len(self.name) <= 100:
            raise ValueError("Buoy name must contain between 1 and 100 characters")
        if self.latitude is not None and not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if self.longitude is not None and not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
