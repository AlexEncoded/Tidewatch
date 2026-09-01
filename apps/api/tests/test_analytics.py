from datetime import datetime
from types import SimpleNamespace

from app.analytics import analyze_pressure, analyze_wave, distance_between_points
from app.analytics import analyze_movement
from app.domain.movement import estimate_movement
from app.domain.battery_health import estimate_battery_health
from app.domain.battery_analysis import BatterySample, estimate_battery_discharge
from app.domain.temperature import estimate_temperature
from app.domain.pressure import estimate_pressure
from app.domain.wave import estimate_wave
from app.application.wave_analysis import analyze_wave_for_buoy
from app.application.movement_analysis import analyze_movement_for_buoy
from app.application.pressure_analysis import analyze_pressure_for_buoy
from app.application.battery_analysis import analyze_battery_for_buoy
from app.application.temperature_analysis import (
    analyze_temperature_for_buoy,
    analyze_temperature_readings,
    list_valid_temperature_readings,
)
from app.application.battery_health import analyze_battery_health_for_buoy
from app.domain.sensor_health import decide_channel
from app.domain.maintenance import is_buoy_silent
from app.domain.reading_quality import classify_latest_readings
from app.domain.sensor_completeness import missing_sensor_channels
from app.domain.telemetry import latest_usable_reading
from app.domain.directions import circular_difference_degrees
from app.domain.vectors import euclidean_difference
from app.models import PressureReading


def test_distance_between_points_is_zero_for_same_coordinates() -> None:
    assert distance_between_points(36.7, 3.1, 36.7, 3.1) == 0


def test_movement_domain_service_is_independent_from_persistence_models() -> None:
    locations = [
        SimpleNamespace(latitude=36.71, longitude=3.11, measured_at=datetime(2024, 1, 1, 0, 1)),
        SimpleNamespace(latitude=36.7, longitude=3.1, measured_at=datetime(2024, 1, 1, 0, 0)),
    ]

    estimate = estimate_movement(locations)

    assert estimate.sample_count == 2
    assert estimate.distance_travelled_m is not None
    assert estimate.confidence == "experimental"


def test_movement_analytics_adapter_preserves_buoy_contract() -> None:
    locations = [
        SimpleNamespace(latitude=36.71, longitude=3.11, measured_at=datetime(2024, 1, 1, 0, 1)),
        SimpleNamespace(latitude=36.7, longitude=3.1, measured_at=datetime(2024, 1, 1, 0, 0)),
    ]

    analysis = analyze_movement("TW-MOVE", locations)

    assert analysis.buoy_id == "TW-MOVE"
    assert analysis.confidence == "experimental"


def test_movement_application_service_uses_a_telemetry_port() -> None:
    class FakeReader:
        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(latitude=36.71, longitude=3.11, measured_at=datetime(2024, 1, 1, 0, 1)),
                SimpleNamespace(latitude=36.7, longitude=3.1, measured_at=datetime(2024, 1, 1, 0, 0)),
            ]

    analysis = analyze_movement_for_buoy(FakeReader(), "TW-PORT", 10)

    assert analysis.buoy_id == "TW-PORT"
    assert analysis.sample_count == 2
    assert analysis.confidence == "experimental"


def test_pressure_analysis_requires_three_samples_for_wave_estimate() -> None:
    readings = [
        PressureReading(buoy_id="TW-TEST", pressure_kpa=value)
        for value in (101.3, 101.8)
    ]

    analysis = analyze_pressure("TW-TEST", readings)

    assert analysis.pressure_range_kpa == 0.5
    assert analysis.estimated_wave_height_m is None
    assert analysis.confidence == "insufficient_data"


def test_pressure_domain_service_estimates_wave_height_and_sea_state() -> None:
    estimate = estimate_pressure([101.3, 102.0, 101.5])

    assert estimate.pressure_range_kpa == 0.7
    assert estimate.estimated_wave_height_m == 0.071
    assert estimate.sea_state == "calm"
    assert estimate.confidence == "experimental"


def test_pressure_application_service_filters_invalid_readings() -> None:
    class FakeReader:
        def list_pressures(self, buoy_id, limit, sensor_channel="A"):
            return [
                SimpleNamespace(pressure_kpa=101.3, quality="good"),
                SimpleNamespace(pressure_kpa=102.0, quality="good"),
                SimpleNamespace(pressure_kpa=110.0, quality="invalid"),
            ]

    analysis = analyze_pressure_for_buoy(FakeReader(), "TW-PRESS", 10)

    assert analysis.sample_count == 2
    assert analysis.estimated_wave_height_m is None
    assert analysis.confidence == "insufficient_data"


