from app.application.maintenance_notifications import (
    build_maintenance_notification_payload,
    deliver_maintenance_notification,
)
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


def test_maintenance_notification_delivery_uses_injected_transport() -> None:
    issue = MaintenanceIssue(
        buoy_id="buoy-1",
        buoy_name="North buoy",
        issue_type="silent_buoy",
        severity="warning",
        message="No telemetry",
    )
    calls = []

    class Response:
        def raise_for_status(self) -> None:
            calls.append("raised")

    def transport(url: str, *, json: dict, timeout: float) -> Response:
        calls.append((url, json, timeout))
        return Response()

    assert deliver_maintenance_notification(
        "https://example.test/hook", [issue], transport
    ) == 1
    assert calls[0][0] == "https://example.test/hook"
    assert calls[0][2] == 5
    assert calls[1] == "raised"
