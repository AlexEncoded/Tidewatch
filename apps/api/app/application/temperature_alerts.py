"""Application use cases and mappings for temperature alerts."""

from ..domain.temperature_alert import (
    TemperatureAlertSnapshot,
    TemperatureAnomalySnapshot,
)
from .ports import TemperatureAlertsReader
from .ports import TemperatureAlertStore
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


def evaluate_and_store_temperature_alerts(
    store: TemperatureAlertStore,
    threshold: float,
    window: int,
) -> list[TemperatureAlertSnapshot]:
    """Persist new anomalies once and return the matching stored snapshots."""
    stored = []
    for anomaly in find_temperature_anomalies(store, threshold, window):
        existing = store.find_alert(anomaly.buoy_id, anomaly.created_at)
        stored.append(
            existing
            if existing is not None
            else store.create_alert(anomaly, anomaly.created_at)
        )
    return stored


def list_stored_temperature_alerts(
    store: TemperatureAlertStore,
    status: str = "open",
) -> list[TemperatureAlertSnapshot]:
    """List persisted temperature-alert snapshots through the output port."""
    return store.list_alerts(status)


def resolve_stored_temperature_alert(
    store: TemperatureAlertStore,
    alert_id: int,
) -> TemperatureAlertSnapshot | None:
    """Resolve a persisted alert through the output port."""
    return store.resolve_alert(alert_id)
