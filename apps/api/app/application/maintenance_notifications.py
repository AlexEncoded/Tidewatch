"""Application services for maintenance notifications."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class MaintenanceNotificationTransport(Protocol):
    """Port used to deliver a maintenance notification payload."""

    def __call__(self, url: str, *, json: dict, timeout: float):
        ...


def build_maintenance_notification_payload(issues: list) -> dict:
    """Build the stable webhook payload from maintenance issue contracts."""
    return {
        "source": "tidewatch",
        "issues": [issue.model_dump(mode="json") for issue in issues],
    }


def deliver_maintenance_notification(
    webhook_url: str,
    issues: list,
    transport: MaintenanceNotificationTransport,
) -> int:
    """Deliver maintenance issues through the injected notification port."""
    transport(
        webhook_url,
        json=build_maintenance_notification_payload(issues),
        timeout=5,
    ).raise_for_status()
    return len(issues)
