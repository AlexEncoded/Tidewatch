"""Application use case for registering a buoy."""

from datetime import datetime, timezone
from uuid import uuid4

from ..domain.fleet.buoy import BuoyRegistrationCommand, BuoySnapshot
from .fleet_ports import BuoyRegistrar, FleetMetrics


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


def register_buoy_and_publish_heartbeat(
    registrar: BuoyRegistrar,
    metrics: FleetMetrics,
    command: BuoyRegistrationCommand,
) -> BuoySnapshot:
    """Register a buoy and publish its initial heartbeat through the port."""
    buoy = register_buoy(registrar, command)
    metrics.record_buoy_heartbeat(buoy.buoy_id, buoy.last_seen_at)
    return buoy
