from app.application.telemetry_ingestion import with_device_provenance


def test_batch_device_is_used_when_reading_has_no_owner() -> None:
    assert with_device_provenance({"device_id": None}, "unit-a") == {
        "device_id": "unit-a"
    }


def test_explicit_reading_owner_is_preserved() -> None:
    assert with_device_provenance({"device_id": "unit-b"}, "unit-a") == {
        "device_id": "unit-b"
    }
