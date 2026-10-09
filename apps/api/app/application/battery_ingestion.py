"""Application service for battery telemetry ingestion."""

from ..domain.devices import DeviceOwnershipError, validate_device_ownership
from ..domain.telemetry import BatteryTelemetrySnapshot
from .ports import BatteryTelemetryReader


def record_battery_reading(
    reader: BatteryTelemetryReader,
    reading: BatteryTelemetrySnapshot,
) -> BatteryTelemetrySnapshot:
    """Validate an optional physical-unit link before persisting battery data."""
    device = None
    if reading.physical_device_id is not None:
        device = reader.get_device_snapshot(reading.physical_device_id)
        validate_device_ownership(device, reading.buoy_id)
        if device.sensor_channel != reading.device_id:
            raise ValueError("Battery channel must match the physical device channel")
    saved_reading = reader.add_battery(reading)
    if device is not None:
        reader.mark_device_seen_by_id(device.device_id, reading.measured_at)
    return saved_reading
