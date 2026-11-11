from datetime import datetime, timezone

from app.application.maintenance_notifications import (
    MaintenanceNotificationTransport,
    build_maintenance_notification_payload,
    deliver_maintenance_notification,
    enqueue_maintenance_notification,
    maintenance_notification_idempotency_key,
)
from app.domain.maintenance import MaintenanceIssueSnapshot
from app.domain.maintenance_issues import build_reading_quality_issues


def test_callable_satisfies_notification_transport_port() -> None:
    def transport(url: str, *, json: dict, timeout: float):
        return None

    assert isinstance(transport, MaintenanceNotificationTransport)


def test_maintenance_notification_payload_serializes_issue_contracts() -> None:
    issue = MaintenanceIssueSnapshot(
        buoy_id="buoy-1",
        buoy_name="North buoy",
        issue_type="low_battery",
        severity="warning",
        message="Battery level is low",
    )

    payload = build_maintenance_notification_payload([issue])

    assert payload["source"] == "tidewatch"
    assert payload["issues"] == [
        {
            "buoy_id": issue.buoy_id,
            "buoy_name": issue.buoy_name,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "message": issue.message,
        }
    ]


def test_enqueue_maintenance_notification_persists_domain_issue_and_key() -> None:
    issue = MaintenanceIssueSnapshot(
        buoy_id="buoy-1",
        buoy_name="North buoy",
        issue_type="low_battery",
        severity="warning",
        message="Battery level is low",
    )
    requested_at = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
    stored = object()

    class JobStore:
        def enqueue(self, idempotency_key, payload, issue_count, now):
            self.arguments = (idempotency_key, payload, issue_count, now)
            return stored

    jobs = JobStore()

    result = enqueue_maintenance_notification(
        jobs, [issue], requested_at, "client-request-1"
    )

    assert result is stored
    key, payload, issue_count, enqueued_at = jobs.arguments
    assert key == "client-request-1"
    assert payload["source"] == "tidewatch"
    assert payload["issues"] == [
        {
            "buoy_id": "buoy-1",
            "buoy_name": "North buoy",
            "issue_type": "low_battery",
            "severity": "warning",
            "message": "Battery level is low",
        }
    ]
    assert payload["notification_idempotency_key"] == key
    assert issue_count == 1
    assert enqueued_at == requested_at


def test_generated_notification_key_is_stable_within_its_time_bucket() -> None:
    payload = {"source": "tidewatch", "issues": []}
    first_time = datetime(2026, 11, 11, 12, 1, tzinfo=timezone.utc)
    same_bucket = datetime(2026, 11, 11, 12, 14, tzinfo=timezone.utc)
    next_bucket = datetime(2026, 11, 11, 12, 16, tzinfo=timezone.utc)

    first_key = maintenance_notification_idempotency_key(payload, None, first_time)

    assert maintenance_notification_idempotency_key(payload, None, same_bucket) == first_key
    assert maintenance_notification_idempotency_key(payload, None, next_bucket) != first_key


def test_maintenance_notification_delivery_uses_injected_transport() -> None:
    issue = MaintenanceIssueSnapshot(
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


def test_reading_quality_issues_are_built_without_api_dependencies() -> None:
    issues = build_reading_quality_issues(
        "buoy-1",
        "North buoy",
        {
            "temperature": [type("Reading", (), {"quality": "invalid"})()],
            "pressure": [],
            "salinity": [],
        },
    )

    assert len(issues) == 1
    assert issues[0].issue_type == "invalid_reading"
