"""Application use case for writing conductivity telemetry."""

from datetime import datetime, timezone

from ..domain.conductivity import ConductivityTelemetrySnapshot
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics
from .water_quality_ports import ConductivityTelemetryGateway


def ingest_conductivity_reading(
    gateway: ConductivityTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: ConductivityTelemetrySnapshot,
    received_at: datetime | None = None,
) -> ConductivityTelemetrySnapshot | None:
    """Persist one conductivity reading and publish heartbeat and metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_conductivity(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "conductivity",
        reading.sensor_channel,
        reading.quality,
        {"conductivity_us_cm": reading.conductivity_us_cm},
    )
    return saved_reading
