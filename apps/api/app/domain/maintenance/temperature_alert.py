"""Domain snapshots for persisted temperature alerts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

TemperatureAlertStatus = Literal["open", "resolved"]
TemperatureAlertSeverity = Literal["warning"]


@dataclass(frozen=True)
class TemperatureAnomalySnapshot:
    """Computed temperature anomaly for API presentation."""

    buoy_id: str
    buoy_name: str
    severity: TemperatureAlertSeverity
    temperature_celsius: float
    average_temperature: float
    created_at: datetime
    message: str


@dataclass(frozen=True)
class TemperatureAlertSnapshot:
    """Persisted temperature alert data independent of the HTTP contract."""

    id: int
    buoy_id: str
    buoy_name: str
    severity: TemperatureAlertSeverity
    temperature_celsius: float
    average_temperature: float
    created_at: datetime
    message: str
    status: TemperatureAlertStatus
    resolved_at: datetime | None = None


def build_temperature_anomaly(
    buoy_id: str,
    buoy_name: str,
    is_anomaly: bool,
    latest_temperature: float | None,
    average_temperature: float | None,
    anomaly_reason: str | None,
    created_at: datetime,
) -> TemperatureAnomalySnapshot | None:
    """Build an alert snapshot only when analysis has a complete anomaly."""
    if (
        not is_anomaly
        or latest_temperature is None
        or average_temperature is None
    ):
        return None
    return TemperatureAnomalySnapshot(
        buoy_id=buoy_id,
        buoy_name=buoy_name,
        severity="warning",
        temperature_celsius=latest_temperature,
        average_temperature=average_temperature,
        created_at=created_at,
        message=anomaly_reason or "Temperature anomaly detected",
    )
