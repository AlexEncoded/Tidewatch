from collections.abc import Mapping
from typing import NewType

from ..shared.device import SensorChannel
from .sensor_family import SensorFamily
from .reading_quality import MeasuredReading

MissingSensorChannelLabel = NewType("MissingSensorChannelLabel", str)


def missing_sensor_channels(
    sensor_readings: Mapping[SensorFamily, Mapping[SensorChannel, MeasuredReading | None]],
) -> list[MissingSensorChannelLabel]:
    """List missing redundant channels when a sensor has partial telemetry."""
    missing: list[MissingSensorChannelLabel] = []
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
            missing.append(MissingSensorChannelLabel(f"{sensor}:B"))
        elif has_b and not has_a:
            missing.append(MissingSensorChannelLabel(f"{sensor}:A"))
    return missing
