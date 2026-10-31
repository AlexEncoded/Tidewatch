import pytest

from app.domain.sensor_health_rules import (
    SENSOR_DEGRADATION_THRESHOLDS,
    degraded_sensor_names,
)


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (0.5, []),
        (0.501, ["temperature"]),
        (None, []),
    ],
)
def test_sensor_degradation_uses_strict_sensor_specific_threshold(delta, expected):
    assert degraded_sensor_names({"temperature": delta}) == expected


def test_sensor_degradation_aggregates_wind_subchannels():
    assert degraded_sensor_names({"wind_speed": 0.6}) == ["wind_speed", "wind"]


@pytest.mark.parametrize("delta", [-0.1, float("nan"), float("inf")])
def test_sensor_degradation_rejects_invalid_delta(delta):
    with pytest.raises(ValueError, match="non-negative finite number"):
        degraded_sensor_names({"temperature": delta})


def test_sensor_degradation_rejects_unknown_sensor_name():
    with pytest.raises(ValueError, match="Unsupported sensor health deltas: mystery"):
        degraded_sensor_names({"mystery": 1.0})


def test_all_registered_sensor_thresholds_are_positive_finite_values():
    assert SENSOR_DEGRADATION_THRESHOLDS
    assert all(
        threshold > 0 and threshold < float("inf")
        for threshold in SENSOR_DEGRADATION_THRESHOLDS.values()
    )
