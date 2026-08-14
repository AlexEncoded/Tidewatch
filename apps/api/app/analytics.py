from statistics import fmean

from .models import (
    PressureAnalysis,
    PressureReading,
    TemperatureAnalysis,
    TemperatureReading,
)


KPA_TO_METRES_OF_WATER = 0.102


def analyze_temperatures(
    buoy_id: str,
    readings: list[TemperatureReading],
    threshold: float,
) -> TemperatureAnalysis:
    if not readings:
        return TemperatureAnalysis(buoy_id=buoy_id, sample_count=0)

    values = [reading.temperature_celsius for reading in readings]
    latest = readings[0].temperature_celsius
    oldest = readings[-1].temperature_celsius
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

    return TemperatureAnalysis(
        buoy_id=buoy_id,
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


def analyze_pressure(
    buoy_id: str,
    readings: list[PressureReading],
) -> PressureAnalysis:
    """Estimate wave height from pressure variation.

    This is deliberately an educational approximation: 1 kPa is treated as
    roughly 0.102 metres of water column. A production model would account for
    sensor depth, tide, filtering and the buoy's calibration curve.
    """
    if not readings:
        return PressureAnalysis(buoy_id=buoy_id, sample_count=0)

    values = [reading.pressure_kpa for reading in readings]
    minimum = min(values)
    maximum = max(values)
    pressure_range = maximum - minimum
    has_enough_samples = len(values) >= 3

    return PressureAnalysis(
        buoy_id=buoy_id,
        sample_count=len(values),
        latest_pressure_kpa=round(readings[0].pressure_kpa, 3),
        average_pressure_kpa=round(fmean(values), 3),
        minimum_pressure_kpa=round(minimum, 3),
        maximum_pressure_kpa=round(maximum, 3),
        pressure_range_kpa=round(pressure_range, 3),
        estimated_wave_height_m=(
            round(pressure_range * KPA_TO_METRES_OF_WATER, 3)
            if has_enough_samples
            else None
        ),
        confidence="experimental" if has_enough_samples else "insufficient_data",
    )
