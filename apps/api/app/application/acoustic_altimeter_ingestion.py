"""Application use case for writing acoustic-altimeter telemetry."""

from datetime import datetime, timezone

from ..domain.acoustic_altimeter import AcousticAltimeterTelemetrySnapshot
from .acoustic_sensor_ports import AcousticAltimeterTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_acoustic_altimeter_reading(
    gateway: AcousticAltimeterTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: AcousticAltimeterTelemetrySnapshot,
    received_at: datetime | None = None,
) -> AcousticAltimeterTelemetrySnapshot | None:
    """Persist one altimeter reading and publish heartbeat and metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_acoustic_altimeter(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "acoustic_altimeter",
        reading.sensor_channel,
        reading.quality,
        {"depth_meters": reading.depth_meters},
    )
    return saved_reading
