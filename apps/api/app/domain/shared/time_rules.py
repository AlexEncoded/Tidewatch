"""Shared domain rules for durations and time thresholds."""

from math import isfinite


def require_positive_finite_seconds(seconds: float, label: str) -> None:
    """Reject invalid seconds thresholds before evaluating freshness."""
    if not isfinite(seconds) or seconds <= 0:
        raise ValueError(f"{label} must be a positive finite number")
