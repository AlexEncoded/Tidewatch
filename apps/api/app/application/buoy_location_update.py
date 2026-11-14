"""Application workflow for recording buoy location and refreshing movement."""

from dataclasses import dataclass

from ..domain.buoy import BuoyLocationCommand, BuoySnapshot
from ..domain.movement import MovementAnalysisSnapshot
from .movement_analysis import analyze_movement_for_buoy
from .fleet_ports import BuoyLocationUpdater, FleetMetrics, LocationTelemetryReader


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


def update_buoy_location_and_publish_movement(
    updater: BuoyLocationUpdater,
    movement_reader: LocationTelemetryReader,
    metrics: FleetMetrics,
    buoy_id: str,
    command: BuoyLocationCommand,
) -> BuoyLocationUpdateResult | None:
    """Update location, analyze movement, and publish a known speed metric."""
    result = update_buoy_location(updater, movement_reader, buoy_id, command)
    if result is None:
        return None
    if result.movement.average_speed_mps is not None:
        metrics.record_buoy_movement(buoy_id, result.movement.average_speed_mps)
    return result
