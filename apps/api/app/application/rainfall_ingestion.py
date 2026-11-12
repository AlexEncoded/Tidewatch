"""Application use case for writing rainfall telemetry."""

from datetime import datetime, timezone

from ..domain.rainfall import RainfallTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .weather_ports import RainfallTelemetryGateway


def ingest_rainfall_reading(
    gateway: RainfallTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: RainfallTelemetrySnapshot,
    received_at: datetime | None = None,
) -> RainfallTelemetrySnapshot | None:
    """Persist one rainfall reading and publish heartbeat and metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_rainfall(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "rainfall",
        reading.sensor_channel,
        reading.quality,
        {"rainfall_mm_h": reading.rainfall_mm_h},
    )
    return saved_reading
