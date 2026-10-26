"""Application services for maintenance notifications."""

from dataclasses import asdict, is_dataclass
from datetime import datetime
import hashlib
import json
from typing import Protocol, runtime_checkable


def _serialize_issue(issue) -> dict:
    if is_dataclass(issue):
        return asdict(issue)
    return issue.model_dump(mode="json")


@runtime_checkable
class MaintenanceNotificationTransport(Protocol):
    """Port used to deliver a maintenance notification payload."""

    def __call__(self, url: str, *, json: dict, timeout: float):
        ...


def build_maintenance_notification_payload(issues: list) -> dict:
    """Build the stable webhook payload from maintenance issue contracts."""
    return {
        "source": "tidewatch",
        "issues": [_serialize_issue(issue) for issue in issues],
    }


def maintenance_notification_idempotency_key(
    payload: dict,
    requested_key: str | None,
    now: datetime,
) -> str:
    """Use a client key or deduplicate identical requests within a 15-minute window."""
    if requested_key is not None:
        return requested_key
    bucket = int(now.timestamp()) // (15 * 60)
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{bucket}:{material}".encode("utf-8")).hexdigest()


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
