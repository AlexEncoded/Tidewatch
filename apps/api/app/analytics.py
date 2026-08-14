from statistics import fmean

from .models import TemperatureAnalysis, TemperatureReading


def analyze_temperatures(
    buoy_id: str,
    readings: list[TemperatureReading],
    threshold: float,
) -> TemperatureAnalysis:
    if not readings:
        return TemperatureAnalysis(buoy_id=buoy_id, sample_count=0)

    values = [reading.temperature_celsius for reading in readings]
    latest = readings[0].temperature_celsius
    average = fmean(values)
    is_anomaly = len(values) >= 3 and abs(latest - average) > threshold

    return TemperatureAnalysis(
        buoy_id=buoy_id,
        sample_count=len(values),
        latest_temperature=latest,
        average_temperature=round(average, 2),
        minimum_temperature=min(values),
        maximum_temperature=max(values),
        is_anomaly=is_anomaly,
        anomaly_reason=(
            f"Latest reading differs from the recent average by more than {threshold:.2f} °C"
            if is_anomaly
            else None
        ),
    )
