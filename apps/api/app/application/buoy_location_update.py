"""Application workflow for recording buoy location and refreshing movement."""

from dataclasses import dataclass

from ..domain.buoy import BuoyLocationCommand, BuoySnapshot
from ..domain.movement import MovementAnalysisSnapshot
from .movement_analysis import analyze_movement_for_buoy
from .ports import BuoyLocationUpdater, LocationTelemetryReader


@dataclass(frozen=True)
class BuoyLocationUpdateResult:
    buoy: BuoySnapshot
    movement: MovementAnalysisSnapshot


def update_buoy_location(
    updater: BuoyLocationUpdater,
    movement_reader: LocationTelemetryReader,
    buoy_id: str,
    command: BuoyLocationCommand,
) -> BuoyLocationUpdateResult | None:
    """Persist new coordinates and calculate recent movement for the buoy."""
    buoy = updater.update_buoy_location(buoy_id, command)
    if buoy is None:
        return None
    movement = analyze_movement_for_buoy(movement_reader, buoy_id, 50)
    return BuoyLocationUpdateResult(buoy=buoy, movement=movement)
