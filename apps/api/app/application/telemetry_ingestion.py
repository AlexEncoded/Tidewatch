"""Application helpers for normalising incoming telemetry batches."""

from ..domain.telemetry import (
    AmbientLightTelemetrySnapshot,
    ConductivityTelemetrySnapshot,
    DissolvedOxygenTelemetrySnapshot,
    ImuTelemetrySnapshot,
    LocationTelemetrySnapshot,
    MarineCurrentTelemetrySnapshot,
    PHTelemetrySnapshot,
    SalinityTelemetrySnapshot,
    TurbidityTelemetrySnapshot,
    WindTelemetrySnapshot,
)
from ..domain.pressure import PressureTelemetrySnapshot
from ..domain.temperature import TemperatureTelemetrySnapshot


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


def build_temperature_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> TemperatureTelemetrySnapshot:
    """Normalize a validated temperature payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return TemperatureTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_pressure_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> PressureTelemetrySnapshot:
    """Normalize a validated pressure payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return PressureTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_salinity_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> SalinityTelemetrySnapshot:
    """Normalize a validated salinity payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return SalinityTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_imu_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> ImuTelemetrySnapshot:
    """Normalize a validated IMU payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return ImuTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_ambient_light_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> AmbientLightTelemetrySnapshot:
    """Normalize a validated ambient-light payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return AmbientLightTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_wind_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> WindTelemetrySnapshot:
    """Normalize a validated wind payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return WindTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_marine_current_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> MarineCurrentTelemetrySnapshot:
    """Normalize a validated marine-current payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return MarineCurrentTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_turbidity_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> TurbidityTelemetrySnapshot:
    """Normalize a validated turbidity payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return TurbidityTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_dissolved_oxygen_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> DissolvedOxygenTelemetrySnapshot:
    """Normalize a validated dissolved-oxygen payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return DissolvedOxygenTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_ph_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> PHTelemetrySnapshot:
    """Normalize a validated pH payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return PHTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def build_conductivity_snapshot(
    buoy_id: str,
    reading_data: dict,
    batch_device_id: str | None,
) -> ConductivityTelemetrySnapshot:
    """Normalize a validated conductivity payload into a domain snapshot."""
    normalized = with_device_provenance(reading_data, batch_device_id)
    return ConductivityTelemetrySnapshot(buoy_id=buoy_id, **normalized)


def empty_accepted_reading_counts() -> dict[str, int]:
    """Return stable zero counters for every supported telemetry family."""
    return {family: 0 for family in TELEMETRY_FAMILIES}
