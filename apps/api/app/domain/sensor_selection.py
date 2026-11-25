"""Selection rules for displaying redundant sensor readings."""

from typing import TypeVar

from .fleet.devices import SensorChannel
from .reading_quality import ReadingQuality

ReadingT = TypeVar("ReadingT")

_QUALITY_PRIORITY = {"good": 0, "suspect": 1, "invalid": 2}


def preferred_sensor_channel(
    quality_a: ReadingQuality = "good",
    quality_b: ReadingQuality = "good",
) -> SensorChannel:
    """Return the higher-quality channel, preferring A when quality ties."""
    return (
        "B"
        if _QUALITY_PRIORITY[quality_b] < _QUALITY_PRIORITY[quality_a]
        else "A"
    )


def select_summary_reading(
    channel_a: ReadingT | None,
    channel_b: ReadingT | None,
) -> ReadingT | None:
    """Prefer better-quality channels; unclassified readings count as good."""
    if channel_a is None:
        return channel_b
    if channel_b is None:
        return channel_a
    selected = preferred_sensor_channel(
        getattr(channel_a, "quality", "good"),
        getattr(channel_b, "quality", "good"),
    )
    if selected == "B":
        return channel_b
    return channel_a
