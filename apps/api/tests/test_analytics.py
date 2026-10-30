from datetime import datetime, timedelta, timezone
from math import pi, sin
from types import SimpleNamespace

import pytest

from app.domain.movement import distance_between_points, estimate_movement
from app.domain.battery_health import estimate_battery_health
from app.domain.battery_analysis import BatterySample, estimate_battery_discharge
from app.domain.battery_analysis import BatteryAnalysisSnapshot
from app.domain.temperature import estimate_temperature
from app.domain.pressure import estimate_pressure
from app.domain.wave import (
    estimate_fused_wave_period,
    estimate_wave,
    estimate_wave_period,
)
from app.application.wave_analysis import analyze_wave_for_buoy
from app.domain.wave import WaveAnalysisSnapshot
from app.application.movement_analysis import analyze_movement_for_buoy
from app.domain.movement import MovementAnalysisSnapshot
from app.application.pressure_analysis import analyze_pressure_for_buoy
from app.domain.pressure import PressureAnalysisSnapshot
from app.application.battery_analysis import analyze_battery_for_buoy
from app.application.temperature_analysis import (
    analyze_temperature_for_buoy,
    analyze_temperature_readings,
    list_valid_temperature_readings,
)
from app.domain.temperature import TemperatureAnalysisSnapshot
from app.application.battery_health import analyze_battery_health_for_buoy
from app.domain.battery_health import BatteryHealthSnapshot
from app.domain.sensor_health import decide_channel, evaluate_sensor_health
from app.domain.maintenance import is_buoy_silent
from app.domain.reading_quality import classify_latest_readings
from app.domain.sensor_completeness import missing_sensor_channels
from app.domain.telemetry import latest_usable_reading
from app.domain.directions import circular_difference_degrees
from app.domain.vectors import euclidean_difference
from app.domain.deltas import absolute_difference
from app.domain.sensor_health_rules import degraded_sensor_names
from app.domain.sensor_status import sensor_health_status


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


def test_movement_domain_normalizes_mixed_datetime_awareness() -> None:
    locations = [
        SimpleNamespace(
            latitude=36.71,
            longitude=3.11,
            measured_at=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
        ),
        SimpleNamespace(
            latitude=36.7,
            longitude=3.1,
            measured_at=datetime(2024, 1, 1, 0, 0),
        ),
    ]

    estimate = estimate_movement(locations)

    assert estimate.average_speed_mps is not None


def test_movement_application_service_uses_a_telemetry_port() -> None:
    class FakeReader:
        def buoy_exists(self, buoy_id):
            return buoy_id != "missing"

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(latitude=36.71, longitude=3.11, measured_at=datetime(2024, 1, 1, 0, 1)),
                SimpleNamespace(latitude=36.7, longitude=3.1, measured_at=datetime(2024, 1, 1, 0, 0)),
            ]

    analysis = analyze_movement_for_buoy(FakeReader(), "TW-PORT", 10)

    assert isinstance(analysis, MovementAnalysisSnapshot)
    assert analysis.buoy_id == "TW-PORT"
    assert analysis.sample_count == 2
    assert analysis.confidence == "experimental"



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

    assert isinstance(analysis, PressureAnalysisSnapshot)
    assert analysis.sample_count == 2
    assert analysis.estimated_wave_height_m is None
    assert analysis.confidence == "insufficient_data"


def test_wave_analysis_returns_insufficient_data_without_vertical_samples() -> None:
    class EmptyReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return []

        def list_locations(self, buoy_id, limit):
            return [SimpleNamespace(altitude_meters=None)]

    analysis = analyze_wave_for_buoy(EmptyReader(), "TW-TEST", 10, 0.1)

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


def test_wave_domain_service_estimates_period_from_upward_crossings() -> None:
    samples = [
        (datetime(2024, 1, 1, 0, 0), -1.0),
        (datetime(2024, 1, 1, 0, 1), 1.0),
        (datetime(2024, 1, 1, 0, 2), -1.0),
        (datetime(2024, 1, 1, 0, 3), 1.0),
    ]

    assert estimate_wave_period(samples) == 120.0


def test_wave_period_domain_normalizes_mixed_datetime_awareness() -> None:
    samples = [
        (datetime(2024, 1, 1, 0, 0), -1.0),
        (datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), 1.0),
        (datetime(2024, 1, 1, 0, 2), -1.0),
        (datetime(2024, 1, 1, 0, 3, tzinfo=timezone.utc), 1.0),
    ]

    assert estimate_wave_period(samples) == 120.0


