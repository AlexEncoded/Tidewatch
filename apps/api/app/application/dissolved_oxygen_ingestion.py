"""Application use case for writing dissolved-oxygen telemetry."""

from datetime import datetime, timezone

from ..domain.dissolved_oxygen import DissolvedOxygenTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .water_quality_ports import DissolvedOxygenTelemetryGateway


def ingest_dissolved_oxygen_reading(
    gateway: DissolvedOxygenTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: DissolvedOxygenTelemetrySnapshot,
    received_at: datetime | None = None,
) -> DissolvedOxygenTelemetrySnapshot | None:
    """Persist an oxygen reading and publish heartbeat and sensor metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_dissolved_oxygen(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "dissolved_oxygen",
        reading.sensor_channel,
        reading.quality,
        {"dissolved_oxygen_mg_l": reading.dissolved_oxygen_mg_l},
    )
    return saved_reading
