from datetime import datetime, timezone
from pathlib import Path

from app.application.telemetry_ingestion import (
    TELEMETRY_FAMILIES,
    build_location_snapshot,
    build_imu_snapshot,
    build_ambient_light_snapshot,
    build_wind_snapshot,
    build_pressure_snapshot,
    build_salinity_snapshot,
    build_temperature_snapshot,
    empty_accepted_reading_counts,
    with_device_provenance,
)


def test_batch_device_is_used_when_reading_has_no_owner() -> None:
    reading = {"device_id": None}
    assert with_device_provenance(reading, "unit-a") == {
        "device_id": "unit-a"
    }
    assert reading == {"device_id": None}


def test_explicit_reading_owner_is_preserved() -> None:
    assert with_device_provenance({"device_id": "unit-b"}, "unit-a") == {
        "device_id": "unit-b"
    }


def test_location_payload_maps_to_domain_snapshot_with_batch_provenance() -> None:
    snapshot = build_location_snapshot(
        "buoy-1",
        {
            "latitude": 10.0,
            "longitude": 20.0,
            "altitude_meters": 3.5,
            "speed_mps": 0.4,
            "hdop": 0.8,
            "satellites": 12,
            "device_id": None,
            "measured_at": datetime(2026, 9, 24, tzinfo=timezone.utc),
        },
        "unit-a",
    )

    assert snapshot.buoy_id == "buoy-1"
    assert snapshot.altitude_meters == 3.5
    assert snapshot.device_id == "unit-a"
    assert snapshot.measured_at == datetime(2026, 9, 24, tzinfo=timezone.utc)


def test_temperature_payload_maps_to_domain_snapshot_with_batch_provenance() -> None:
    measured_at = datetime(2026, 9, 24, tzinfo=timezone.utc)
    snapshot = build_temperature_snapshot(
        "buoy-1",
        {
            "temperature_celsius": 18.25,
            "sensor_channel": "B",
            "device_id": None,
            "sensor_id": "temp-2",
            "firmware_version": "1.2.3",
            "quality": "good",
            "measured_at": measured_at,
        },
        "unit-b",
    )

    assert snapshot.buoy_id == "buoy-1"
    assert snapshot.temperature_celsius == 18.25
    assert snapshot.sensor_channel == "B"
    assert snapshot.device_id == "unit-b"
    assert snapshot.measured_at == measured_at


def test_pressure_payload_maps_to_domain_snapshot_with_batch_provenance() -> None:
    measured_at = datetime(2026, 9, 24, tzinfo=timezone.utc)
    snapshot = build_pressure_snapshot(
        "buoy-1",
        {
            "pressure_kpa": 101.4,
            "sensor_channel": "A",
            "device_id": None,
            "sensor_id": "pressure-a",
            "firmware_version": "2.0",
            "quality": "suspect",
            "measured_at": measured_at,
        },
        "unit-a",
    )

    assert snapshot.pressure_kpa == 101.4
    assert snapshot.sensor_id == "pressure-a"
    assert snapshot.device_id == "unit-a"
    assert snapshot.quality == "suspect"
    assert snapshot.measured_at == measured_at


def test_salinity_payload_maps_to_domain_snapshot_with_batch_provenance() -> None:
    measured_at = datetime(2026, 9, 24, tzinfo=timezone.utc)
    snapshot = build_salinity_snapshot(
        "buoy-1",
        {
            "salinity_psu": 34.7,
            "sensor_channel": "B",
            "device_id": None,
            "sensor_id": "salinity-b",
            "firmware_version": "2.1",
            "quality": "good",
            "measured_at": measured_at,
        },
        "unit-b",
    )

    assert snapshot.salinity_psu == 34.7
    assert snapshot.sensor_channel == "B"
    assert snapshot.device_id == "unit-b"
    assert snapshot.measured_at == measured_at


def test_imu_payload_maps_to_domain_snapshot_with_batch_provenance() -> None:
    measured_at = datetime(2026, 9, 24, tzinfo=timezone.utc)
    fields = {
        "acceleration_x_mps2": 0.1,
        "acceleration_y_mps2": -0.2,
        "acceleration_z_mps2": 9.81,
        "angular_velocity_x_dps": 1.0,
        "angular_velocity_y_dps": 2.0,
        "angular_velocity_z_dps": 3.0,
        "sensor_channel": "A",
        "device_id": None,
        "sensor_id": "imu-a",
        "firmware_version": "3.0",
        "quality": "good",
        "measured_at": measured_at,
    }

    snapshot = build_imu_snapshot("buoy-1", fields, "unit-a")

    assert snapshot.acceleration_z_mps2 == 9.81
    assert snapshot.angular_velocity_y_dps == 2.0
    assert snapshot.device_id == "unit-a"
    assert snapshot.measured_at == measured_at


def test_ambient_light_payload_maps_to_domain_snapshot_with_batch_provenance() -> None:
    measured_at = datetime(2026, 9, 24, tzinfo=timezone.utc)
    snapshot = build_ambient_light_snapshot(
        "buoy-1",
        {
            "illuminance_lux": 1200.0,
            "sensor_channel": "B",
            "device_id": None,
            "sensor_id": "light-b",
            "firmware_version": "1.1",
            "quality": "good",
            "measured_at": measured_at,
        },
        "unit-b",
    )

    assert snapshot.illuminance_lux == 1200.0
    assert snapshot.device_id == "unit-b"
    assert snapshot.sensor_channel == "B"
    assert snapshot.measured_at == measured_at


def test_wind_payload_maps_to_domain_snapshot_with_batch_provenance() -> None:
    measured_at = datetime(2026, 9, 25, tzinfo=timezone.utc)
    snapshot = build_wind_snapshot(
        "buoy-1",
        {
            "wind_speed_mps": 8.2,
            "wind_direction_degrees": 276.0,
            "sensor_channel": "B",
            "device_id": None,
            "sensor_id": "wind-b",
            "firmware_version": "4.0",
            "quality": "good",
            "measured_at": measured_at,
        },
        "unit-b",
    )

    assert snapshot.wind_speed_mps == 8.2
    assert snapshot.wind_direction_degrees == 276.0
    assert snapshot.sensor_channel == "B"
    assert snapshot.device_id == "unit-b"
    assert snapshot.measured_at == measured_at


def test_accepted_reading_counts_cover_all_supported_families() -> None:
    counts = empty_accepted_reading_counts()

    assert tuple(counts) == TELEMETRY_FAMILIES
    assert all(value == 0 for value in counts.values())


def test_ingestion_router_delegates_device_provenance_to_application() -> None:
    router_source = (
        Path(__file__).parents[1] / "app" / "routers" / "ingestion.py"
    ).read_text(encoding="utf-8")

    assert 'reading_data["device_id"]' not in router_source
    assert 'location_data["device_id"]' not in router_source
    assert router_source.count("with_device_provenance(") == 12
    assert "BuoyLocationReading(" not in router_source
    assert "reading = TemperatureReading(" not in router_source
    assert "reading = PressureReading(" not in router_source
    assert "reading = SalinityReading(" not in router_source
    assert "reading = ImuReading(" not in router_source
    assert "reading = AmbientLightReading(" not in router_source
    assert "reading = WindReading(" not in router_source
