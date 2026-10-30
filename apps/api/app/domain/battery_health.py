from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite

from .telemetry_types import BATTERY_MAX_PERCENT, BATTERY_MIN_PERCENT


@dataclass(frozen=True)
class BatteryHealthSnapshot:
    buoy_id: str
    status: str
    device_a_percent: float | None
    device_b_percent: float | None
    checked_at: datetime
    delta_percent: float | None = None
    degraded_devices: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BatteryHealthEstimate:
    status: str
    device_a_percent: float | None
    device_b_percent: float | None
    delta_percent: float | None = None
    degraded_devices: list[str] | None = None


def estimate_battery_health(
    device_a_percent: float | None,
    device_b_percent: float | None,
    threshold: float,
) -> BatteryHealthEstimate:
    """Evaluate redundant battery percentages without persistence dependencies."""
    if not isfinite(threshold) or threshold < 0:
        raise ValueError("Battery health threshold must be a non-negative finite number")
    for label, percentage in (
        ("Device A", device_a_percent),
        ("Device B", device_b_percent),
    ):
        if percentage is not None and (
            not isfinite(percentage)
            or not BATTERY_MIN_PERCENT <= percentage <= BATTERY_MAX_PERCENT
        ):
            raise ValueError(
                f"{label} battery percentage must be between "
                f"{BATTERY_MIN_PERCENT} and {BATTERY_MAX_PERCENT}"
            )

    if device_a_percent is None or device_b_percent is None:
        return BatteryHealthEstimate(
            status="insufficient_data",
            device_a_percent=device_a_percent,
            device_b_percent=device_b_percent,
        )

    delta = round(abs(device_a_percent - device_b_percent), 2)
    degraded_devices = []
    if delta > threshold:
        degraded_devices = [
            "A" if device_a_percent < device_b_percent else "B"
        ]

    return BatteryHealthEstimate(
        status="degraded" if degraded_devices else "consistent",
        device_a_percent=device_a_percent,
        device_b_percent=device_b_percent,
        delta_percent=delta,
        degraded_devices=degraded_devices,
    )
