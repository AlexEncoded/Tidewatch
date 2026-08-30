from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BatterySample:
    battery_percent: float
    measured_at: datetime


@dataclass(frozen=True)
class BatteryDischargeEstimate:
    sample_count: int
    latest_percent: float | None = None
    oldest_percent: float | None = None
    change_percent: float | None = None
    discharge_rate_percent_per_hour: float | None = None
    estimated_hours_remaining: float | None = None
    confidence: str = "insufficient_data"


def estimate_battery_discharge(
    readings: list[BatterySample],
) -> BatteryDischargeEstimate:
    """Estimate discharge rate from newest-first battery samples."""
    if not readings:
        return BatteryDischargeEstimate(sample_count=0)

    latest = readings[0]
    oldest = readings[-1]
    change = round(latest.battery_percent - oldest.battery_percent, 2)
    elapsed_hours = (latest.measured_at - oldest.measured_at).total_seconds() / 3600
    discharge_rate = None
    estimated_hours = None
    if len(readings) >= 2 and elapsed_hours > 0:
        discharge_rate = round(max(0, -change) / elapsed_hours, 3)
        if discharge_rate > 0:
            estimated_hours = round(latest.battery_percent / discharge_rate, 2)

    return BatteryDischargeEstimate(
        sample_count=len(readings),
        latest_percent=latest.battery_percent,
        oldest_percent=oldest.battery_percent,
        change_percent=change,
        discharge_rate_percent_per_hour=discharge_rate,
        estimated_hours_remaining=estimated_hours,
        confidence=(
            "experimental"
            if len(readings) >= 2 and discharge_rate is not None
            else "insufficient_data"
        ),
    )
