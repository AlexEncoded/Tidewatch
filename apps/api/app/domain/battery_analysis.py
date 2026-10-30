from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from .telemetry_types import BATTERY_MAX_PERCENT, BATTERY_MIN_PERCENT


@dataclass(frozen=True)
class BatterySample:
    battery_percent: float
    measured_at: datetime

    def __post_init__(self) -> None:
        if (
            not isfinite(self.battery_percent)
            or not BATTERY_MIN_PERCENT <= self.battery_percent <= BATTERY_MAX_PERCENT
        ):
            raise ValueError(
                f"Battery percentage must be between {BATTERY_MIN_PERCENT} "
                f"and {BATTERY_MAX_PERCENT}"
            )
        if self.measured_at.tzinfo is None:
            object.__setattr__(
                self, "measured_at", self.measured_at.replace(tzinfo=timezone.utc)
            )


@dataclass(frozen=True)
class BatteryDischargeEstimate:
    sample_count: int
    latest_percent: float | None = None
    oldest_percent: float | None = None
    change_percent: float | None = None
    discharge_rate_percent_per_hour: float | None = None
    estimated_hours_remaining: float | None = None
    confidence: str = "insufficient_data"


@dataclass(frozen=True)
class BatteryAnalysisSnapshot:
    """Domain result exposed by the historical battery use case."""

    buoy_id: str
    device_id: str
    sample_count: int
    latest_percent: float | None = None
    oldest_percent: float | None = None
    change_percent: float | None = None
    discharge_rate_percent_per_hour: float | None = None
    estimated_hours_remaining: float | None = None
    confidence: str = "insufficient_data"


def estimate_battery_discharge(
    readings: Sequence[BatterySample],
) -> BatteryDischargeEstimate:
    """Estimate discharge from battery samples, regardless of input order."""
    if not readings:
        return BatteryDischargeEstimate(sample_count=0)

    ordered = sorted(readings, key=lambda reading: reading.measured_at, reverse=True)
    latest = ordered[0]
    oldest = ordered[-1]
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
