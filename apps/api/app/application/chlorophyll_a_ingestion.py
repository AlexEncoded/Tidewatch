"""Application use case for writing chlorophyll-a telemetry."""

from datetime import datetime, timezone

from ..domain.chlorophyll_a import ChlorophyllATelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .water_quality_ports import ChlorophyllATelemetryGateway


def ingest_chlorophyll_a_reading(
    gateway: ChlorophyllATelemetryGateway,
    metrics: TelemetryMetrics,
    reading: ChlorophyllATelemetrySnapshot,
    received_at: datetime | None = None,
) -> ChlorophyllATelemetrySnapshot | None:
    """Persist one chlorophyll-a reading and publish its metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_chlorophyll_a(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "chlorophyll_a",
        reading.sensor_channel,
        reading.quality,
        {"chlorophyll_a_ug_l": reading.chlorophyll_a_ug_l},
    )
    return saved_reading
