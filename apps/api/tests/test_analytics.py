from types import SimpleNamespace

from app.analytics import analyze_pressure, analyze_wave, distance_between_points
from app.domain.wave import estimate_wave
from app.models import PressureReading


def test_distance_between_points_is_zero_for_same_coordinates() -> None:
    assert distance_between_points(36.7, 3.1, 36.7, 3.1) == 0


def test_pressure_analysis_requires_three_samples_for_wave_estimate() -> None:
    readings = [
        PressureReading(buoy_id="TW-TEST", pressure_kpa=value)
        for value in (101.3, 101.8)
    ]

    analysis = analyze_pressure("TW-TEST", readings)

    assert analysis.pressure_range_kpa == 0.5
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
