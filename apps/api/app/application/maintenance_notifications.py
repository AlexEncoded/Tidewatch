"""Application services for maintenance notifications."""


def build_maintenance_notification_payload(issues: list) -> dict:
    """Build the stable webhook payload from maintenance issue contracts."""
    return {
        "source": "tidewatch",
        "issues": [issue.model_dump(mode="json") for issue in issues],
    }
