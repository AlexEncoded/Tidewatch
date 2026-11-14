"""Application services for maintenance notifications."""

from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from typing import Protocol, Sequence, runtime_checkable

from ..domain.maintenance import MaintenanceIssueSnapshot
from ..domain.maintenance_notification_job import MaintenanceNotificationJob
from .maintenance_evaluation import evaluate_maintenance_issues
from .maintenance_ports import MaintenanceMetrics, MaintenanceReader
from .maintenance_notification_ports import MaintenanceNotificationJobStore


def _serialize_issue(issue: MaintenanceIssueSnapshot) -> dict:
    return asdict(issue)


@runtime_checkable
class MaintenanceNotificationTransport(Protocol):
    """Port used to deliver a maintenance notification payload."""

    def __call__(self, url: str, *, json: dict, timeout: float):
        ...


def build_maintenance_notification_payload(
    issues: Sequence[MaintenanceIssueSnapshot],
) -> dict:
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


def enqueue_maintenance_notification(
    jobs: MaintenanceNotificationJobStore,
    issues: Sequence[MaintenanceIssueSnapshot],
    requested_at: datetime,
    requested_key: str | None = None,
) -> MaintenanceNotificationJob:
    """Build and persist an idempotent notification job from domain issues."""
    payload = build_maintenance_notification_payload(list(issues))
    key = maintenance_notification_idempotency_key(
        payload, requested_key, requested_at
    )
    payload["notification_idempotency_key"] = key
    return jobs.enqueue(key, payload, len(issues), requested_at)


def evaluate_and_enqueue_maintenance_notification(
    reader: MaintenanceReader,
    metrics: MaintenanceMetrics,
    jobs: MaintenanceNotificationJobStore,
    evaluated_at: datetime,
    requested_at: datetime,
    max_age_minutes: float,
    drift_speed_mps: float,
    requested_key: str | None = None,
) -> MaintenanceNotificationJob:
    """Evaluate the fleet and enqueue its issues as one application use case."""
    issues = evaluate_maintenance_issues(
        reader, metrics, evaluated_at, max_age_minutes, drift_speed_mps
    )
    return enqueue_maintenance_notification(jobs, issues, requested_at, requested_key)


def deliver_maintenance_notification(
    webhook_url: str,
    issues: Sequence[MaintenanceIssueSnapshot],
    transport: MaintenanceNotificationTransport,
) -> int:
    """Deliver maintenance issues through the injected notification port."""
    transport(
        webhook_url,
        json=build_maintenance_notification_payload(issues),
        timeout=5,
    ).raise_for_status()
    return len(issues)