def test_wave_period_domain_interpolates_between_samples() -> None:
    samples = [
        (datetime(2024, 1, 1, 0, 0), -3.0),
        (datetime(2024, 1, 1, 0, 1), 1.0),
        (datetime(2024, 1, 1, 0, 2), -1.0),
        (datetime(2024, 1, 1, 0, 3), 3.0),
    ]

    assert estimate_wave_period(samples) == 90.0


def test_wave_period_domain_orders_samples_by_timestamp() -> None:
    samples = [
        (datetime(2024, 1, 1, 0, 3), 1.0),
        (datetime(2024, 1, 1, 0, 1), 1.0),
        (datetime(2024, 1, 1, 0, 2), -1.0),
        (datetime(2024, 1, 1, 0, 0), -1.0),
    ]

    assert estimate_wave_period(samples) == 120.0


def test_fused_wave_period_averages_agreeing_gnss_and_imu_estimates() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    gnss = [
        (start + timedelta(seconds=seconds), sin(2 * pi * seconds / 8))
        for seconds in range(33)
    ]
    imu = [
        (start + timedelta(seconds=seconds), 9.81 + 0.5 * sin(2 * pi * seconds / 8))
        for seconds in range(33)
    ]

    estimate = estimate_fused_wave_period(gnss, imu)
    assert estimate.estimated_period_seconds == 8.0
    assert estimate.confidence == "experimental"


def test_fused_wave_period_withholds_disagreeing_sensor_estimates() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    timestamps = range(0, 601, 10)
    gnss = [
        (start + timedelta(seconds=seconds), sin(2 * pi * seconds / 60))
        for seconds in timestamps
    ]
    imu = [
        (start + timedelta(seconds=seconds), sin(2 * pi * seconds / 120))
        for seconds in range(0, 601, 10)
    ]

    estimate = estimate_fused_wave_period(gnss, imu)
    assert estimate.estimated_period_seconds is None
    assert estimate.confidence == "sensor_disagreement"


def test_fused_wave_period_uses_the_only_available_modality() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    imu = [
        (start + timedelta(seconds=seconds), sin(2 * pi * seconds / 12))
        for seconds in range(49)
    ]

    estimate = estimate_fused_wave_period([], imu)
    assert estimate.estimated_period_seconds == 12.0
    assert estimate.confidence == "partial"


def test_wave_application_service_uses_a_telemetry_port() -> None:
    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [
                SimpleNamespace(
                    acceleration_z_mps2=value,
                    measured_at=datetime(2026, 1, 1, 0, index, tzinfo=timezone.utc),
                )
                for index, value in enumerate((9.7, 10.2))
            ]

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(
                    altitude_meters=value,
                    measured_at=datetime(2026, 1, 1, 0, index, tzinfo=timezone.utc),
                )
                for index, value in enumerate((2.0, 2.4))
            ]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-PORT", 10, 0.1)

    assert isinstance(analysis, WaveAnalysisSnapshot)
    assert analysis.buoy_id == "TW-PORT"
    assert analysis.estimated_wave_height_m == 0.225


def test_wave_application_service_forwards_calibration_factor() -> None:
    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [
                SimpleNamespace(
                    acceleration_z_mps2=value,
                    measured_at=datetime(2026, 1, 1, 0, index, tzinfo=timezone.utc),
                )
                for index, value in enumerate((9.7, 10.2))
            ]

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(
                    altitude_meters=value,
                    measured_at=datetime(2026, 1, 1, 0, index, tzinfo=timezone.utc),
                )
                for index, value in enumerate((2.0, 2.1))
            ]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-CAL", 10, 0.2)

    assert analysis.gnss_vertical_range_m == 0.1
    assert analysis.estimated_wave_height_m == 0.1


def test_wave_application_service_filters_invalid_telemetry() -> None:
    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [
                SimpleNamespace(
                    acceleration_z_mps2=9.7,
                    quality="good",
                    measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
                SimpleNamespace(
                    acceleration_z_mps2=100.0,
                    quality="invalid",
                    measured_at=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
                ),
            ]

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(
                    altitude_meters=2.0,
                    quality="good",
                    measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
                SimpleNamespace(
                    altitude_meters=20.0,
                    quality="invalid",
                    measured_at=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
                ),
            ]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-WAVE", 10, 0.1)

    assert analysis.sample_count == 1
    assert analysis.confidence == "insufficient_data"


def test_wave_application_service_fuses_only_the_shared_time_range() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [
                SimpleNamespace(
                    measured_at=start + timedelta(seconds=offset),
                    acceleration_z_mps2=value,
                )
                for offset, value in ((0, 0.0), (10, 1.0), (20, 100.0))
            ]

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(
                    measured_at=start + timedelta(seconds=offset), altitude_meters=value
                )
                for offset, value in ((10, 2.0), (20, 2.2), (30, 200.0))
            ]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-SYNC", 10, 0.1)

    assert analysis.imu_vertical_acceleration_range_mps2 == 99.0
    assert analysis.gnss_vertical_range_m == 0.2


