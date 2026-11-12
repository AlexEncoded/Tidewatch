"""Application use case for writing humidity telemetry."""

from datetime import datetime, timezone

from ..domain.humidity import HumidityTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .weather_ports import HumidityTelemetryGateway


def ingest_humidity_reading(
    gateway: HumidityTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: HumidityTelemetrySnapshot,
    received_at: datetime | None = None,
) -> HumidityTelemetrySnapshot | None:
    """Persist one humidity reading and publish heartbeat and metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_humidity(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "humidity",
        reading.sensor_channel,
        reading.quality,
        {"humidity_percent": reading.humidity_percent},
    )
    return saved_reading
