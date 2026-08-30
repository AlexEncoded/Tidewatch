from datetime import datetime, timezone
from statistics import fmean

from .models import (
    PressureAnalysis,
    PressureReading,
    TemperatureAnalysis,
    TemperatureReading,
    MovementAnalysis,
    WaveAnalysis,
    BatteryHealth,
    BatteryReading,
    BatteryAnalysis,
)
from .domain.wave import DEFAULT_IMU_WAVE_HEIGHT_FACTOR, estimate_wave
from .domain.movement import distance_between_points, estimate_movement
from .domain.battery_health import estimate_battery_health


KPA_TO_METRES_OF_WATER = 0.102


def analyze_movement(buoy_id: str, locations: list) -> MovementAnalysis:
    estimate = estimate_movement(locations)
    return MovementAnalysis(
        buoy_id=buoy_id,
        sample_count=estimate.sample_count,
        distance_travelled_m=estimate.distance_travelled_m,
        displacement_m=estimate.displacement_m,
        average_speed_mps=estimate.average_speed_mps,
        confidence=estimate.confidence,
    )


def analyze_battery_health(
    buoy_id: str,
    readings: dict[str, BatteryReading | None],
    threshold: float,
) -> BatteryHealth:
    device_a = readings.get("A")
    device_b = readings.get("B")
    estimate = estimate_battery_health(
        device_a.battery_percent if device_a else None,
        device_b.battery_percent if device_b else None,
        threshold,
    )

    return BatteryHealth(
        buoy_id=buoy_id,
        status=estimate.status,
        device_a_percent=estimate.device_a_percent,
        device_b_percent=estimate.device_b_percent,
        delta_percent=estimate.delta_percent,
        degraded_devices=estimate.degraded_devices or [],
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


def analyze_wave(
    buoy_id: str,
    imu_readings: list,
    locations: list,
    imu_wave_height_factor: float = DEFAULT_IMU_WAVE_HEIGHT_FACTOR,
) -> WaveAnalysis:
    """Combine GNSS altitude and IMU vertical motion into an experimental estimate.

    The IMU contribution uses a deliberately conservative synthetic calibration
    factor; real deployments must replace it with a buoy-specific transfer model.
    """
    altitude_values = [
        reading.altitude_meters
        for reading in locations
        if reading.altitude_meters is not None
    ]
    acceleration_values = [reading.acceleration_z_mps2 for reading in imu_readings]
    estimate = estimate_wave(
        altitude_values,
        acceleration_values,
        imu_wave_height_factor=imu_wave_height_factor,
    )
    if estimate.estimated_wave_height_m is None:
        return WaveAnalysis(buoy_id=buoy_id, sample_count=max(len(imu_readings), len(locations)))
    return WaveAnalysis(
        buoy_id=buoy_id,
        sample_count=max(len(imu_readings), len(locations)),
        gnss_vertical_range_m=(
            round(estimate.gnss_vertical_range_m, 3)
            if estimate.gnss_vertical_range_m is not None
            else None
        ),
        imu_vertical_acceleration_range_mps2=(
            round(estimate.imu_vertical_acceleration_range_mps2, 3)
            if estimate.imu_vertical_acceleration_range_mps2 is not None
            else None
        ),
        estimated_wave_height_m=round(estimate.estimated_wave_height_m, 3),
        confidence=estimate.confidence,
    )
