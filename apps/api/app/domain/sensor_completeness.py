from collections.abc import Mapping


def missing_sensor_channels(
    sensor_readings: Mapping[str, Mapping[str, object | None]],
) -> list[str]:
    """List missing redundant channels when a sensor has partial telemetry."""
    missing: list[str] = []
    for sensor, channels in sensor_readings.items():
        unknown_channels = set(channels).difference({"A", "B"})
        if unknown_channels:
            raise ValueError(
                f"Unsupported sensor channels for {sensor}: "
                f"{', '.join(sorted(unknown_channels))}"
            )
        has_a = bool(channels.get("A"))
        has_b = bool(channels.get("B"))
        if has_a and not has_b:
            missing.append(f"{sensor}:B")
        elif has_b and not has_a:
            missing.append(f"{sensor}:A")
    return missing
