"""Domain snapshot for the operational health of a physical device."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .time_rules import require_positive_finite_seconds


@dataclass(frozen=True)
class DeviceHealthSnapshot:
    buoy_id: str
    device_id: str
    sensor_channel: Literal["A", "B"]
    status: Literal["active", "maintenance", "inactive"]
    is_stale: bool
    last_seen_at: datetime | None = None
    age_seconds: float | None = None


@dataclass(frozen=True)
class DeviceLivenessAssessment:
    """Domain result for a device heartbeat freshness check."""

    last_seen_at: datetime | None
    age_seconds: float | None
    is_stale: bool


def assess_device_liveness(
    status: str,
    last_seen_at: datetime | None,
    now: datetime,
    max_age_seconds: float,
) -> DeviceLivenessAssessment:
    """Evaluate heartbeat freshness; only active devices can be stale."""
    require_positive_finite_seconds(max_age_seconds, "Maximum heartbeat age")
    reference = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
    normalized_last_seen = None
    age_seconds = None
    if last_seen_at is not None:
        normalized_last_seen = (
            last_seen_at.replace(tzinfo=timezone.utc)
            if last_seen_at.tzinfo is None
            else last_seen_at
        )
        age_seconds = max(0.0, (reference - normalized_last_seen).total_seconds())

    return DeviceLivenessAssessment(
        last_seen_at=normalized_last_seen,
        age_seconds=round(age_seconds, 2) if age_seconds is not None else None,
        is_stale=(
            status == "active"
            and (age_seconds is None or age_seconds > max_age_seconds)
        ),
    )
