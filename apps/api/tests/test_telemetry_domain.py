from datetime import datetime, timezone

import pytest

from app.domain.telemetry import (
    AirTemperatureTelemetrySnapshot,
    BatteryTelemetrySnapshot,
    ImuTelemetrySnapshot,
    SalinityTelemetrySnapshot,
)
from app.domain.pressure import PressureTelemetrySnapshot
from app.domain.temperature import TemperatureTelemetrySnapshot


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


@pytest.mark.parametrize("temperature_celsius", [-5.01, 45.01])
def test_sea_temperature_snapshot_rejects_values_outside_physical_range(
    temperature_celsius: float,
) -> None:
    with pytest.raises(ValueError, match="Sea temperature"):
        TemperatureTelemetrySnapshot(
            buoy_id="buoy-1",
            temperature_celsius=temperature_celsius,
            measured_at=datetime.now(timezone.utc),
        )


def test_sea_temperature_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = TemperatureTelemetrySnapshot("buoy-1", -5, measured_at)
    upper = TemperatureTelemetrySnapshot("buoy-1", 45, measured_at)

    assert lower.temperature_celsius == -5
    assert upper.temperature_celsius == 45


@pytest.mark.parametrize("air_temperature_celsius", [-60.01, 60.01])
def test_air_temperature_snapshot_rejects_values_outside_domain_range(
    air_temperature_celsius: float,
) -> None:
    with pytest.raises(ValueError, match="Air temperature"):
        AirTemperatureTelemetrySnapshot(
            buoy_id="buoy-1",
            air_temperature_celsius=air_temperature_celsius,
            measured_at=datetime.now(timezone.utc),
        )


def test_air_temperature_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = AirTemperatureTelemetrySnapshot("buoy-1", -60, measured_at)
    upper = AirTemperatureTelemetrySnapshot("buoy-1", 60, measured_at)

    assert lower.air_temperature_celsius == -60
    assert upper.air_temperature_celsius == 60


@pytest.mark.parametrize("pressure_kpa", [79.99, 130.01])
def test_water_pressure_snapshot_rejects_values_outside_domain_range(
    pressure_kpa: float,
) -> None:
    with pytest.raises(ValueError, match="Water pressure"):
        PressureTelemetrySnapshot(
            buoy_id="buoy-1",
            pressure_kpa=pressure_kpa,
            measured_at=datetime.now(timezone.utc),
        )


def test_water_pressure_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = PressureTelemetrySnapshot("buoy-1", 80, measured_at)
    upper = PressureTelemetrySnapshot("buoy-1", 130, measured_at)

    assert lower.pressure_kpa == 80
    assert upper.pressure_kpa == 130
