"""Application mappings for persisted temperature alerts."""

from ..domain.temperature_alert import TemperatureAlertSnapshot


def to_stored_temperature_alert(alert) -> TemperatureAlertSnapshot:
    """Map a persisted alert entity to an application snapshot."""
    return TemperatureAlertSnapshot(
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
