from dataclasses import dataclass
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
    degraded_devices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        degraded_devices = tuple(self.degraded_devices)
        object.__setattr__(self, "degraded_devices", degraded_devices)
        if self.status not in {"insufficient_data", "consistent", "degraded"}:
            raise ValueError(f"Unsupported battery health status {self.status!r}")
        for label, percentage in (
            ("Device A", self.device_a_percent),
            ("Device B", self.device_b_percent),
        ):
            _validate_battery_percentage(label, percentage)

        has_both_readings = (
            self.device_a_percent is not None and self.device_b_percent is not None
        )
        if self.status == "insufficient_data":
            if has_both_readings or self.delta_percent is not None or degraded_devices:
                raise ValueError("Insufficient battery data cannot include a delta or degraded devices")
            return
        if not has_both_readings:
            raise ValueError("Battery health status requires readings from both devices")

        expected_delta = round(
            abs(self.device_a_percent - self.device_b_percent), 2
        )
        if self.delta_percent != expected_delta:
            raise ValueError("Battery health delta must match the device percentages")
        if any(device not in {"A", "B"} for device in degraded_devices):
            raise ValueError("Degraded battery devices must be A or B")
        if (self.status == "degraded") != bool(degraded_devices):
            raise ValueError("Battery health status must match degraded devices")
        if self.status == "degraded":
            lower_battery_device = (
                "A"
                if self.device_a_percent < self.device_b_percent
                else "B"
            )
            if degraded_devices != (lower_battery_device,):
                raise ValueError("The degraded device must have the lower battery percentage")


@dataclass(frozen=True)
class BatteryHealthEstimate:
    status: str
    device_a_percent: float | None
    device_b_percent: float | None
    delta_percent: float | None = None
    degraded_devices: tuple[str, ...] = ()


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
        _validate_battery_percentage(label, percentage)

    if device_a_percent is None or device_b_percent is None:
        return BatteryHealthEstimate(
            status="insufficient_data",
            device_a_percent=device_a_percent,
            device_b_percent=device_b_percent,
        )

    delta = round(abs(device_a_percent - device_b_percent), 2)
    degraded_devices: tuple[str, ...] = ()
    if delta > threshold:
        degraded_devices = ("A" if device_a_percent < device_b_percent else "B",)

    return BatteryHealthEstimate(
        status="degraded" if degraded_devices else "consistent",
        device_a_percent=device_a_percent,
        device_b_percent=device_b_percent,
        delta_percent=delta,
        degraded_devices=degraded_devices,
    )


def _validate_battery_percentage(label: str, percentage: float | None) -> None:
    if percentage is not None and (
        not isfinite(percentage)
        or not BATTERY_MIN_PERCENT <= percentage <= BATTERY_MAX_PERCENT
    ):
        raise ValueError(
            f"{label} battery percentage must be between "
            f"{BATTERY_MIN_PERCENT} and {BATTERY_MAX_PERCENT}"
        )
