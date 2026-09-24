"""Mapping helpers for physical-device application results."""

from ..domain.devices import DeviceSnapshot


def to_device_snapshot(device: object) -> DeviceSnapshot:
    """Map a persistence result to the domain device snapshot."""
    return DeviceSnapshot(
        buoy_id=device.buoy_id,
        device_id=device.device_id,
        sensor_channel=device.sensor_channel,
        firmware_version=device.firmware_version,
        status=device.status,
        registered_at=device.registered_at,
        last_seen_at=device.last_seen_at,
    )
