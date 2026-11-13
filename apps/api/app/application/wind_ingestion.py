"""Application use case for writing wind telemetry."""

from datetime import datetime, timezone

from ..domain.wind import WindTelemetrySnapshot
from .flow_ports import WindTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_wind_reading(
    gateway: WindTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: WindTelemetrySnapshot,
    received_at: datetime | None = None,
) -> WindTelemetrySnapshot | None:
    """Persist one wind reading and publish heartbeat and sensor metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_wind(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "wind",
        reading.sensor_channel,
        reading.quality,
        {
            "wind_speed_mps": reading.wind_speed_mps,
            "wind_direction_degrees": reading.wind_direction_degrees,
        },
    )
    return saved_reading
