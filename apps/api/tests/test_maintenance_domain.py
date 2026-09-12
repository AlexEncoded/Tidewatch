import pytest

from app.domain.maintenance import is_buoy_drifting, low_battery_severity


@pytest.mark.parametrize(
    ("average_speed_mps", "limit_mps", "expected"),
    [(None, 1, False), (1, 1, False), (1.01, 1, True)],
)
def test_buoy_drifting_uses_strict_limit(average_speed_mps, limit_mps, expected) -> None:
    assert is_buoy_drifting(average_speed_mps, limit_mps) is expected


@pytest.mark.parametrize(
    ("battery_percent", "expected"),
    [(5, "critical"), (9.99, "critical"), (10, "warning"), (19.99, "warning"), (20, None)],
)
def test_low_battery_severity_boundaries(battery_percent, expected) -> None:
    assert low_battery_severity(battery_percent) == expected
