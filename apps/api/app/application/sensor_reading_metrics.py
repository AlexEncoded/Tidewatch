"""Publish readings from individual sensor endpoints through the metrics port."""

from collections.abc import Mapping

from .telemetry_ports import TelemetryMetrics


_SENSOR_METRICS: dict[str, tuple[str, dict[str, str]]] = {
    "imu": ("imu_readings_total", {}),
    "wind": (
        "wind_readings_total",
        {
            "wind_speed_mps": "current_wind_speed_mps",
            "wind_direction_degrees": "current_wind_direction_degrees",
        },
    ),
    "ambient_light": (
        "ambient_light_readings_total",
        {"illuminance_lux": "current_ambient_light_lux"},
    ),
    "temperature": (
        "temperature_readings_total",
        {"temperature_celsius": "current_temperature_celsius"},
    ),
    "pressure": (
        "pressure_readings_total",
        {"pressure_kpa": "current_pressure_kpa"},
    ),
    "salinity": (
        "salinity_readings_total",
        {"salinity_psu": "current_salinity_psu"},
    ),
    "marine_current": (
        "marine_current_readings_total",
        {
            "current_speed_mps": "current_marine_current_speed_mps",
            "current_direction_degrees": "current_marine_current_direction_degrees",
        },
    ),
    "turbidity": ("turbidity_readings_total", {"turbidity_ntu": "current_turbidity_ntu"}),
    "dissolved_oxygen": (
        "dissolved_oxygen_readings_total",
        {"dissolved_oxygen_mg_l": "current_dissolved_oxygen_mg_l"},
    ),
    "ph": ("ph_readings_total", {"ph": "current_ph"}),
    "conductivity": (
        "conductivity_readings_total",
        {"conductivity_us_cm": "current_conductivity_us_cm"},
    ),
    "chlorophyll_a": (
        "chlorophyll_a_readings_total",
        {"chlorophyll_a_ug_l": "current_chlorophyll_a_ug_l"},
    ),
    "rainfall": ("rainfall_readings_total", {"rainfall_mm_h": "current_rainfall_mm_h"}),
    "humidity": (
        "humidity_readings_total",
        {"humidity_percent": "current_humidity_percent"},
    ),
    "air_temperature": (
        "air_temperature_readings_total",
        {"air_temperature_celsius": "current_air_temperature_celsius"},
    ),
    "atmospheric_pressure": (
        "atmospheric_pressure_readings_total",
        {"atmospheric_pressure_kpa": "current_atmospheric_pressure_kpa"},
    ),
    "acoustic_altimeter": (
        "acoustic_altimeter_readings_total",
        {"depth_meters": "current_acoustic_altimeter_depth_meters"},
    ),
    "underwater_acoustic": (
        "underwater_acoustic_readings_total",
        {"echo_intensity_db": "current_underwater_acoustic_echo_intensity_db"},
    ),
}


def record_sensor_reading_metrics(
    metrics: TelemetryMetrics,
    buoy_id: str,
    sensor_family: str,
    sensor_channel: str,
    quality: str,
    values: Mapping[str, float],
) -> None:
    """Record reading volume, current values, and quality for one sensor."""
    try:
        reading_counter, value_metrics = _SENSOR_METRICS[sensor_family]
    except KeyError:
        raise ValueError(f"Unsupported sensor family: {sensor_family}") from None

    labels = {"buoy_id": buoy_id, "sensor_channel": sensor_channel}
    metrics.metric(reading_counter).labels(**labels).inc()
    for field, metric_name in value_metrics.items():
        if field in values:
            metrics.metric(metric_name).labels(**labels).set(values[field])

    if sensor_family == "imu":
        for axis in ("x", "y", "z"):
            acceleration = values.get(f"acceleration_{axis}_mps2")
            if acceleration is not None:
                metrics.metric("current_imu_acceleration_mps2").labels(
                    **labels, axis=axis
                ).set(acceleration)
            angular_velocity = values.get(f"angular_velocity_{axis}_dps")
            if angular_velocity is not None:
                metrics.metric("current_imu_angular_velocity_dps").labels(
                    **labels, axis=axis
                ).set(angular_velocity)

    metrics.metric("reading_quality_total").labels(
        buoy_id=buoy_id,
        sensor_family=sensor_family,
        sensor_channel=sensor_channel,
        quality=quality,
    ).inc()
