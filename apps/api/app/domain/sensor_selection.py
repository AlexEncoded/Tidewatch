"""Selection rules for displaying redundant sensor readings."""

from typing import TypeVar

ReadingT = TypeVar("ReadingT")

_QUALITY_PRIORITY = {"good": 0, "suspect": 1, "invalid": 2}


def select_summary_reading(
    channel_a: ReadingT | None,
    channel_b: ReadingT | None,
) -> ReadingT | None:
    """Prefer better-quality channels; unclassified readings count as good."""
    if channel_a is None:
        return channel_b
    if channel_b is None:
        return channel_a
    quality_a = getattr(channel_a, "quality", "good")
    quality_b = getattr(channel_b, "quality", "good")
    if _QUALITY_PRIORITY[quality_b] < _QUALITY_PRIORITY[quality_a]:
        return channel_b
    return channel_a
