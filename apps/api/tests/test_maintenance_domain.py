from datetime import datetime, timezone

import pytest

from app.domain.maintenance import (
    is_buoy_drifting,
    is_buoy_silent,
    low_battery_severity,
    missing_redundant_battery_device,
)


@pytest.mark.parametrize(
    ("device_a_percent", "device_b_percent", "expected"),
    [(90, None, "B"), (None, 90, "A"), (90, 90, None), (None, None, None)],
)
def test_missing_redundant_battery_device(device_a_percent, device_b_percent, expected) -> None:
    assert missing_redundant_battery_device(device_a_percent, device_b_percent) == expected


@pytest.mark.parametrize(
    ("status", "last_seen_at", "max_age_seconds", "expected"),
    [
        ("inactive", datetime(2026, 1, 1, tzinfo=timezone.utc), 1, False),
        ("active", None, 1, False),
        ("active", datetime(2026, 1, 1, 0, 1), 60, False),
        ("active", datetime(2026, 1, 1), 60, True),
    ],
)
def test_buoy_silence_requires_active_recent_telemetry(
    status, last_seen_at, max_age_seconds, expected
) -> None:
    now = datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc)

    assert is_buoy_silent(status, last_seen_at, now, max_age_seconds) is expected


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
