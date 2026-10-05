"""Shared value types used by telemetry domain objects and API schemas."""

from typing import Literal

SensorChannel = Literal["A", "B"]
ReadingQuality = Literal["good", "suspect", "invalid"]
