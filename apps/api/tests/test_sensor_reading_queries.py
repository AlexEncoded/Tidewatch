from datetime import datetime, timezone

from app.application.sensor_reading_queries import list_sensor_readings
from app.domain.temperature import TemperatureTelemetrySnapshot


def test_sensor_reading_query_checks_buoy_and_forwards_filters() -> None:
    reading = TemperatureTelemetrySnapshot(
        "buoy-1", 18.0, datetime(2026, 11, 14, tzinfo=timezone.utc)
    )

    class Reader:
        def buoy_exists(self, buoy_id):
            assert buoy_id == "buoy-1"
            return True

    calls = []

    def list_readings(buoy_id, limit, sensor_channel):
        calls.append((buoy_id, limit, sensor_channel))
        return [reading]

    result = list_sensor_readings(Reader(), list_readings, "buoy-1", 25, "B")

    assert result == [reading]
    assert calls == [("buoy-1", 25, "B")]


def test_sensor_reading_query_skips_port_read_for_unknown_buoy() -> None:
    class Reader:
        def buoy_exists(self, buoy_id):
            return False

    def list_readings(*args):
        raise AssertionError("unknown buoy must not load readings")

    assert list_sensor_readings(Reader(), list_readings, "missing", 25, "A") is None
