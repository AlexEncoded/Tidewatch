def sensor_health_status(
    has_available_reading: bool,
    has_degraded_sensor: bool,
    has_missing_channel: bool,
) -> str:
    """Return the aggregate health status for redundant sensor telemetry."""
    if not has_available_reading:
        return "degraded" if has_missing_channel else "insufficient_data"
    if has_degraded_sensor or has_missing_channel:
        return "degraded"
    return "consistent"
