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
