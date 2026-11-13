"""Application use case for writing marine-current telemetry."""

from datetime import datetime, timezone

from ..domain.marine_current import MarineCurrentTelemetrySnapshot
from .flow_ports import MarineCurrentTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_marine_current_reading(
    gateway: MarineCurrentTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: MarineCurrentTelemetrySnapshot,
    received_at: datetime | None = None,
) -> MarineCurrentTelemetrySnapshot | None:
    """Persist one current reading and publish heartbeat and vector metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_marine_current(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "marine_current",
        reading.sensor_channel,
        reading.quality,
        {
            "current_speed_mps": reading.current_speed_mps,
            "current_direction_degrees": reading.current_direction_degrees,
        },
    )
    return saved_reading
