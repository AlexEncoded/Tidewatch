"""Application use cases and mappings for temperature alerts."""

from ..domain.temperature_alert import (
    TemperatureAlertSnapshot,
    TemperatureAnomalySnapshot,
)
from .ports import TemperatureAlertsReader
from .temperature_analysis import analyze_temperature_readings, list_valid_temperature_readings


def find_temperature_anomalies(
    reader: TemperatureAlertsReader,
    threshold: float,
    window: int,
) -> list[TemperatureAnomalySnapshot]:
    """Find anomalous recent temperatures across all buoy identities."""
    alerts = []
    for buoy in reader.list_buoy_identities():
        readings = list_valid_temperature_readings(reader, buoy.buoy_id, window)
        analysis = analyze_temperature_readings(buoy.buoy_id, readings, threshold)
        if analysis.is_anomaly and analysis.latest_temperature is not None:
            alerts.append(
                TemperatureAnomalySnapshot(
                    buoy_id=buoy.buoy_id,
                    buoy_name=buoy.name,
                    severity="warning",
                    temperature_celsius=analysis.latest_temperature,
                    average_temperature=analysis.average_temperature or 0,
                    created_at=readings[0].measured_at,
                    message=analysis.anomaly_reason or "Temperature anomaly detected",
                )
            )
    return alerts


def to_stored_temperature_alert(alert) -> TemperatureAlertSnapshot:
    """Map a persisted alert entity to an application snapshot."""
    return TemperatureAlertSnapshot(
        id=alert.id,
        buoy_id=alert.buoy_id,
        buoy_name=alert.buoy.name,
        severity=alert.severity,
        temperature_celsius=alert.temperature_celsius,
        average_temperature=alert.average_temperature,
        created_at=alert.created_at,
        message=alert.message,
        status=alert.status,
        resolved_at=alert.resolved_at,
    )
