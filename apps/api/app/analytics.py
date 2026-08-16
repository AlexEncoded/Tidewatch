from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
from statistics import fmean

from .models import (
    PressureAnalysis,
    PressureReading,
    TemperatureAnalysis,
    TemperatureReading,
    MovementAnalysis,
    BatteryHealth,
    BatteryReading,
    BatteryAnalysis,
)


KPA_TO_METRES_OF_WATER = 0.102
EARTH_RADIUS_M = 6_371_000


def distance_between_points(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return the great-circle distance between two coordinates in metres."""
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude_a))
        * cos(radians(latitude_b))
        * sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * asin(sqrt(haversine))


def analyze_movement(buoy_id: str, locations: list) -> MovementAnalysis:
    if len(locations) < 2:
        return MovementAnalysis(buoy_id=buoy_id, sample_count=len(locations))

    chronological = list(reversed(locations))
    distance = sum(
        distance_between_points(
            previous.latitude,
            previous.longitude,
            current.latitude,
            current.longitude,
        )
        for previous, current in zip(chronological, chronological[1:])
    )
    displacement = distance_between_points(
        chronological[0].latitude,
        chronological[0].longitude,
        chronological[-1].latitude,
        chronological[-1].longitude,
    )
    elapsed_seconds = (
        chronological[-1].measured_at - chronological[0].measured_at
    ).total_seconds()

    return MovementAnalysis(
        buoy_id=buoy_id,
        sample_count=len(locations),
        distance_travelled_m=round(distance, 2),
        displacement_m=round(displacement, 2),
        average_speed_mps=(round(distance / elapsed_seconds, 3) if elapsed_seconds > 0 else None),
        confidence="experimental",
    )


def analyze_battery_health(
    buoy_id: str,
    readings: dict[str, BatteryReading | None],
    threshold: float,
) -> BatteryHealth:
    device_a = readings.get("A")
    device_b = readings.get("B")
    if device_a is None or device_b is None:
        return BatteryHealth(
            buoy_id=buoy_id,
            status="insufficient_data",
            device_a_percent=device_a.battery_percent if device_a else None,
            device_b_percent=device_b.battery_percent if device_b else None,
            checked_at=datetime.now(timezone.utc),
        )

    delta = round(abs(device_a.battery_percent - device_b.battery_percent), 2)
    degraded_devices = []
    if delta > threshold:
        degraded_devices = [
            "A" if device_a.battery_percent < device_b.battery_percent else "B"
        ]

    return BatteryHealth(
        buoy_id=buoy_id,
        status="degraded" if degraded_devices else "consistent",
        device_a_percent=device_a.battery_percent,
        device_b_percent=device_b.battery_percent,
        delta_percent=delta,
        degraded_devices=degraded_devices,
        checked_at=datetime.now(timezone.utc),
    )


def analyze_battery(
    buoy_id: str, device_id: str, readings: list[BatteryReading]
) -> BatteryAnalysis:
    if not readings:
        return BatteryAnalysis(buoy_id=buoy_id, device_id=device_id, sample_count=0)

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

    return BatteryAnalysis(
        buoy_id=buoy_id,
        device_id=device_id,
        sample_count=len(readings),
        latest_percent=latest.battery_percent,
        oldest_percent=oldest.battery_percent,
        change_percent=change,
        discharge_rate_percent_per_hour=discharge_rate,
        estimated_hours_remaining=estimated_hours,
        confidence="experimental" if len(readings) >= 2 and discharge_rate is not None else "insufficient_data",
    )


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

    return PressureAnalysis(
        buoy_id=buoy_id,
        sample_count=len(values),
        latest_pressure_kpa=round(readings[0].pressure_kpa, 3),
        average_pressure_kpa=round(fmean(values), 3),
        minimum_pressure_kpa=round(minimum, 3),
        maximum_pressure_kpa=round(maximum, 3),
        pressure_range_kpa=round(pressure_range, 3),
        estimated_wave_height_m=(
            round(estimated_wave_height, 3) if estimated_wave_height is not None else None
        ),
        confidence="experimental" if has_enough_samples else "insufficient_data",
        sea_state=sea_state,
    )
