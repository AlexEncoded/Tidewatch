from datetime import datetime, timezone

from prometheus_client import generate_latest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.availability_metrics import initialize_availability_metrics
from app.database import Base
from app.entities import BuoyEntity, DeviceEntity


def test_initialize_availability_metrics_includes_unseen_registered_entities() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    buoy_id = "availability-seed-test"
    device_id = "availability-seed-device"
    with Session(engine) as session:
        session.add(
            BuoyEntity(
                id=buoy_id,
                name="Seed test",
                status="active",
                last_seen_at=None,
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        session.flush()
        session.add(
            DeviceEntity(
                device_id=device_id,
                buoy_id=buoy_id,
                sensor_channel="A",
                status="active",
                registered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                last_seen_at=None,
            )
        )
        session.commit()

        initialize_availability_metrics(session)

    metrics = generate_latest().decode("utf-8")
    assert (
        f'tidewatch_buoy_last_seen_timestamp_seconds{{buoy_id="{buoy_id}"}} 0.0'
        in metrics
    )
    assert (
        'tidewatch_device_last_seen_timestamp_seconds'
        f'{{buoy_id="{buoy_id}",device_id="{device_id}",sensor_channel="A"}} 0.0'
    ) in metrics
    engine.dispose()
