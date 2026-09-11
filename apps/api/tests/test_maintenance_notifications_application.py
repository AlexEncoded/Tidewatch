from app.application.maintenance_notifications import build_maintenance_notification_payload
from app.models import MaintenanceIssue


def test_maintenance_notification_payload_serializes_issue_contracts() -> None:
    issue = MaintenanceIssue(
        buoy_id="buoy-1",
        buoy_name="North buoy",
        issue_type="low_battery",
        severity="warning",
        message="Battery level is low",
    )

    payload = build_maintenance_notification_payload([issue])

    assert payload["source"] == "tidewatch"
    assert payload["issues"] == [issue.model_dump(mode="json")]
