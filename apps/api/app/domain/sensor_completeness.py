from collections.abc import Mapping


def missing_sensor_channels(
    sensor_readings: Mapping[str, Mapping[str, object | None]],
) -> list[str]:
    """List missing redundant channels when a sensor has partial telemetry."""
    return [
        f"{sensor}:{channel}"
        for sensor, channels in sensor_readings.items()
        if any(channels.values())
        for channel, reading in channels.items()
        if not reading
    ]
