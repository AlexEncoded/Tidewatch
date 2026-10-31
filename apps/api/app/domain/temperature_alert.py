"""Domain snapshots for persisted temperature alerts."""

from dataclasses import dataclass
from datetime import datetime

from .temperature import TemperatureAnalysisSnapshot


@dataclass(frozen=True)
class TemperatureAnomalySnapshot:
    """Computed temperature anomaly for API presentation."""

    buoy_id: str
    buoy_name: str
    severity: str
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
    severity: str
    temperature_celsius: float
    average_temperature: float
    created_at: datetime
    message: str
    status: str
    resolved_at: datetime | None = None


def build_temperature_anomaly(
    buoy_id: str,
    buoy_name: str,
    analysis: TemperatureAnalysisSnapshot,
    created_at: datetime,
) -> TemperatureAnomalySnapshot | None:
    """Build an alert snapshot only when analysis has a complete anomaly."""
    if (
        not analysis.is_anomaly
        or analysis.latest_temperature is None
        or analysis.average_temperature is None
    ):
        return None
    return TemperatureAnomalySnapshot(
        buoy_id=buoy_id,
        buoy_name=buoy_name,
        severity="warning",
        temperature_celsius=analysis.latest_temperature,
        average_temperature=analysis.average_temperature,
        created_at=created_at,
        message=analysis.anomaly_reason or "Temperature anomaly detected",
    )
