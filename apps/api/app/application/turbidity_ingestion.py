"""Application use case for writing turbidity telemetry."""

from datetime import datetime, timezone

from ..domain.turbidity import TurbidityTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .water_quality_ports import TurbidityTelemetryGateway


def ingest_turbidity_reading(
    gateway: TurbidityTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: TurbidityTelemetrySnapshot,
    received_at: datetime | None = None,
) -> TurbidityTelemetrySnapshot | None:
    """Persist one turbidity reading and publish heartbeat and metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_turbidity(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "turbidity",
        reading.sensor_channel,
        reading.quality,
        {"turbidity_ntu": reading.turbidity_ntu},
    )
    return saved_reading
