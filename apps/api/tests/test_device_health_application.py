from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.application.device_health import summarize_device_health


def test_device_health_marks_missing_and_old_active_heartbeats_stale() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    devices = [
        SimpleNamespace(
            buoy_id="buoy-1",
            device_id="unit-a",
            sensor_channel="A",
            status="active",
            last_seen_at=now - timedelta(minutes=31),
        ),
        SimpleNamespace(
            buoy_id="buoy-1",
            device_id="unit-b",
            sensor_channel="B",
            status="active",
            last_seen_at=None,
        ),
    ]

    health = summarize_device_health(devices, now, 30 * 60)

    assert [item.is_stale for item in health] == [True, True]
    assert health[0].age_seconds == 1860.0
    assert health[1].age_seconds is None


def test_device_health_does_not_mark_maintenance_device_stale() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    device = SimpleNamespace(
        buoy_id="buoy-1",
        device_id="unit-a",
        sensor_channel="A",
        status="maintenance",
        last_seen_at=None,
    )

    health = summarize_device_health([device], now, 30 * 60)

    assert health[0].is_stale is False
