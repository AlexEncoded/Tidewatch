from datetime import datetime, timezone

from app.application.maintenance_issues import build_battery_maintenance_issues
from app.models import BatteryHealth


def test_battery_maintenance_service_reports_low_and_missing_units() -> None:
    battery_a = type("Battery", (), {"battery_percent": 8.0})()
    health = BatteryHealth(
        buoy_id="buoy-1",
        status="healthy",
        device_a_percent=8.0,
        device_b_percent=None,
        delta_percent=None,
        degraded_devices=[],
        checked_at=datetime.now(timezone.utc),
    )

    issues = build_battery_maintenance_issues(
        "buoy-1", "North buoy", {"A": battery_a, "B": None}, health
    )

    assert [issue.issue_type for issue in issues] == [
        "low_battery",
        "missing_redundant_device",
    ]
