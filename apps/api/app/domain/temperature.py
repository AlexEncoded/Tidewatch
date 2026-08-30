from dataclasses import dataclass
from statistics import fmean


@dataclass(frozen=True)
class TemperatureEstimate:
    sample_count: int
    latest_temperature: float | None = None
    average_temperature: float | None = None
    minimum_temperature: float | None = None
    maximum_temperature: float | None = None
    change_celsius: float | None = None
    trend: str = "insufficient_data"
    is_anomaly: bool = False
    anomaly_reason: str | None = None


def estimate_temperature(
    values: list[float],
    threshold: float,
) -> TemperatureEstimate:
    """Calculate trend and outlier status from newest-first temperatures."""
    if not values:
        return TemperatureEstimate(sample_count=0)

    latest = values[0]
    oldest = values[-1]
    change = round(latest - oldest, 2)
    average = fmean(values)
    is_anomaly = len(values) >= 3 and abs(latest - average) > threshold
    trend = "insufficient_data"
    if len(values) >= 2:
        if change > 0.2:
            trend = "rising"
        elif change < -0.2:
            trend = "falling"
        else:
            trend = "stable"

    return TemperatureEstimate(
        sample_count=len(values),
        latest_temperature=latest,
        average_temperature=round(average, 2),
        minimum_temperature=min(values),
        maximum_temperature=max(values),
        change_celsius=change,
        trend=trend,
        is_anomaly=is_anomaly,
        anomaly_reason=(
            f"Latest reading differs from the recent average by more than {threshold:.2f} °C"
            if is_anomaly
            else None
        ),
    )
