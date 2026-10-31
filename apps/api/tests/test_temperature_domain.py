from datetime import datetime, timezone

import pytest

from app.domain.temperature import (
    TemperatureTelemetrySnapshot,
    analyze_temperature_samples,
    estimate_temperature,
    valid_temperature_readings,
)


def _reading(value: float, quality: str = "good") -> TemperatureTelemetrySnapshot:
    return TemperatureTelemetrySnapshot(
        buoy_id="buoy-1",
        temperature_celsius=value,
        measured_at=datetime(2026, 10, 31, tzinfo=timezone.utc),
        quality=quality,
    )


@pytest.mark.parametrize("threshold", [0.0, -1.0, float("nan"), float("inf")])
def test_temperature_estimate_rejects_invalid_anomaly_threshold(threshold: float):
    with pytest.raises(ValueError, match="positive finite number"):
        estimate_temperature([20.0], threshold)


@pytest.mark.parametrize("temperature", [-5.1, 45.1, float("nan"), float("inf")])
def test_temperature_estimate_rejects_values_outside_physical_range(
    temperature: float,
):
    with pytest.raises(ValueError, match="Sea temperature must be between -5 and 45"):
        estimate_temperature([temperature], 2.0)


def test_temperature_analysis_filters_invalid_quality_and_keeps_suspect_samples():
    readings = [
        _reading(25.0),
        _reading(20.0, quality="suspect"),
        _reading(45.0, quality="invalid"),
    ]

    assert valid_temperature_readings(readings) == readings[:2]
    analysis = analyze_temperature_samples("buoy-1", readings, threshold=2.0)

    assert analysis.sample_count == 2
    assert analysis.latest_temperature == 25.0
    assert analysis.trend == "rising"