def test_wave_analysis_returns_insufficient_data_without_vertical_samples() -> None:
    analysis = analyze_wave("TW-TEST", [], [SimpleNamespace(altitude_meters=None)])

    assert analysis.sample_count == 1
    assert analysis.estimated_wave_height_m is None
    assert analysis.confidence == "insufficient_data"


def test_wave_domain_service_is_independent_from_persistence_models() -> None:
    estimate = estimate_wave((2.0, 2.4), (9.7, 10.2))

    assert estimate.gnss_vertical_range_m == 0.4
    assert estimate.imu_vertical_acceleration_range_mps2 == 0.5
    assert estimate.estimated_wave_height_m == 0.225
    assert estimate.confidence == "experimental"


def test_wave_domain_service_accepts_calibration_factor() -> None:
    estimate = estimate_wave((2.0, 2.4), (9.7, 10.2), imu_wave_height_factor=0.2)

    assert estimate.estimated_wave_height_m == 0.25


def test_wave_application_service_uses_a_telemetry_port() -> None:
    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [SimpleNamespace(acceleration_z_mps2=value) for value in (9.7, 10.2)]

        def list_locations(self, buoy_id, limit):
            return [SimpleNamespace(altitude_meters=value) for value in (2.0, 2.4)]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-PORT", 10, 0.1)

    assert analysis.buoy_id == "TW-PORT"
    assert analysis.estimated_wave_height_m == 0.225


def test_wave_application_service_forwards_calibration_factor() -> None:
    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [SimpleNamespace(acceleration_z_mps2=value) for value in (9.7, 10.2)]

        def list_locations(self, buoy_id, limit):
            return [SimpleNamespace(altitude_meters=value) for value in (2.0, 2.1)]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-CAL", 10, 0.2)

    assert analysis.gnss_vertical_range_m == 0.1
    assert analysis.estimated_wave_height_m == 0.1


def test_sensor_health_averages_consistent_redundant_channels() -> None:
    assert decide_channel(True, True) == "average"


def test_sensor_health_invalidates_degraded_redundant_channels() -> None:
    assert decide_channel(True, True, degraded=True) == "invalid"


def test_sensor_health_falls_back_to_available_channel() -> None:
    assert decide_channel(True, False) == "fallback_a"
    assert decide_channel(False, True) == "fallback_b"


def test_sensor_health_invalidates_missing_channels() -> None:
    assert decide_channel(False, False) == "invalid"


def test_maintenance_domain_detects_stale_active_buoy() -> None:
    now = datetime(2024, 1, 1, 1, 0)

    assert is_buoy_silent("active", datetime(2024, 1, 1, 0, 0), now, 3000) is True


def test_maintenance_domain_ignores_inactive_or_recent_buoys() -> None:
    now = datetime(2024, 1, 1, 1, 0)

    assert is_buoy_silent("inactive", datetime(2024, 1, 1, 0, 0), now, 3000) is False
    assert is_buoy_silent("active", datetime(2024, 1, 1, 0, 59), now, 3000) is False


def test_reading_quality_domain_classifies_latest_sensor_states() -> None:
    invalid, suspect = classify_latest_readings(
        {
            "temperature": [SimpleNamespace(quality="invalid")],
            "pressure": [SimpleNamespace(quality="suspect")],
            "salinity": [SimpleNamespace(quality="good")],
            "wind": [],
        }
    )

    assert invalid == ["temperature"]
    assert suspect == ["pressure"]


def test_sensor_completeness_domain_lists_partial_redundancy() -> None:
    missing = missing_sensor_channels(
        {
            "temperature": {"A": object(), "B": None},
            "pressure": {"A": None, "B": None},
            "salinity": {"A": object(), "B": object()},
        }
    )

    assert missing == ["temperature:B"]


