"""Application helpers for normalising incoming telemetry batches."""

from ..domain.telemetry import LocationTelemetrySnapshot


TELEMETRY_FAMILIES = (
    "temperature",
    "pressure",
    "salinity",
    "imu",
    "ambient_light",
    "wind",
    "marine_current",
    "turbidity",
    "dissolved_oxygen",
    "ph",
    "conductivity",
    "chlorophyll_a",
    "rainfall",
    "humidity",
    "air_temperature",
    "atmospheric_pressure",
    "acoustic_altimeter",
    "underwater_acoustic",
    "battery",
)


def with_device_provenance(
    reading_data: dict,
    batch_device_id: str | None,
) -> dict:
    """Return a copy with the batch device when no owner is explicit."""
    normalized = dict(reading_data)
    if batch_device_id is not None and normalized.get("device_id") is None:
        normalized["device_id"] = batch_device_id
    return normalized


def build_location_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> LocationTelemetrySnapshot:
    """Normalize a validated location payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return LocationTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def empty_accepted_reading_counts() -> dict[str, int]:
    """Return stable zero counters for every supported telemetry family."""
    return {family: 0 for family in TELEMETRY_FAMILIES}