def test_wave_application_service_does_not_fuse_disjoint_time_ranges() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [
                SimpleNamespace(
                    measured_at=start + timedelta(seconds=offset),
                    acceleration_z_mps2=float(offset),
                )
                for offset in (0, 10)
            ]

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(
                    measured_at=start + timedelta(seconds=offset),
                    altitude_meters=float(offset),
                )
                for offset in (20, 30)
            ]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-DISJOINT", 10, 0.1)

    assert analysis.estimated_wave_height_m is None
    assert analysis.confidence == "insufficient_data"
    assert analysis.period_confidence == "insufficient_data"


def test_wave_application_service_does_not_report_period_outside_shared_window() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    locations = [
        SimpleNamespace(
            measured_at=start + timedelta(seconds=seconds),
            altitude_meters=sin(2 * pi * seconds / 8),
        )
        for seconds in range(33)
    ]
    imu_readings = [
        SimpleNamespace(
            measured_at=start + timedelta(seconds=100 + seconds),
            acceleration_z_mps2=9.81 + 0.5 * sin(2 * pi * seconds / 8),
        )
        for seconds in range(33)
    ]

    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return imu_readings

        def list_locations(self, buoy_id, limit):
            return locations

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-NO-OVERLAP", 40, 0.1)

    assert analysis.estimated_period_seconds is None
    assert analysis.estimated_wave_height_m is None


def test_wave_application_service_excludes_suspect_readings() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return [
                SimpleNamespace(
                    measured_at=start + timedelta(seconds=offset),
                    acceleration_z_mps2=value,
                    quality=quality,
                )
                for offset, value, quality in (
                    (0, 0.0, "good"),
                    (1, 0.5, "good"),
                    (2, 100.0, "suspect"),
                )
            ]

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(
                    measured_at=start + timedelta(seconds=offset),
                    altitude_meters=value,
                    quality=quality,
                )
                for offset, value, quality in (
                    (0, 2.0, "good"),
                    (1, 2.4, "good"),
                    (2, 200.0, "suspect"),
                )
            ]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-SUSPECT", 10, 0.1)

    assert analysis.gnss_vertical_range_m == 0.4
    assert analysis.imu_vertical_acceleration_range_mps2 == 0.5
    assert analysis.estimated_wave_height_m == 0.225


def test_wave_application_service_keeps_single_modality_estimate_partial() -> None:
    class FakeReader:
        def list_imu(self, buoy_id, limit, sensor_channel):
            return []

        def list_locations(self, buoy_id, limit):
            return [
                SimpleNamespace(
                    altitude_meters=value,
                    measured_at=datetime(
                        2026, 1, 1, 0, index, tzinfo=timezone.utc
                    ),
                )
                for index, value in enumerate((2.0, 2.4))
            ]

    analysis = analyze_wave_for_buoy(FakeReader(), "TW-GNSS-ONLY", 10, 0.1)

    assert analysis.estimated_wave_height_m == 0.4
    assert analysis.confidence == "partial"
    assert analysis.imu_vertical_acceleration_range_mps2 is None


def test_sensor_health_averages_consistent_redundant_channels() -> None:
    assert decide_channel(True, True) == "average"


def test_sensor_health_invalidates_degraded_redundant_channels() -> None:
    assert decide_channel(True, True, degraded=True) == "invalid"


def test_sensor_health_falls_back_to_available_channel() -> None:
    assert decide_channel(True, False) == "fallback_a"
    assert decide_channel(False, True) == "fallback_b"


def test_sensor_health_invalidates_missing_channels() -> None:
    assert decide_channel(False, False) == "invalid"


def test_sensor_health_evaluation_composes_domain_rules() -> None:
    evaluation = evaluate_sensor_health(
        {"temperature": 0.6},
        {"temperature": {"A": object(), "B": None}},
    )

    assert evaluation.status == "degraded"
    assert evaluation.degraded_sensors == ["temperature"]
    assert evaluation.missing_sensors == ["temperature:B"]
    assert evaluation.decisions == {"temperature": "fallback_a"}


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


def test_vector_domain_rejects_different_dimensions() -> None:
    with pytest.raises(ValueError, match="same dimension"):
        euclidean_difference((1, 2), (1, 2, 3))


