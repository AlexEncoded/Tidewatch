from dataclasses import dataclass
from datetime import timezone
from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_M = 6_371_000


@dataclass(frozen=True)
class MovementEstimate:
    sample_count: int
    distance_travelled_m: float | None = None
    displacement_m: float | None = None
    average_speed_mps: float | None = None
    confidence: str = "insufficient_data"


def distance_between_points(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return the great-circle distance between two coordinates in metres."""
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude_a))
        * cos(radians(latitude_b))
        * sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * asin(sqrt(haversine))


def estimate_movement(locations: list) -> MovementEstimate:
    """Estimate travelled distance and speed from chronological location samples."""
    if len(locations) < 2:
        return MovementEstimate(sample_count=len(locations))

    chronological = list(reversed(locations))
    distance = sum(
        distance_between_points(
            previous.latitude,
            previous.longitude,
            current.latitude,
            current.longitude,
        )
        for previous, current in zip(chronological, chronological[1:])
    )
    displacement = distance_between_points(
        chronological[0].latitude,
        chronological[0].longitude,
        chronological[-1].latitude,
        chronological[-1].longitude,
    )
    start_time = chronological[0].measured_at
    end_time = chronological[-1].measured_at
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    elapsed_seconds = (end_time - start_time).total_seconds()

    return MovementEstimate(
        sample_count=len(locations),
        distance_travelled_m=round(distance, 2),
        displacement_m=round(displacement, 2),
        average_speed_mps=(round(distance / elapsed_seconds, 3) if elapsed_seconds > 0 else None),
        confidence="experimental",
    )
