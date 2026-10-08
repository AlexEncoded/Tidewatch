from datetime import datetime, timezone

import pytest

from app.domain.telemetry import (
    AirTemperatureTelemetrySnapshot,
    AmbientLightTelemetrySnapshot,
    AcousticAltimeterTelemetrySnapshot,
    AtmosphericPressureTelemetrySnapshot,
    BatteryTelemetrySnapshot,
    ChlorophyllATelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    ImuTelemetrySnapshot,
    HumidityTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    PHTelemetrySnapshot,
    RainfallTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    LocationTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    UnderwaterAcousticTelemetrySnapshot,
    WindTelemetrySnapshot,
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


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("device_id", "", "Device ID"),
        ("device_id", "d" * 101, "Device ID"),
        ("sensor_id", "s" * 101, "Sensor ID"),
        ("firmware_version", "v" * 51, "Firmware version"),
    ],
)
def test_sensor_snapshot_rejects_provenance_outside_contract_limits(
    field: str,
    value: str,
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        SalinityTelemetrySnapshot(
            buoy_id="buoy-1",
            salinity_psu=35,
            measured_at=datetime.now(timezone.utc),
            **{field: value},
        )


def test_sensor_snapshot_accepts_provenance_at_contract_limits() -> None:
    snapshot = SalinityTelemetrySnapshot(
        buoy_id="buoy-1",
        salinity_psu=35,
        measured_at=datetime.now(timezone.utc),
        device_id="d" * 100,
        sensor_id="s" * 100,
        firmware_version="v" * 50,
    )

    assert len(snapshot.device_id or "") == 100
    assert len(snapshot.sensor_id or "") == 100
    assert len(snapshot.firmware_version or "") == 50


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


@pytest.mark.parametrize("illuminance_lux", [-0.01, 150000.01])
def test_ambient_light_snapshot_rejects_values_outside_domain_range(
    illuminance_lux: float,
) -> None:
    with pytest.raises(ValueError, match="Ambient light"):
        AmbientLightTelemetrySnapshot(
            buoy_id="buoy-1",
            illuminance_lux=illuminance_lux,
            measured_at=datetime.now(timezone.utc),
        )


def test_ambient_light_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    lower = AmbientLightTelemetrySnapshot("buoy-1", 0, measured_at)
    upper = AmbientLightTelemetrySnapshot("buoy-1", 150000, measured_at)

    assert lower.illuminance_lux == 0
    assert upper.illuminance_lux == 150000


@pytest.mark.parametrize("wind_speed_mps", [-0.01, 100.01])
def test_wind_snapshot_rejects_speed_outside_domain_range(
    wind_speed_mps: float,
) -> None:
    with pytest.raises(ValueError, match="Wind speed"):
        WindTelemetrySnapshot(
            buoy_id="buoy-1",
            wind_speed_mps=wind_speed_mps,
            wind_direction_degrees=0,
            measured_at=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize("wind_direction_degrees", [-0.01, 360])
def test_wind_snapshot_rejects_direction_outside_domain_range(
    wind_direction_degrees: float,
) -> None:
    with pytest.raises(ValueError, match="Wind direction"):
        WindTelemetrySnapshot(
            buoy_id="buoy-1",
            wind_speed_mps=0,
            wind_direction_degrees=wind_direction_degrees,
            measured_at=datetime.now(timezone.utc),
        )


def test_wind_snapshot_accepts_speed_and_direction_boundaries() -> None:
    measured_at = datetime.now(timezone.utc)
    calm = WindTelemetrySnapshot("buoy-1", 0, 0, measured_at)
    upper_speed = WindTelemetrySnapshot("buoy-1", 100, 359.999, measured_at)

    assert calm.wind_speed_mps == 0
    assert calm.wind_direction_degrees == 0
    assert upper_speed.wind_speed_mps == 100
    assert upper_speed.wind_direction_degrees == 359.999


@pytest.mark.parametrize("current_speed_mps", [-0.01, 20.01])
def test_marine_current_snapshot_rejects_speed_outside_domain_range(
    current_speed_mps: float,
) -> None:
    with pytest.raises(ValueError, match="Marine-current speed"):
        MarineCurrentTelemetrySnapshot(
            buoy_id="buoy-1",
            current_speed_mps=current_speed_mps,
            current_direction_degrees=0,
            measured_at=datetime.now(timezone.utc),
        )


@pytest.mark.parametrize("current_direction_degrees", [-0.01, 360])
def test_marine_current_snapshot_rejects_direction_outside_domain_range(
    current_direction_degrees: float,
) -> None:
    with pytest.raises(ValueError, match="Marine-current direction"):
        MarineCurrentTelemetrySnapshot(
            buoy_id="buoy-1",
            current_speed_mps=0,
            current_direction_degrees=current_direction_degrees,
            measured_at=datetime.now(timezone.utc),
        )


def test_marine_current_snapshot_accepts_speed_and_direction_boundaries() -> None:
    measured_at = datetime.now(timezone.utc)
    calm = MarineCurrentTelemetrySnapshot("buoy-1", 0, 0, measured_at)
    upper_speed = MarineCurrentTelemetrySnapshot("buoy-1", 20, 359.999, measured_at)

    assert calm.current_speed_mps == 0
    assert calm.current_direction_degrees == 0
    assert upper_speed.current_speed_mps == 20
    assert upper_speed.current_direction_degrees == 359.999


@pytest.mark.parametrize("depth_meters", [-0.01, 20000.01])
def test_acoustic_altimeter_snapshot_rejects_depth_outside_domain_range(
    depth_meters: float,
) -> None:
    with pytest.raises(ValueError, match="Acoustic-altimeter depth"):
        AcousticAltimeterTelemetrySnapshot(
            buoy_id="buoy-1",
            depth_meters=depth_meters,
            measured_at=datetime.now(timezone.utc),
        )


def test_acoustic_altimeter_snapshot_accepts_depth_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    surface = AcousticAltimeterTelemetrySnapshot("buoy-1", 0, measured_at)
    maximum = AcousticAltimeterTelemetrySnapshot("buoy-1", 20000, measured_at)

    assert surface.depth_meters == 0
    assert maximum.depth_meters == 20000


@pytest.mark.parametrize("echo_intensity_db", [-200.01, 100.01])
def test_underwater_acoustic_snapshot_rejects_values_outside_domain_range(
    echo_intensity_db: float,
) -> None:
    with pytest.raises(ValueError, match="Underwater acoustic echo intensity"):
        UnderwaterAcousticTelemetrySnapshot(
            buoy_id="buoy-1",
            echo_intensity_db=echo_intensity_db,
            measured_at=datetime.now(timezone.utc),
        )


def test_underwater_acoustic_snapshot_accepts_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    minimum = UnderwaterAcousticTelemetrySnapshot("buoy-1", -200, measured_at)
    maximum = UnderwaterAcousticTelemetrySnapshot("buoy-1", 100, measured_at)

    assert minimum.echo_intensity_db == -200
    assert maximum.echo_intensity_db == 100


@pytest.mark.parametrize("field,value", [
    ("acceleration_x_mps2", -200.01),
    ("acceleration_y_mps2", 200.01),
    ("angular_velocity_z_dps", -2000.01),
    ("angular_velocity_x_dps", 2000.01),
])
def test_imu_snapshot_rejects_components_outside_domain_range(
    field: str,
    value: float,
) -> None:
    components = {
        "acceleration_x_mps2": 0,
        "acceleration_y_mps2": 0,
        "acceleration_z_mps2": 0,
        "angular_velocity_x_dps": 0,
        "angular_velocity_y_dps": 0,
        "angular_velocity_z_dps": 0,
    }
    components[field] = value

    with pytest.raises(ValueError, match="IMU"):
        ImuTelemetrySnapshot(
            buoy_id="buoy-1",
            measured_at=datetime.now(timezone.utc),
            **components,
        )


def test_imu_snapshot_accepts_component_range_endpoints() -> None:
    snapshot = ImuTelemetrySnapshot(
        buoy_id="buoy-1",
        acceleration_x_mps2=-200,
        acceleration_y_mps2=200,
        acceleration_z_mps2=0,
        angular_velocity_x_dps=-2000,
        angular_velocity_y_dps=2000,
        angular_velocity_z_dps=0,
        measured_at=datetime.now(timezone.utc),
    )

    assert snapshot.acceleration_x_mps2 == -200
    assert snapshot.acceleration_y_mps2 == 200
    assert snapshot.angular_velocity_x_dps == -2000
    assert snapshot.angular_velocity_y_dps == 2000


def test_location_snapshot_accepts_geographic_and_gnss_boundaries() -> None:
    snapshot = LocationTelemetrySnapshot(
        buoy_id="buoy-1",
        latitude=90,
        longitude=180,
        measured_at=datetime.now(timezone.utc),
        altitude_meters=20000,
        speed_mps=100,
        hdop=100,
        satellites=100,
    )

    assert snapshot.latitude == 90
    assert snapshot.longitude == 180
    assert snapshot.altitude_meters == 20000
    assert snapshot.speed_mps == 100


@pytest.mark.parametrize(
    "overrides,error", [
        ({"latitude": 90.01}, "Latitude"),
        ({"longitude": -180.01}, "Longitude"),
        ({"altitude_meters": -1000.01}, "GNSS altitude"),
        ({"speed_mps": 100.01}, "GNSS speed"),
        ({"hdop": 0}, "GNSS HDOP"),
        ({"satellites": 101}, "GNSS satellite count"),
    ],
)
def test_location_snapshot_rejects_values_outside_domain_range(
    overrides: dict[str, object],
    error: str,
) -> None:
    values: dict[str, object] = {
        "buoy_id": "buoy-1",
        "latitude": 0,
        "longitude": 0,
        "measured_at": datetime.now(timezone.utc),
    }
    values.update(overrides)

    with pytest.raises(ValueError, match=error):
        LocationTelemetrySnapshot(**values)


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


def test_battery_snapshot_accepts_percentage_range_endpoints() -> None:
    measured_at = datetime.now(timezone.utc)
    empty = BatteryTelemetrySnapshot("buoy-1", 0, "A", measured_at)
    full = BatteryTelemetrySnapshot("buoy-1", 100, "B", measured_at)

    assert empty.battery_percent == 0
    assert full.battery_percent == 100


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
