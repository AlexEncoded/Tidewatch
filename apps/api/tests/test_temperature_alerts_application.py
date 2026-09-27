from datetime import datetime, timezone
from app.application.temperature_alerts import find_temperature_anomalies
from app.domain.buoy import BuoyIdentitySnapshot
from app.domain.temperature import TemperatureTelemetrySnapshot


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


def test_temperature_anomalies_are_built_through_reader_port() -> None:
    alerts = find_temperature_anomalies(FakeTemperatureAlertsReader(), 2.0, 10)

    assert len(alerts) == 1
    assert alerts[0].buoy_id == "buoy-1"
    assert alerts[0].buoy_name == "North buoy"
    assert alerts[0].temperature_celsius == 30.0
