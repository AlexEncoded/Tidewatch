from datetime import datetime, timezone

from app.application.telemetry_batch import (
    TELEMETRY_READING_FAMILIES,
    TelemetryBatchCommand,
)
from app.schemas.ingestion import TelemetryBatchCreate


def test_batch_command_covers_every_validated_sensor_family() -> None:
    schema_families = set(TelemetryBatchCreate.model_fields) - {
        "device_id",
        "location",
        "device_runtime",
    }

    assert set(TELEMETRY_READING_FAMILIES) == schema_families
    command = TelemetryBatchCommand.from_mapping({})
    assert set(command.readings) == schema_families
    assert all(command.readings[family] == () for family in schema_families)


def test_device_runtime_telemetry_requires_device_identity() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="requires a physical device_id"):
        TelemetryBatchCreate.model_validate(
            {
                "temperatures": [{"temperature_celsius": 18, "sensor_channel": "A"}],
                "device_runtime": {
                    "cpu_usage_percent": 30,
                    "memory_usage_percent": 50,
                },
            }
        )


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
        "device_runtime": {
            "cpu_usage_percent": 35.0,
            "memory_usage_percent": 62.0,
            "measured_at": measured_at,
        },
    }

    command = TelemetryBatchCommand.from_mapping(source)
    source["temperatures"][0]["temperature_celsius"] = -1

    assert command.readings["temperatures"][0]["temperature_celsius"] == 18.5
    assert (
        command.as_json_mapping()["temperatures"][0]["measured_at"]
        == measured_at.isoformat()
    )
    assert command.as_json_mapping()["device_id"] == "buoy-device"
    assert command.as_json_mapping()["device_runtime"]["measured_at"] == measured_at.isoformat()
