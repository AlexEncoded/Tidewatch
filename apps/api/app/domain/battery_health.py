from dataclasses import dataclass


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
