"""Domain calculations for comparing redundant sensor channels."""

from collections.abc import Mapping

from .deltas import absolute_difference
from .directions import circular_difference_degrees
from .vectors import euclidean_difference


def calculate_sensor_health_deltas(
    readings: Mapping[str, Mapping[str, list[object]]],
) -> dict[str, float | None]:
    """Calculate A/B sensor deltas from the latest usable channel readings."""

    def value(family: str, channel: str, attribute: str):
        channel_readings = readings[family][channel]
        return getattr(channel_readings[0], attribute) if channel_readings else None

    def scalar(family: str, attribute: str, digits: int) -> float | None:
        left = value(family, "A", attribute)
        right = value(family, "B", attribute)
        return (
            round(absolute_difference(left, right), digits)
            if left is not None and right is not None
            else None
        )

    def circular(family: str, attribute: str, digits: int) -> float | None:
        left = value(family, "A", attribute)
        right = value(family, "B", attribute)
        return (
            round(circular_difference_degrees(left, right), digits)
            if left is not None and right is not None
            else None
        )

    imu_a = readings["imu"]["A"]
    imu_b = readings["imu"]["B"]
    imu_delta = (
        round(
            euclidean_difference(
                [
                    getattr(imu_a[0], f"acceleration_{axis}_mps2")
                    for axis in ("x", "y", "z")
                ],
                [
                    getattr(imu_b[0], f"acceleration_{axis}_mps2")
                    for axis in ("x", "y", "z")
                ],
            ),
            3,
        )
        if imu_a and imu_b
        else None
    )
    return {
        "temperature": scalar("temperature", "temperature_celsius", 3),
        "pressure": scalar("pressure", "pressure_kpa", 3),
        "salinity": scalar("salinity", "salinity_psu", 3),
        "imu": imu_delta,
        "ambient_light": scalar("ambient_light", "illuminance_lux", 2),
        "wind_speed": scalar("wind", "wind_speed_mps", 3),
        "wind_direction": circular("wind", "wind_direction_degrees", 2),
        "marine_current_speed": scalar("marine_current", "current_speed_mps", 3),
        "marine_current_direction": circular(
            "marine_current", "current_direction_degrees", 2
        ),
        "turbidity": scalar("turbidity", "turbidity_ntu", 3),
        "dissolved_oxygen": scalar("dissolved_oxygen", "dissolved_oxygen_mg_l", 3),
        "ph": scalar("ph", "ph", 3),
        "conductivity": scalar("conductivity", "conductivity_us_cm", 2),
        "chlorophyll_a": scalar("chlorophyll_a", "chlorophyll_a_ug_l", 3),
        "rainfall": scalar("rainfall", "rainfall_mm_h", 2),
        "humidity": scalar("humidity", "humidity_percent", 2),
        "air_temperature": scalar("air_temperature", "air_temperature_celsius", 2),
        "atmospheric_pressure": scalar("atmospheric_pressure", "atmospheric_pressure_kpa", 3),
        "acoustic_altimeter": scalar("acoustic_altimeter", "depth_meters", 3),
        "underwater_acoustic": scalar("underwater_acoustic", "echo_intensity_db", 2),
    }
