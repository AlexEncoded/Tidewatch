"""Domain snapshots for buoy identity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BuoyIdentitySnapshot:
    """Minimal buoy identity needed by fleet-level application queries."""

    buoy_id: str
    name: str
