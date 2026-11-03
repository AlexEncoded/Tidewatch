import pytest

from app.application.sensor_reading_metrics import record_sensor_reading_metrics


class FakeMetricSample:
    def __init__(
        self,
        calls: list[tuple[str, dict[str, object], str, float | None]],
        name: str,
    ) -> None:
        self.calls = calls
        self.name = name
        self.labels_value: dict[str, object] = {}

    def labels(self, **labels: str) -> "FakeMetricSample":
        self.labels_value = labels
        return self

    def inc(self, amount: float = 1) -> None:
        self.calls.append((self.name, self.labels_value, "inc", amount))

    def set(self, value: float) -> None:
        self.calls.append((self.name, self.labels_value, "set", value))


class FakeTelemetryMetrics:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object], str, float | None]] = []

    def metric(self, name: str) -> FakeMetricSample:
        return FakeMetricSample(self.calls, name)


@pytest.mark.parametrize(
    "family,field,value,gauge",
    [
        ("wind", "wind_speed_mps", 3.2, "current_wind_speed_mps"),
        ("ambient_light", "illuminance_lux", 25, "current_ambient_light_lux"),
        ("temperature", "temperature_celsius", 18, "current_temperature_celsius"),
        ("pressure", "pressure_kpa", 100, "current_pressure_kpa"),
        ("salinity", "salinity_psu", 35, "current_salinity_psu"),
        ("marine_current", "current_speed_mps", 0.5, "current_marine_current_speed_mps"),
        ("turbidity", "turbidity_ntu", 2, "current_turbidity_ntu"),
        ("dissolved_oxygen", "dissolved_oxygen_mg_l", 8, "current_dissolved_oxygen_mg_l"),
        ("ph", "ph", 7, "current_ph"),
        ("conductivity", "conductivity_us_cm", 500, "current_conductivity_us_cm"),
        ("chlorophyll_a", "chlorophyll_a_ug_l", 4, "current_chlorophyll_a_ug_l"),
        ("rainfall", "rainfall_mm_h", 1, "current_rainfall_mm_h"),
        ("humidity", "humidity_percent", 60, "current_humidity_percent"),
        ("air_temperature", "air_temperature_celsius", 15, "current_air_temperature_celsius"),
        (
            "atmospheric_pressure",
            "atmospheric_pressure_kpa",
            100,
            "current_atmospheric_pressure_kpa",
        ),
        ("acoustic_altimeter", "depth_meters", 3, "current_acoustic_altimeter_depth_meters"),
        (
            "underwater_acoustic",
            "echo_intensity_db",
            20,
            "current_underwater_acoustic_echo_intensity_db",
        ),
    ],
)
def test_sensor_family_metrics_use_existing_counter_and_gauge(
    family: str, field: str, value: float, gauge: str
) -> None:
    metrics = FakeTelemetryMetrics()

    record_sensor_reading_metrics(metrics, "TW-1", family, "A", "good", {field: value})

    assert any(
        name == f"{family}_readings_total"
        and operation == "inc"
        and labels == {"buoy_id": "TW-1", "sensor_channel": "A"}
        for name, labels, operation, _ in metrics.calls
    )
    assert any(
        name == gauge and operation == "set" and recorded_value == value
        for name, _, operation, recorded_value in metrics.calls
    )


def test_sensor_reading_metrics_publish_current_values_quality_and_imu_axes() -> None:
    metrics = FakeTelemetryMetrics()

    record_sensor_reading_metrics(
        metrics, "TW-1", "imu", "B", "suspect",
        {
            "acceleration_x_mps2": 1.0,
            "acceleration_y_mps2": 2.0,
            "acceleration_z_mps2": 3.0,
            "angular_velocity_x_dps": 4.0,
            "angular_velocity_y_dps": 5.0,
            "angular_velocity_z_dps": 6.0,
        },
    )

    assert ("imu_readings_total", {"buoy_id": "TW-1", "sensor_channel": "B"}, "inc", 1) in metrics.calls
    assert (
        "current_imu_acceleration_mps2",
        {"buoy_id": "TW-1", "sensor_channel": "B", "axis": "x"},
        "set",
        1.0,
    ) in metrics.calls
    assert (
        "current_imu_angular_velocity_dps",
        {"buoy_id": "TW-1", "sensor_channel": "B", "axis": "z"},
        "set",
        6.0,
    ) in metrics.calls
    assert (
        "reading_quality_total",
        {
            "buoy_id": "TW-1",
            "sensor_family": "imu",
            "sensor_channel": "B",
            "quality": "suspect",
        },
        "inc",
        1,
    ) in metrics.calls


def test_sensor_reading_metrics_reject_unknown_families() -> None:
    with pytest.raises(ValueError, match="Unsupported sensor family"):
        record_sensor_reading_metrics(FakeTelemetryMetrics(), "TW-1", "unknown", "A", "good", {})
