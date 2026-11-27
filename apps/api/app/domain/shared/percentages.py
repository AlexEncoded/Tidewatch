"""Validation for finite physical values expressed as percentages."""

from math import isfinite


def validate_percentage(value: float, label: str = "Percentage") -> None:
    """Reject values outside the finite inclusive range from zero to one hundred."""
    if not isfinite(value) or not 0 <= value <= 100:
        raise ValueError(f"{label} must be between 0 and 100")
