from collections.abc import Mapping


SENSOR_DEGRADATION_THRESHOLDS = {
    "temperature": 0.5,
    "pressure": 0.25,
    "salinity": 0.2,
    "imu": 0.5,
    "ambient_light": 5000,
    "wind_speed": 0.5,
    "wind_direction": 15,
    "marine_current_speed": 0.25,
    "marine_current_direction": 15,
    "turbidity": 10,
    "dissolved_oxygen": 1,
    "ph": 0.2,
    "conductivity": 2000,
    "chlorophyll_a": 5,
    "rainfall": 20,
    "humidity": 5,
    "air_temperature": 0.5,
    "atmospheric_pressure": 0.25,
    "acoustic_altimeter": 0.5,
    "underwater_acoustic": 5,
}


def degraded_sensor_names(deltas: Mapping[str, float | None]) -> list[str]:
    """Return degraded sensors and aggregate wind/current families."""
    degraded = [
        sensor
        for sensor, value in deltas.items()
        if value is not None and value > SENSOR_DEGRADATION_THRESHOLDS[sensor]
    ]
    if "wind_speed" in degraded or "wind_direction" in degraded:
        degraded.append("wind")
    if "marine_current_speed" in degraded or "marine_current_direction" in degraded:
        degraded.append("marine_current")
    return degraded
