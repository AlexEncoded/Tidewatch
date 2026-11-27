"""Shared quality labels for measured domain readings."""

from typing import Literal, get_args

ReadingQuality = Literal["good", "suspect", "invalid"]
VALID_READING_QUALITIES = frozenset(get_args(ReadingQuality))
