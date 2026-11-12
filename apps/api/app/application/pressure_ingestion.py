"""Application use case for writing water-pressure telemetry."""

from datetime import datetime, timezone

from ..domain.pressure import PressureTelemetrySnapshot
from .marine_water_ports import PressureTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_pressure_reading(
    gateway: PressureTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: PressureTelemetrySnapshot,
    received_at: datetime | None = None,
) -> PressureTelemetrySnapshot | None:
    """Persist one pressure reading and publish heartbeat and sensor metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_pressure(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "pressure",
        reading.sensor_channel,
        reading.quality,
        {"pressure_kpa": reading.pressure_kpa},
    )
    return saved_reading
