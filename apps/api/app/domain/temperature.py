from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from statistics import fmean

from .telemetry import SensorTelemetrySnapshot
from .telemetry_types import ReadingQuality, SensorChannel

SEA_TEMPERATURE_MIN_CELSIUS = -5
SEA_TEMPERATURE_MAX_CELSIUS = 45


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


@dataclass(frozen=True)
class TemperatureTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one measured water temperature."""

    buoy_id: str
    temperature_celsius: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not SEA_TEMPERATURE_MIN_CELSIUS <= self.temperature_celsius <= SEA_TEMPERATURE_MAX_CELSIUS:
            raise ValueError(
                "Sea temperature must be between "
                f"{SEA_TEMPERATURE_MIN_CELSIUS} and {SEA_TEMPERATURE_MAX_CELSIUS} °C"
            )


@dataclass(frozen=True)
class TemperatureAnalysisSnapshot:
    """Domain result exposed by the historical temperature use case."""

    buoy_id: str
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
    if not isfinite(threshold) or threshold <= 0:
        raise ValueError("Temperature anomaly threshold must be a positive finite number")
    for value in values:
        if (
            not isfinite(value)
            or not SEA_TEMPERATURE_MIN_CELSIUS
            <= value
            <= SEA_TEMPERATURE_MAX_CELSIUS
        ):
            raise ValueError(
                "Sea temperature must be between "
                f"{SEA_TEMPERATURE_MIN_CELSIUS} and "
                f"{SEA_TEMPERATURE_MAX_CELSIUS} °C"
            )
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


def valid_temperature_readings(
    readings: Sequence[TemperatureTelemetrySnapshot],
) -> list[TemperatureTelemetrySnapshot]:
    """Exclude invalid-quality readings while retaining good and suspect data."""
    return [reading for reading in readings if reading.quality != "invalid"]


def analyze_temperature_samples(
    buoy_id: str,
    readings: Sequence[TemperatureTelemetrySnapshot],
    threshold: float,
) -> TemperatureAnalysisSnapshot:
    """Filter invalid samples and build the public domain analysis snapshot."""
    usable_readings = valid_temperature_readings(readings)
    estimate = estimate_temperature(
        [reading.temperature_celsius for reading in usable_readings], threshold
    )
    return TemperatureAnalysisSnapshot(
        buoy_id=buoy_id,
        sample_count=estimate.sample_count,
        latest_temperature=estimate.latest_temperature,
        average_temperature=estimate.average_temperature,
        minimum_temperature=estimate.minimum_temperature,
        maximum_temperature=estimate.maximum_temperature,
        change_celsius=estimate.change_celsius,
        trend=estimate.trend,
        is_anomaly=estimate.is_anomaly,
        anomaly_reason=estimate.anomaly_reason,
    )
