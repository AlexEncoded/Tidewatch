"""Application use case for writing inertial-motion telemetry."""

from datetime import datetime, timezone

from ..domain.imu import ImuTelemetrySnapshot
from .motion_ports import ImuTelemetryGateway
from .sensor_reading_metrics import record_sensor_reading_metrics
from .telemetry_ports import TelemetryMetrics


def ingest_imu_reading(
    gateway: ImuTelemetryGateway,
    metrics: TelemetryMetrics,
    reading: ImuTelemetrySnapshot,
    received_at: datetime | None = None,
) -> ImuTelemetrySnapshot | None:
    """Persist one IMU snapshot and publish heartbeat and vector metrics."""
    if not gateway.buoy_exists(reading.buoy_id):
        return None

    saved_reading = gateway.add_imu(reading)
    metrics.metric("buoy_last_seen_timestamp_seconds").labels(
        buoy_id=reading.buoy_id
    ).set((received_at or datetime.now(timezone.utc)).timestamp())
    record_sensor_reading_metrics(
        metrics,
        reading.buoy_id,
        "imu",
        reading.sensor_channel,
        reading.quality,
        {
            "acceleration_x_mps2": reading.acceleration_x_mps2,
            "acceleration_y_mps2": reading.acceleration_y_mps2,
            "acceleration_z_mps2": reading.acceleration_z_mps2,
            "angular_velocity_x_dps": reading.angular_velocity_x_dps,
            "angular_velocity_y_dps": reading.angular_velocity_y_dps,
            "angular_velocity_z_dps": reading.angular_velocity_z_dps,
        },
    )
    return saved_reading
