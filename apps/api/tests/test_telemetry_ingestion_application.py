from datetime import datetime, timezone
from pathlib import Path

from app.application.telemetry_ingestion import (
    TELEMETRY_FAMILIES,
    build_location_snapshot,
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
    assert router_source.count("with_device_provenance(") == 18
    assert "BuoyLocationReading(" not in router_source
