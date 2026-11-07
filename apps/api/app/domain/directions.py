"""Shared domain rules for angular directions."""

DIRECTION_MIN_DEGREES = 0
DIRECTION_MAX_DEGREES = 360


def circular_difference_degrees(first: float, second: float) -> float:
    """Return the smallest absolute angular difference in degrees."""
    difference = abs(first - second) % 360
    return min(difference, 360 - difference)
