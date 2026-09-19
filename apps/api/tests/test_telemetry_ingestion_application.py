from pathlib import Path

from app.application.telemetry_ingestion import with_device_provenance


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


def test_ingestion_router_delegates_device_provenance_to_application() -> None:
    router_source = (
        Path(__file__).parents[1] / "app" / "routers" / "ingestion.py"
    ).read_text(encoding="utf-8")

    assert 'reading_data["device_id"]' not in router_source
    assert 'location_data["device_id"]' not in router_source
    assert router_source.count("with_device_provenance(") == 19
