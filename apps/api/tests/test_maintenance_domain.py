import pytest

from app.domain.maintenance import low_battery_severity


@pytest.mark.parametrize(
    ("battery_percent", "expected"),
    [(5, "critical"), (9.99, "critical"), (10, "warning"), (19.99, "warning"), (20, None)],
)
def test_low_battery_severity_boundaries(battery_percent, expected) -> None:
    assert low_battery_severity(battery_percent) == expected
