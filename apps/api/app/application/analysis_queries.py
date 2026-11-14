"""Application queries shared by buoy-scoped analysis use cases."""

from collections.abc import Callable
from typing import Protocol, TypeVar


class BuoyAnalysisReader(Protocol):
    """Port for confirming that an analysis target exists."""

    def buoy_exists(self, buoy_id: str) -> bool:
        ...


AnalysisT = TypeVar("AnalysisT")


def analyze_if_buoy_exists(
    reader: BuoyAnalysisReader,
    buoy_id: str,
    analyze: Callable[[], AnalysisT],
) -> AnalysisT | None:
    """Run a buoy-scoped analysis only when its buoy exists."""
    if not reader.buoy_exists(buoy_id):
        return None
    return analyze()