def test_telemetry_domain_skips_invalid_and_stale_readings() -> None:
    now = datetime(2024, 1, 1, 1, 0)
    readings = [
        SimpleNamespace(quality="invalid", measured_at=datetime(2024, 1, 1, 0, 59)),
        SimpleNamespace(quality="good", measured_at=datetime(2024, 1, 1, 0, 0)),
        SimpleNamespace(quality="good", measured_at=datetime(2024, 1, 1, 0, 59)),
    ]

    usable = latest_usable_reading(readings, max_age_seconds=300, now=now)

    assert usable == [readings[2]]


def test_direction_domain_uses_smallest_circular_difference() -> None:
    assert circular_difference_degrees(359, 1) == 2
    assert circular_difference_degrees(10, 190) == 180


def test_vector_domain_calculates_euclidean_difference() -> None:
    assert euclidean_difference((1, 2, 3), (4, 6, 3)) == 5


def test_battery_health_domain_service_detects_lower_degraded_device() -> None:
    estimate = estimate_battery_health(72.0, 85.0, threshold=5.0)

    assert estimate.status == "degraded"
    assert estimate.delta_percent == 13.0
    assert estimate.degraded_devices == ["A"]


def test_battery_health_domain_service_requires_both_devices() -> None:
    estimate = estimate_battery_health(72.0, None, threshold=5.0)

    assert estimate.status == "insufficient_data"
    assert estimate.delta_percent is None


def test_battery_analysis_domain_service_estimates_discharge() -> None:
    readings = [
        BatterySample(80.0, datetime(2024, 1, 1, 2, 0)),
        BatterySample(90.0, datetime(2024, 1, 1, 0, 0)),
    ]

    estimate = estimate_battery_discharge(readings)

    assert estimate.change_percent == -10.0
    assert estimate.discharge_rate_percent_per_hour == 5.0
    assert estimate.estimated_hours_remaining == 16.0
    assert estimate.confidence == "experimental"


def test_battery_application_service_uses_device_port() -> None:
    class FakeReader:
        def list_batteries(self, buoy_id, limit, device_id=None):
            assert device_id == "B"
            return [
                SimpleNamespace(battery_percent=80.0, measured_at=datetime(2024, 1, 1, 2, 0)),
                SimpleNamespace(battery_percent=90.0, measured_at=datetime(2024, 1, 1, 0, 0)),
            ]

    analysis = analyze_battery_for_buoy(FakeReader(), "TW-BAT", "B", 10)

    assert analysis.device_id == "B"
    assert analysis.discharge_rate_percent_per_hour == 5.0


def test_battery_health_application_service_reads_both_devices() -> None:
    class FakeReader:
        def latest_battery(self, buoy_id, device_id=None):
            if device_id == "A":
                return SimpleNamespace(battery_percent=72.0)
            return SimpleNamespace(battery_percent=85.0)

    health = analyze_battery_health_for_buoy(FakeReader(), "TW-HEALTH", 5.0)

    assert health.status == "degraded"
    assert health.degraded_devices == ["A"]


def test_temperature_domain_service_detects_rising_anomaly() -> None:
    estimate = estimate_temperature([30.0, 20.0, 20.0], threshold=2.0)

    assert estimate.trend == "rising"
    assert estimate.average_temperature == 23.33
    assert estimate.is_anomaly is True
    assert estimate.anomaly_reason is not None


def test_temperature_application_service_filters_invalid_readings() -> None:
    class FakeReader:
        def list_temperatures(self, buoy_id, limit, sensor_channel="A"):
            return [
                SimpleNamespace(temperature_celsius=30.0, quality="good"),
                SimpleNamespace(temperature_celsius=20.0, quality="good"),
                SimpleNamespace(temperature_celsius=100.0, quality="invalid"),
            ]

    analysis = analyze_temperature_for_buoy(FakeReader(), "TW-TEMP", 10, 2.0)

    assert analysis.sample_count == 2
    assert analysis.latest_temperature == 30.0
    assert analysis.trend == "rising"


def test_temperature_application_helpers_share_filtered_readings() -> None:
    class FakeReader:
        def list_temperatures(self, buoy_id, limit, sensor_channel="A"):
            return [
                SimpleNamespace(temperature_celsius=30.0, quality="good"),
                SimpleNamespace(temperature_celsius=100.0, quality="invalid"),
            ]

    readings = list_valid_temperature_readings(FakeReader(), "TW-TEMP", 10)
    analysis = analyze_temperature_readings("TW-TEMP", readings, 2.0)

    assert len(readings) == 1
    assert analysis.sample_count == 1
