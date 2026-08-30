from datetime import datetime, timezone

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
from .domain.battery_analysis import BatterySample, estimate_battery_discharge
from .domain.temperature import estimate_temperature
from .domain.pressure import estimate_pressure


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
    estimate = estimate_battery_discharge(
        [
            BatterySample(
                battery_percent=reading.battery_percent,
                measured_at=reading.measured_at,
            )
            for reading in readings
        ]
    )

    return BatteryAnalysis(
        buoy_id=buoy_id,
        device_id=device_id,
        sample_count=estimate.sample_count,
        latest_percent=estimate.latest_percent,
        oldest_percent=estimate.oldest_percent,
        change_percent=estimate.change_percent,
        discharge_rate_percent_per_hour=estimate.discharge_rate_percent_per_hour,
        estimated_hours_remaining=estimate.estimated_hours_remaining,
        confidence=estimate.confidence,
    )


def analyze_temperatures(
    buoy_id: str,
    readings: list[TemperatureReading],
    threshold: float,
) -> TemperatureAnalysis:
    values = [reading.temperature_celsius for reading in readings]
    estimate = estimate_temperature(values, threshold)

    return TemperatureAnalysis(
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


def analyze_pressure(
    buoy_id: str,
    readings: list[PressureReading],
) -> PressureAnalysis:
    """Estimate wave height from pressure variation.

    This is deliberately an educational approximation: 1 kPa is treated as
    roughly 0.102 metres of water column. A production model would account for
    sensor depth, tide, filtering and the buoy's calibration curve.
    """
    values = [reading.pressure_kpa for reading in readings]
    estimate = estimate_pressure(values)

    return PressureAnalysis(
        buoy_id=buoy_id,
        sample_count=estimate.sample_count,
        latest_pressure_kpa=estimate.latest_pressure_kpa,
        average_pressure_kpa=estimate.average_pressure_kpa,
        minimum_pressure_kpa=estimate.minimum_pressure_kpa,
        maximum_pressure_kpa=estimate.maximum_pressure_kpa,
        pressure_range_kpa=estimate.pressure_range_kpa,
        estimated_wave_height_m=estimate.estimated_wave_height_m,
        confidence=estimate.confidence,
        sea_state=estimate.sea_state,
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
