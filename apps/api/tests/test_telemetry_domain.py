from datetime import datetime, timezone

import pytest

from app.domain.telemetry import (
    BatteryTelemetrySnapshot,
    ImuTelemetrySnapshot,
    SalinityTelemetrySnapshot,
)


@pytest.mark.parametrize(
    "sensor_channel",
    ["C", "a", ""],
)
def test_sensor_snapshot_rejects_unknown_channel(sensor_channel: str) -> None:
    with pytest.raises(ValueError, match="Unsupported sensor channel"):
        SalinityTelemetrySnapshot(
            buoy_id="buoy-1",
            salinity_psu=35,
            measured_at=datetime.now(timezone.utc),
            sensor_channel=sensor_channel,
        )


def test_sensor_snapshot_rejects_unknown_quality() -> None:
    with pytest.raises(ValueError, match="Unsupported reading quality"):
        ImuTelemetrySnapshot(
            buoy_id="buoy-1",
            acceleration_x_mps2=0,
            acceleration_y_mps2=0,
            acceleration_z_mps2=9.8,
            angular_velocity_x_dps=0,
            angular_velocity_y_dps=0,
            angular_velocity_z_dps=0,
            measured_at=datetime.now(timezone.utc),
            quality="unknown",
        )


def test_sensor_snapshot_accepts_supported_metadata() -> None:
    snapshot = SalinityTelemetrySnapshot(
        buoy_id="buoy-1",
        salinity_psu=35,
        measured_at=datetime.now(timezone.utc),
        sensor_channel="B",
        quality="suspect",
    )

    assert snapshot.sensor_channel == "B"
    assert snapshot.quality == "suspect"


@pytest.mark.parametrize("battery_percent", [-0.1, 100.1])
def test_battery_snapshot_rejects_percentage_outside_domain_range(
    battery_percent: float,
) -> None:
    with pytest.raises(ValueError, match="Battery percentage"):
        BatteryTelemetrySnapshot(
            buoy_id="buoy-1",
            battery_percent=battery_percent,
            device_id="A",
            measured_at=datetime.now(timezone.utc),
        )


def test_battery_snapshot_rejects_unknown_device_channel() -> None:
    with pytest.raises(ValueError, match="Unsupported battery device channel"):
        BatteryTelemetrySnapshot(
            buoy_id="buoy-1",
            battery_percent=50,
            device_id="C",
            measured_at=datetime.now(timezone.utc),
        )
