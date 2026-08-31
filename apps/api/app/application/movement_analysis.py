"""Application service for the movement-analysis use case."""

from ..domain.movement import estimate_movement
from ..models import MovementAnalysis
from .ports import LocationTelemetryReader


MovementTelemetryReader = LocationTelemetryReader


def analyze_movement_for_buoy(
    reader: MovementTelemetryReader,
    buoy_id: str,
    window: int,
) -> MovementAnalysis:
    """Run movement analysis through a persistence port."""
    estimate = estimate_movement(reader.list_locations(buoy_id, window))
    return MovementAnalysis(
        buoy_id=buoy_id,
        sample_count=estimate.sample_count,
        distance_travelled_m=estimate.distance_travelled_m,
        displacement_m=estimate.displacement_m,
        average_speed_mps=estimate.average_speed_mps,
        confidence=estimate.confidence,
    )
