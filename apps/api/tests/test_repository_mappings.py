from datetime import datetime, timezone
from types import SimpleNamespace

from app.domain.buoy import BuoySnapshot
from app.domain.devices import DeviceSnapshot
from app.persistence_mappers import buoy_snapshot, device_snapshot, sensor_health_check_snapshot


def test_buoy_entity_mapper_returns_domain_snapshot_without_losing_fields() -> None:
    created_at = datetime(2026, 10, 5, tzinfo=timezone.utc)
    last_seen_at = datetime(2026, 10, 4, tzinfo=timezone.utc)
    entity = SimpleNamespace(
        id="TW-123",
        name="North buoy",
        latitude=36.7,
        longitude=3.1,
        status="maintenance",
        last_seen_at=last_seen_at,
        created_at=created_at,
    )

    snapshot = buoy_snapshot(entity)

    assert snapshot == BuoySnapshot(
        buoy_id="TW-123",
        name="North buoy",
        latitude=36.7,
        longitude=3.1,
        status="maintenance",
        last_seen_at=last_seen_at,
        created_at=created_at,
    )


def test_device_entity_mapper_preserves_operational_state() -> None:
    registered_at = datetime(2026, 10, 5, tzinfo=timezone.utc)
    last_seen_at = datetime(2026, 10, 6, tzinfo=timezone.utc)
    entity = SimpleNamespace(
        buoy_id="TW-123",
        device_id="device-A",
        sensor_channel="A",
        registered_at=registered_at,
        firmware_version="1.2.3",
        status="maintenance",
        last_seen_at=last_seen_at,
    )

    snapshot = device_snapshot(entity)

    assert snapshot == DeviceSnapshot(
        buoy_id="TW-123",
        device_id="device-A",
        sensor_channel="A",
        registered_at=registered_at,
        firmware_version="1.2.3",
        status="maintenance",
        last_seen_at=last_seen_at,
    )


def test_sensor_health_entity_mapper_preserves_per_sensor_decisions() -> None:
    checked_at = datetime(2026, 10, 5, tzinfo=timezone.utc)
    fields = (
        "temperature_delta_celsius pressure_delta_kpa salinity_delta_psu "
        "imu_acceleration_delta_mps2 ambient_light_delta_lux wind_speed_delta_mps "
        "wind_direction_delta_degrees marine_current_speed_delta_mps "
        "marine_current_direction_delta_degrees turbidity_delta_ntu "
        "dissolved_oxygen_delta_mg_l ph_delta conductivity_delta_us_cm "
        "chlorophyll_a_delta_ug_l rainfall_delta_mm_h humidity_delta_percent "
        "air_temperature_delta_celsius atmospheric_pressure_delta_kpa "
        "acoustic_altimeter_delta_meters underwater_acoustic_delta_db"
    ).split()
    entity = SimpleNamespace(
        id=7,
        buoy_id="TW-123",
        status="degraded",
        checked_at=checked_at,
        degraded_sensors=["temperature"],
        missing_sensors=["pressure:B"],
        decisions={"temperature": "fallback_a"},
        **{field: None for field in fields},
    )

    snapshot = sensor_health_check_snapshot(entity)

    assert snapshot.id == 7
    assert snapshot.buoy_id == "TW-123"
    assert snapshot.checked_at == checked_at
    assert snapshot.degraded_sensors == ["temperature"]
    assert snapshot.missing_sensors == ["pressure:B"]
    assert snapshot.decisions == {"temperature": "fallback_a"}
