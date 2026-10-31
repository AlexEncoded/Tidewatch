"""Application use cases and mappings for temperature alerts."""

from ..domain.temperature_alert import (
    TemperatureAlertSnapshot,
    TemperatureAnomalySnapshot,
    build_temperature_anomaly,
)
from .alert_ports import TemperatureAlertsReader, TemperatureAlertStore
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
        if readings:
            anomaly = build_temperature_anomaly(
                buoy.buoy_id,
                buoy.name,
                analysis,
                readings[0].measured_at,
            )
            if anomaly is not None:
                alerts.append(anomaly)
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
