"""Application use case for changing a buoy's operational status."""

from ..domain.buoy import BuoySnapshot, BuoyStatusCommand
from .ports import BuoyStatusRegistry


def update_buoy_status(
    registry: BuoyStatusRegistry,
    buoy_id: str,
    command: BuoyStatusCommand,
) -> BuoySnapshot | None:
    """Update the buoy status, returning ``None`` when it does not exist."""
    return registry.update_buoy_status(buoy_id, command)
