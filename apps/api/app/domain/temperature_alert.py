"""Domain snapshots for persisted temperature alerts."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TemperatureAlertSnapshot:
    """Persisted temperature alert data independent of the HTTP contract."""

    id: int
    buoy_id: str
    buoy_name: str
    severity: str
    temperature_celsius: float
    average_temperature: float
    created_at: datetime
    message: str
    status: str
    resolved_at: datetime | None = None
