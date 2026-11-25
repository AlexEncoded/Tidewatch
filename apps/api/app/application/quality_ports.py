"""Application ports for cross-sensor data-quality summaries."""

from collections.abc import Mapping
from typing import Protocol

from ..domain.sensors.reading_quality import ReadingQuality


class QualitySummaryReader(Protocol):
    """Read quality counts without exposing sensor persistence adapters."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def quality_counts(self, buoy_id: str) -> Mapping[ReadingQuality, int]:
        ...
