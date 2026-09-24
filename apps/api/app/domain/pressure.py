from dataclasses import dataclass
from datetime import datetime
from statistics import fmean


KPA_TO_METRES_OF_WATER = 0.102


@dataclass(frozen=True)
class PressureTelemetrySnapshot:
    """Domain representation of one water-pressure sample."""

    buoy_id: str
    pressure_kpa: float
    measured_at: datetime
    sensor_channel: str = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: str = "good"


@dataclass(frozen=True)
class PressureEstimate:
    sample_count: int
    latest_pressure_kpa: float | None = None
    average_pressure_kpa: float | None = None
    minimum_pressure_kpa: float | None = None
    maximum_pressure_kpa: float | None = None
    pressure_range_kpa: float | None = None
    estimated_wave_height_m: float | None = None
    confidence: str = "insufficient_data"
    sea_state: str = "unknown"


@dataclass(frozen=True)
class PressureAnalysisSnapshot:
    buoy_id: str
    sample_count: int
    latest_pressure_kpa: float | None = None
    average_pressure_kpa: float | None = None
    minimum_pressure_kpa: float | None = None
    maximum_pressure_kpa: float | None = None
    pressure_range_kpa: float | None = None
    estimated_wave_height_m: float | None = None
    confidence: str = "insufficient_data"
    sea_state: str = "unknown"


def estimate_pressure(values: list[float]) -> PressureEstimate:
    """Estimate pressure variation and an educational wave-height proxy."""
    if not values:
        return PressureEstimate(sample_count=0)

    minimum = min(values)
    maximum = max(values)
    pressure_range = maximum - minimum
    has_enough_samples = len(values) >= 3
    estimated_wave_height = (
        pressure_range * KPA_TO_METRES_OF_WATER if has_enough_samples else None
    )
    sea_state = "unknown"
    if estimated_wave_height is not None:
        if estimated_wave_height < 0.3:
            sea_state = "calm"
        elif estimated_wave_height < 1.0:
            sea_state = "moderate"
        else:
            sea_state = "rough"

    return PressureEstimate(
        sample_count=len(values),
        latest_pressure_kpa=round(values[0], 3),
        average_pressure_kpa=round(fmean(values), 3),
        minimum_pressure_kpa=round(minimum, 3),
        maximum_pressure_kpa=round(maximum, 3),
        pressure_range_kpa=round(pressure_range, 3),
        estimated_wave_height_m=(
            round(estimated_wave_height, 3)
            if estimated_wave_height is not None
            else None
        ),
        confidence="experimental" if has_enough_samples else "insufficient_data",
        sea_state=sea_state,
    )
