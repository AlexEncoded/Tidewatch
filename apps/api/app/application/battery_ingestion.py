"""Application service for battery telemetry ingestion."""

from datetime import datetime, timezone

from ..domain.devices import (
    DeviceOwnershipError,
    validate_device_ownership,
    validate_telemetry_device_channel,
)
from ..domain.battery import BatteryTelemetrySnapshot
from .battery_ports import BatteryMetrics, BatteryTelemetryReader


def record_battery_reading(
    reader: BatteryTelemetryReader,
    reading: BatteryTelemetrySnapshot,
    received_at: datetime | None = None,
) -> BatteryTelemetrySnapshot:
    """Validate an optional physical-unit link before persisting battery data."""
    device = None
    if reading.physical_device_id is not None:
        device = reader.get_device_snapshot(reading.physical_device_id)
        validate_device_ownership(device, reading.buoy_id)
        validate_telemetry_device_channel(device, (reading.device_id,), "Battery")
    saved_reading = reader.add_battery(reading)
    if device is not None:
        reader.mark_device_seen_by_id(
            device.device_id, received_at or datetime.now(timezone.utc)
        )
    return saved_reading


def ingest_battery_reading(
    reader: BatteryTelemetryReader,
    metrics: BatteryMetrics,
    reading: BatteryTelemetrySnapshot,
    received_at: datetime | None = None,
) -> BatteryTelemetrySnapshot | None:
    """Validate buoy and device ownership, persist battery, and publish metrics."""
    if not reader.buoy_exists(reading.buoy_id):
        return None

    observed_at = received_at or datetime.now(timezone.utc)
    saved_reading = record_battery_reading(reader, reading, observed_at)
    metrics.record_reading(
        reading.buoy_id,
        reading.battery_percent,
        saved_reading.physical_device_id,
        saved_reading.device_id,
        observed_at,
    )
    return saved_reading
