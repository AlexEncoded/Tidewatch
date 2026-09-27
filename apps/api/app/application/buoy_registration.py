"""Application use case for registering a buoy."""

from datetime import datetime, timezone
from uuid import uuid4

from ..domain.buoy import BuoyRegistrationCommand, BuoySnapshot
from .ports import BuoyRegistrar


def register_buoy(
    registrar: BuoyRegistrar,
    command: BuoyRegistrationCommand,
) -> BuoySnapshot:
    """Assign the buoy identifier and timestamp, then persist it via the port."""
    buoy = BuoySnapshot(
        buoy_id=f"TW-{uuid4().hex[:8].upper()}",
        name=command.name,
        latitude=command.latitude,
        longitude=command.longitude,
        status="active",
        last_seen_at=None,
        created_at=datetime.now(timezone.utc),
    )
    return registrar.register_buoy(buoy)
