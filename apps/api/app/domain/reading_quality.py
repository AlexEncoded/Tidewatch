from collections.abc import Mapping, Sequence


def classify_latest_readings(
    readings_by_sensor: Mapping[str, Sequence[object]],
) -> tuple[list[str], list[str]]:
    """Return sensor names with invalid and suspect latest readings."""
    invalid_sensors = []
    suspect_sensors = []
    for sensor, readings in readings_by_sensor.items():
        if not readings:
            continue
        quality = getattr(readings[0], "quality", None)
        if quality == "invalid":
            invalid_sensors.append(sensor)
        elif quality == "suspect":
            suspect_sensors.append(sensor)
    return invalid_sensors, suspect_sensors
