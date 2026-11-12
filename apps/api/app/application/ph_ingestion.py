"""Application use case for writing pH telemetry."""

from datetime import datetime, timezone

from ..domain.ph import PHTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .water_quality_ports import PHTelemetryGateway


def ingest_ph_reading(
    gateway: PHTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: PHTelemetrySnapshot,
    received_at: datetime | None = None,
) -> PHTelemetrySnapshot | None:
    """Persist one pH reading and publish heartbeat and sensor metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_ph(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "ph",
        reading.sensor_channel,
        reading.quality,
        {"ph": reading.ph},
    )
    return saved_reading
