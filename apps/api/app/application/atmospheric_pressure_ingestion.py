"""Application use case for writing atmospheric-pressure telemetry."""

from datetime import datetime, timezone

from ..domain.atmospheric_pressure import AtmosphericPressureTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .weather_ports import AtmosphericPressureTelemetryGateway


def ingest_atmospheric_pressure_reading(
    gateway: AtmosphericPressureTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: AtmosphericPressureTelemetrySnapshot,
    received_at: datetime | None = None,
) -> AtmosphericPressureTelemetrySnapshot | None:
    """Persist one atmospheric-pressure reading and publish its metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_atmospheric_pressure(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "atmospheric_pressure",
        reading.sensor_channel,
        reading.quality,
        {"atmospheric_pressure_kpa": reading.atmospheric_pressure_kpa},
    )
    return saved_reading
