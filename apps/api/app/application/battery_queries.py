"""Application queries for buoy-scoped battery telemetry."""

from ..domain.devices import validate_device_ownership
from ..domain.battery import BatteryTelemetrySnapshot
from .battery_ports import BatteryTelemetryReader


class BatteryBuoyNotFound(LookupError):
    """Raised when a battery query targets a missing buoy."""


def _validate_query_target(
    reader: BatteryTelemetryReader,
    buoy_id: str,
    physical_device_id: str | None,
) -> None:
    if not reader.buoy_exists(buoy_id):
        raise BatteryBuoyNotFound(buoy_id)
    if physical_device_id is not None:
        device = reader.get_device_snapshot(physical_device_id)
        validate_device_ownership(device, buoy_id)


def get_latest_battery(
    reader: BatteryTelemetryReader,
    buoy_id: str,
    device_id: str | None,
    physical_device_id: str | None,
) -> BatteryTelemetrySnapshot | None:
    """Load the latest battery reading after validating its buoy and device."""
    _validate_query_target(reader, buoy_id, physical_device_id)
    return reader.latest_battery(buoy_id, device_id, physical_device_id)


def list_battery_history(
    reader: BatteryTelemetryReader,
    buoy_id: str,
    limit: int,
    device_id: str | None,
    physical_device_id: str | None,
) -> list[BatteryTelemetrySnapshot]:
    """Load battery history after validating its buoy and device."""
    _validate_query_target(reader, buoy_id, physical_device_id)
    return reader.list_batteries(buoy_id, limit, device_id, physical_device_id)
