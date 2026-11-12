"""Application use case for writing salinity telemetry."""

from datetime import datetime, timezone

from ..domain.salinity import SalinityTelemetrySnapshot
from .marine_water_ports import SalinityTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_salinity_reading(
    gateway: SalinityTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: SalinityTelemetrySnapshot,
    received_at: datetime | None = None,
) -> SalinityTelemetrySnapshot | None:
    """Persist one salinity reading and publish heartbeat and metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_salinity(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "salinity",
        reading.sensor_channel,
        reading.quality,
        {"salinity_psu": reading.salinity_psu},
    )
    return saved_reading
