from datetime import datetime, timezone

from app.application.telemetry_batch import TelemetryBatchCommand


def test_batch_command_copies_readings_and_serializes_datetime_for_queue() -> None:
    measured_at = datetime(2026, 10, 19, 12, 30, tzinfo=timezone.utc)
    source = {
        "device_id": "buoy-device",
        "temperatures": [
            {
                "temperature_celsius": 18.5,
                "sensor_channel": "A",
                "measured_at": measured_at,
            }
        ],
        "location": {"latitude": 36.8, "longitude": 2.6},
    }

    command = TelemetryBatchCommand.from_mapping(source)
    source["temperatures"][0]["temperature_celsius"] = -1

    assert command.readings["temperatures"][0]["temperature_celsius"] == 18.5
    assert (
        command.as_json_mapping()["temperatures"][0]["measured_at"]
        == measured_at.isoformat()
    )
    assert command.as_json_mapping()["device_id"] == "buoy-device"