def test_delta_domain_calculates_absolute_scalar_difference() -> None:
    assert absolute_difference(2.5, 7.0) == 4.5


def test_sensor_health_rules_include_aggregate_degraded_families() -> None:
    degraded = degraded_sensor_names(
        {
            "temperature": 0.6,
            "wind_speed": 0.6,
            "wind_direction": None,
            "marine_current_speed": 0.3,
        }
    )

    assert degraded == ["temperature", "wind_speed", "marine_current_speed", "wind", "marine_current"]


def test_sensor_status_domain_distinguishes_available_health_states() -> None:
    assert sensor_health_status(False, False, False) == "insufficient_data"
    assert sensor_health_status(False, False, True) == "degraded"
    assert sensor_health_status(True, False, False) == "consistent"
    assert sensor_health_status(True, True, False) == "degraded"
    assert sensor_health_status(True, False, True) == "degraded"


def test_battery_health_domain_service_detects_lower_degraded_device() -> None:
    estimate = estimate_battery_health(72.0, 85.0, threshold=5.0)

    assert estimate.status == "degraded"
    assert estimate.delta_percent == 13.0
    assert estimate.degraded_devices == ["A"]


def test_battery_health_domain_service_accepts_exact_threshold() -> None:
    estimate = estimate_battery_health(80.0, 85.0, threshold=5.0)

    assert estimate.status == "consistent"
    assert estimate.delta_percent == 5.0
    assert estimate.degraded_devices == []


def test_battery_health_domain_service_requires_both_devices() -> None:
    estimate = estimate_battery_health(72.0, None, threshold=5.0)

    assert estimate.status == "insufficient_data"
    assert estimate.delta_percent is None


@pytest.mark.parametrize("threshold", [-1.0, float("nan"), float("inf")])
def test_battery_health_domain_service_rejects_invalid_threshold(
    threshold: float,
) -> None:
    with pytest.raises(ValueError, match="non-negative finite number"):
        estimate_battery_health(72.0, 85.0, threshold)


@pytest.mark.parametrize(
    "percentage", [-0.1, 100.1, float("nan"), float("inf")]
)
def test_battery_health_domain_service_rejects_invalid_battery_percentages(
    percentage: float,
) -> None:
    with pytest.raises(ValueError, match="battery percentage must be between 0 and 100"):
        estimate_battery_health(percentage, 85.0, threshold=5.0)


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

    assert isinstance(analysis, BatteryAnalysisSnapshot)
    assert analysis.device_id == "B"
    assert analysis.discharge_rate_percent_per_hour == 5.0


def test_battery_health_application_service_reads_both_devices() -> None:
    class FakeReader:
        def latest_battery(self, buoy_id, device_id=None):
            if device_id == "A":
                return SimpleNamespace(battery_percent=72.0)
            return SimpleNamespace(battery_percent=85.0)

    health = analyze_battery_health_for_buoy(FakeReader(), "TW-HEALTH", 5.0)

    assert isinstance(health, BatteryHealthSnapshot)
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

    assert isinstance(analysis, TemperatureAnalysisSnapshot)
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


def test_wave_fusion_recovers_known_period_from_synthetic_gnss_and_imu() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    period_seconds = 8.0
    timestamps = [index * 0.25 for index in range(97)]
    locations = [
        SimpleNamespace(
            measured_at=start + timedelta(seconds=seconds),
            altitude_meters=4.2 + 0.75 * sin(2 * pi * seconds / period_seconds),
            quality="good",
        )
        for seconds in timestamps
    ]
    imu_readings = [
        SimpleNamespace(
            measured_at=start + timedelta(seconds=seconds),
            acceleration_z_mps2=9.81 + 0.4 * sin(2 * pi * seconds / period_seconds),
            quality="good",
        )
        for seconds in timestamps
    ]

    class SyntheticReader:
        def list_locations(self, buoy_id, limit):
            return locations

        def list_imu(self, buoy_id, limit, sensor_channel):
            return imu_readings

    analysis = analyze_wave_for_buoy(
        SyntheticReader(), "TW-SYNTHETIC-WAVE", len(timestamps), 0.1
    )

    assert analysis.sample_count == len(timestamps)
    assert analysis.gnss_vertical_range_m == pytest.approx(1.5)
    assert analysis.imu_vertical_acceleration_range_mps2 == pytest.approx(0.8)
    assert analysis.estimated_wave_height_m == pytest.approx(0.79)
    assert analysis.estimated_period_seconds == pytest.approx(period_seconds)
    assert analysis.period_confidence == "experimental"
    assert analysis.confidence == "experimental"
