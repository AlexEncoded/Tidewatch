"""Domain snapshots for buoy identity."""

from dataclasses import dataclass
from datetime import datetime


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
class BuoyStatusCommand:
    """Requested operational status for a buoy."""

    status: str


@dataclass(frozen=True)
class BuoyLocationCommand:
    """Requested coordinates for a buoy's latest location."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class BuoyRegistrationCommand:
    """Validated input for registering a new buoy."""

    name: str
    latitude: float | None = None
    longitude: float | None = None
