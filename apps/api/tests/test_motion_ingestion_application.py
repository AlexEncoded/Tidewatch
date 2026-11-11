from datetime import datetime, timezone

from app.application.motion_ingestion import ingest_imu_reading
from app.domain.imu import ImuTelemetrySnapshot


class FakeMetrics:
    def __init__(self) -> None:
        self.events = []
        self.metric_name = None
        self.labels_value = None

    def metric(self, name: str):
        self.metric_name = name
        return self

    def labels(self, **labels):
        self.labels_value = labels
        return self

    def inc(self, amount: float = 1) -> None:
        self.events.append((self.metric_name, self.labels_value, "inc", amount))

    def set(self, value: float) -> None:
        self.events.append((self.metric_name, self.labels_value, "set", value))


class FakeGateway:
    def __init__(self, exists: bool = True) -> None:
        self.exists = exists
        self.events = []

    def buoy_exists(self, buoy_id: str) -> bool:
        self.events.append(("exists", buoy_id))
        return self.exists

    def add_imu(self, reading: ImuTelemetrySnapshot):
        self.events.append(("add", reading))
        return reading


def test_imu_ingestion_persists_and_publishes_all_axis_metrics() -> None:
    received_at = datetime(2026, 11, 11, 0, 1, tzinfo=timezone.utc)
    reading = ImuTelemetrySnapshot(
        buoy_id="buoy-1",
        acceleration_x_mps2=1.0,
        acceleration_y_mps2=2.0,
        acceleration_z_mps2=9.81,
        angular_velocity_x_dps=0.1,
        angular_velocity_y_dps=0.2,
        angular_velocity_z_dps=0.3,
        measured_at=received_at,
    )
    gateway = FakeGateway()
    metrics = FakeMetrics()

    saved = ingest_imu_reading(gateway, metrics, reading, received_at)

    assert saved is reading
    assert gateway.events == [("exists", "buoy-1"), ("add", reading)]
    axis_events = [
        event
        for event in metrics.events
        if event[0]
        in {"current_imu_acceleration_mps2", "current_imu_angular_velocity_dps"}
    ]
    assert len(axis_events) == 6
    assert {event[1]["axis"] for event in axis_events} == {"x", "y", "z"}
    assert any(
        name == "imu_readings_total" and operation == "inc"
        for name, _, operation, _ in metrics.events
    )


def test_imu_ingestion_skips_persistence_and_metrics_for_unknown_buoy() -> None:
    reading = ImuTelemetrySnapshot(
        buoy_id="missing",
        acceleration_x_mps2=1.0,
        acceleration_y_mps2=2.0,
        acceleration_z_mps2=9.81,
        angular_velocity_x_dps=0.1,
        angular_velocity_y_dps=0.2,
        angular_velocity_z_dps=0.3,
        measured_at=datetime(2026, 11, 11, tzinfo=timezone.utc),
    )
    gateway = FakeGateway(exists=False)
    metrics = FakeMetrics()

    assert ingest_imu_reading(gateway, metrics, reading) is None
    assert gateway.events == [("exists", "missing")]
    assert metrics.events == []
