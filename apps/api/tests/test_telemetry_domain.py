from datetime import datetime, timezone

import pytest

from app.domain.telemetry import (
    AirTemperatureTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    BatteryTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    ImuTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    PHTelemetrySnapshot,
    RainfallTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
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


@pytest.mark.parametrize("salinity_psu", [-0.01, 45.01])
def test_salinity_snapshot_rejects_values_outside_domain_range(
    salinity_psu: float,
) -> None:
    with pytest.raises(ValueError, match="Salinity"):
        SalinityTelemetrySnapshot(
            buoy_id="buoy-1",
            salinity_psu=salinity_psu,
            measured_at=datetime.now(timezone.utc),
        )


def test_salinity_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = SalinityTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = SalinityTelemetrySnapshot("buoy-1", 45, measured_at)

    assert lower.salinity_psu == 0
    assert upper.salinity_psu == 45


@pytest.mark.parametrize("humidity_percent", [-0.01, 100.01])
def test_humidity_snapshot_rejects_values_outside_domain_range(
    humidity_percent: float,
) -> None:
    with pytest.raises(ValueError, match="Humidity"):
        HumidityTelemetrySnapshot(
            buoy_id="buoy-1",
            humidity_percent=humidity_percent,
            measured_at=datetime.now(timezone.utc),
        )


def test_humidity_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = HumidityTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = HumidityTelemetrySnapshot("buoy-1", 100, measured_at)

    assert lower.humidity_percent == 0
    assert upper.humidity_percent == 100


@pytest.mark.parametrize("turbidity_ntu", [-0.01, 5000.01])
def test_turbidity_snapshot_rejects_values_outside_domain_range(
    turbidity_ntu: float,
) -> None:
    with pytest.raises(ValueError, match="Turbidity"):
        TurbidityTelemetrySnapshot(
            buoy_id="buoy-1",
            turbidity_ntu=turbidity_ntu,
            measured_at=datetime.now(timezone.utc),
        )


def test_turbidity_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = TurbidityTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = TurbidityTelemetrySnapshot("buoy-1", 5000, measured_at)

    assert lower.turbidity_ntu == 0
    assert upper.turbidity_ntu == 5000


@pytest.mark.parametrize("dissolved_oxygen_mg_l", [-0.01, 20.01])
def test_dissolved_oxygen_snapshot_rejects_values_outside_domain_range(
    dissolved_oxygen_mg_l: float,
) -> None:
    with pytest.raises(ValueError, match="Dissolved oxygen"):
        DissolvedOxygenTelemetrySnapshot(
            buoy_id="buoy-1",
            dissolved_oxygen_mg_l=dissolved_oxygen_mg_l,
            measured_at=datetime.now(timezone.utc),
        )


def test_dissolved_oxygen_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = DissolvedOxygenTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = DissolvedOxygenTelemetrySnapshot("buoy-1", 20, measured_at)

    assert lower.dissolved_oxygen_mg_l == 0
    assert upper.dissolved_oxygen_mg_l == 20


@pytest.mark.parametrize("ph", [-0.01, 14.01])
def test_ph_snapshot_rejects_values_outside_domain_range(ph: float) -> None:
    with pytest.raises(ValueError, match="pH"):
        PHTelemetrySnapshot(
            buoy_id="buoy-1",
            ph=ph,
            measured_at=datetime.now(timezone.utc),
        )


def test_ph_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = PHTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = PHTelemetrySnapshot("buoy-1", 14, measured_at)

    assert lower.ph == 0
    assert upper.ph == 14


@pytest.mark.parametrize("conductivity_us_cm", [-0.01, 200000.01])
def test_conductivity_snapshot_rejects_values_outside_domain_range(
    conductivity_us_cm: float,
) -> None:
    with pytest.raises(ValueError, match="Conductivity"):
        ConductivityTelemetrySnapshot(
            buoy_id="buoy-1",
            conductivity_us_cm=conductivity_us_cm,
            measured_at=datetime.now(timezone.utc),
        )


def test_conductivity_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = ConductivityTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = ConductivityTelemetrySnapshot("buoy-1", 200000, measured_at)

    assert lower.conductivity_us_cm == 0
    assert upper.conductivity_us_cm == 200000


@pytest.mark.parametrize("chlorophyll_a_ug_l", [-0.01, 1000.01])
def test_chlorophyll_a_snapshot_rejects_values_outside_domain_range(
    chlorophyll_a_ug_l: float,
) -> None:
    with pytest.raises(ValueError, match="Chlorophyll-a"):
        ChlorophyllATelemetrySnapshot(
            buoy_id="buoy-1",
            chlorophyll_a_ug_l=chlorophyll_a_ug_l,
            measured_at=datetime.now(timezone.utc),
        )


def test_chlorophyll_a_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = ChlorophyllATelemetrySnapshot("buoy-1", 0, measured_at)
    upper = ChlorophyllATelemetrySnapshot("buoy-1", 1000, measured_at)

    assert lower.chlorophyll_a_ug_l == 0
    assert upper.chlorophyll_a_ug_l == 1000


@pytest.mark.parametrize("rainfall_mm_h", [-0.01, 500.01])
def test_rainfall_snapshot_rejects_values_outside_domain_range(
    rainfall_mm_h: float,
) -> None:
    with pytest.raises(ValueError, match="Rainfall"):
        RainfallTelemetrySnapshot(
            buoy_id="buoy-1",
            rainfall_mm_h=rainfall_mm_h,
            measured_at=datetime.now(timezone.utc),
        )


def test_rainfall_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = RainfallTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = RainfallTelemetrySnapshot("buoy-1", 500, measured_at)

    assert lower.rainfall_mm_h == 0
    assert upper.rainfall_mm_h == 500


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


@pytest.mark.parametrize("pressure_kpa", [79.99, 120.01])
def test_atmospheric_pressure_snapshot_rejects_values_outside_domain_range(
    pressure_kpa: float,
) -> None:
    with pytest.raises(ValueError, match="Atmospheric pressure"):
        AtmosphericPressureTelemetrySnapshot(
            buoy_id="buoy-1",
            atmospheric_pressure_kpa=pressure_kpa,
            measured_at=datetime.now(timezone.utc),
        )


def test_atmospheric_pressure_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = AtmosphericPressureTelemetrySnapshot("buoy-1", 80, measured_at)
    upper = AtmosphericPressureTelemetrySnapshot("buoy-1", 120, measured_at)

    assert lower.atmospheric_pressure_kpa == 80
    assert upper.atmospheric_pressure_kpa == 120
