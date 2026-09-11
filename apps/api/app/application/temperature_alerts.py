"""Application mappings for persisted temperature alerts."""

from ..models import StoredTemperatureAlert


def to_stored_temperature_alert(alert) -> StoredTemperatureAlert:
    """Map a persisted alert entity to the API contract."""
    return StoredTemperatureAlert(
        id=alert.id,
        buoy_id=alert.buoy_id,
        buoy_name=alert.buoy.name,
        severity=alert.severity,
        temperature_celsius=alert.temperature_celsius,
        average_temperature=alert.average_temperature,
        created_at=alert.created_at,
        message=alert.message,
        status=alert.status,
        resolved_at=alert.resolved_at,
    )
