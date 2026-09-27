from datetime import datetime, timezone
from app.application.temperature_alerts import (
    evaluate_and_store_temperature_alerts,
    find_temperature_anomalies,
)
from app.domain.buoy import BuoyIdentitySnapshot
from app.domain.temperature import TemperatureTelemetrySnapshot
from app.domain.temperature_alert import TemperatureAlertSnapshot


class FakeTemperatureAlertsReader:
    def list_buoy_identities(self):
        return [BuoyIdentitySnapshot(buoy_id="buoy-1", name="North buoy")]

    def list_temperatures(self, buoy_id, limit, sensor_channel="A"):
        return [
            TemperatureTelemetrySnapshot(
                buoy_id=buoy_id,
                temperature_celsius=value,
                measured_at=datetime(2026, 9, 27, minute=index, tzinfo=timezone.utc),
            )
            for index, value in enumerate((30.0, 18.1, 18.2, 18.0))
        ]


class FakeTemperatureAlertStore(FakeTemperatureAlertsReader):
    def __init__(self):
        self.stored = {}
        self.create_calls = 0

    def find_alert(self, buoy_id, measured_at):
        return self.stored.get((buoy_id, measured_at))

    def create_alert(self, alert, reading_measured_at):
        self.create_calls += 1
        snapshot = TemperatureAlertSnapshot(
            id=self.create_calls,
            buoy_id=alert.buoy_id,
            buoy_name=alert.buoy_name,
            severity=alert.severity,
            temperature_celsius=alert.temperature_celsius,
            average_temperature=alert.average_temperature,
            created_at=alert.created_at,
            message=alert.message,
            status="open",
        )
        self.stored[(alert.buoy_id, reading_measured_at)] = snapshot
        return snapshot


def test_temperature_anomalies_are_built_through_reader_port() -> None:
    alerts = find_temperature_anomalies(FakeTemperatureAlertsReader(), 2.0, 10)

    assert len(alerts) == 1
    assert alerts[0].buoy_id == "buoy-1"
    assert alerts[0].buoy_name == "North buoy"
    assert alerts[0].temperature_celsius == 30.0


def test_temperature_alert_evaluation_is_idempotent_through_store_port() -> None:
    store = FakeTemperatureAlertStore()

    first = evaluate_and_store_temperature_alerts(store, 2.0, 10)
    second = evaluate_and_store_temperature_alerts(store, 2.0, 10)

    assert len(first) == len(second) == 1
    assert first[0].id == second[0].id
    assert store.create_calls == 1
