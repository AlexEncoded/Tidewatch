"""Application ports for cross-sensor data-quality summaries."""

from typing import Protocol


class QualitySummaryReader(Protocol):
    """Read quality counts without exposing sensor persistence adapters."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...

    def quality_counts(self, buoy_id: str) -> dict[str, int]:
        ...
