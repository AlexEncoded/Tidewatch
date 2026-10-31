from datetime import datetime, timezone
from dataclasses import dataclass
from math import isfinite
from typing import Literal

from .telemetry_types import validate_battery_percentage
from .time_rules import require_positive_finite_seconds


BatterySeverity = Literal["warning", "critical"]


@dataclass(frozen=True)
class MaintenanceIssueSnapshot:
    """Domain representation of a maintenance issue."""

    buoy_id: str
    buoy_name: str
    issue_type: str
    severity: str
    message: str


def missing_redundant_battery_device(
    device_a_percent: float | None,
    device_b_percent: float | None,
) -> Literal["A", "B"] | None:
    """Return the missing redundant unit when exactly one unit has telemetry."""
    if device_a_percent is not None:
        validate_battery_percentage(device_a_percent, "Device A battery percentage")
    if device_b_percent is not None:
        validate_battery_percentage(device_b_percent, "Device B battery percentage")
    if device_a_percent is not None and device_b_percent is None:
        return "B"
    if device_b_percent is not None and device_a_percent is None:
        return "A"
    return None


def is_buoy_drifting(average_speed_mps: float | None, limit_mps: float) -> bool:
    """Return whether observed movement exceeds the configured drift limit."""
    require_positive_finite_seconds(limit_mps, "Drift speed limit")
    if average_speed_mps is not None and (
        not isfinite(average_speed_mps) or average_speed_mps < 0
    ):
        raise ValueError("Average speed must be a non-negative finite number")
    return average_speed_mps is not None and average_speed_mps > limit_mps


def low_battery_severity(battery_percent: float) -> BatterySeverity | None:
    """Return the maintenance severity for a battery reading, if it is low."""
    validate_battery_percentage(battery_percent)
    if battery_percent < 10:
        return "critical"
    if battery_percent < 20:
        return "warning"
    return None


def is_buoy_silent(
    status: str,
    last_seen_at: datetime | None,
    now: datetime,
    max_age_seconds: float,
) -> bool:
    """Return whether an active buoy has exceeded its telemetry age limit."""
    require_positive_finite_seconds(max_age_seconds, "Maximum buoy age")
    if status != "active" or last_seen_at is None:
        return False
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - last_seen_at).total_seconds() > max_age_seconds
