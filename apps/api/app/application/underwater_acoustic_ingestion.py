"""Application use case for writing underwater-acoustic telemetry."""

from datetime import datetime, timezone

from ..domain.underwater_acoustic import UnderwaterAcousticTelemetrySnapshot
from .acoustic_sensor_ports import UnderwaterAcousticTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_underwater_acoustic_reading(
    gateway: UnderwaterAcousticTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: UnderwaterAcousticTelemetrySnapshot,
    received_at: datetime | None = None,
) -> UnderwaterAcousticTelemetrySnapshot | None:
    """Persist one underwater-echo reading and publish heartbeat and metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_underwater_acoustic(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "underwater_acoustic",
        reading.sensor_channel,
        reading.quality,
        {"echo_intensity_db": reading.echo_intensity_db},
    )
    return saved_reading
