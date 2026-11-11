"""Application use case for writing ambient-light telemetry."""

from datetime import datetime, timezone

from ..domain.ambient_light import AmbientLightTelemetrySnapshot
from .ambient_light_ports import AmbientLightTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_ambient_light_reading(
    gateway: AmbientLightTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: AmbientLightTelemetrySnapshot,
    received_at: datetime | None = None,
) -> AmbientLightTelemetrySnapshot | None:
    """Persist one reading and publish heartbeat and sensor metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_ambient_light(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "ambient_light",
        reading.sensor_channel,
        reading.quality,
        {"illuminance_lux": reading.illuminance_lux},
    )
    return saved_reading
