"""Device registration conflicts and ownership boundaries."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.repository import BuoyRepository


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def database():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


@pytest.mark.parametrize("same_id", [True, False])
def test_registration_handles_conflict_after_precheck(client, monkeypatch, same_id):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Race"}).json()["id"]
    path = f"/api/v1/buoys/{buoy_id}/devices"
    original_create = BuoyRepository.create_device

    def conflicting_create(repository, buoy_id, payload):
        # The precheck succeeded, but a competing insert has claimed the key.
        winner = payload.model_copy(
            update={"sensor_channel": "B"} if same_id else {"device_id": "winner"}
        )
        original_create(repository, buoy_id, winner)
        return original_create(repository, buoy_id, payload)

    monkeypatch.setattr(BuoyRepository, "create_device", conflicting_create)
    response = client.post(path, json={"device_id": "other", "sensor_channel": "A"})
    assert response.status_code == 409
    assert len(client.get(path).json()) == 1


def test_device_status_cannot_be_changed_from_another_buoy(client):
    owner = client.post("/api/v1/buoys", json={"name": "Owner"}).json()["id"]
    other = client.post("/api/v1/buoys", json={"name": "Other"}).json()["id"]
    path = f"/api/v1/buoys/{owner}/devices"
    client.post(path, json={"device_id": "unit", "sensor_channel": "A"})
    response = client.patch(
        f"/api/v1/buoys/{other}/devices/unit/status", json={"status": "inactive"}
    )
    assert response.status_code == 404
    assert client.get(path).json()[0]["status"] == "active"


def test_batch_telemetry_records_device_heartbeat(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Heartbeat"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "heartbeat-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={"device_id": "heartbeat-unit", "location": {"latitude": 1, "longitude": 2}},
    )

    assert response.status_code == 202
    device = client.get(f"/api/v1/buoys/{buoy_id}/devices").json()[0]
    assert device["last_seen_at"] is not None
    assert "tidewatch_device_last_seen_timestamp_seconds" in client.get("/metrics").text


def test_batch_location_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "GNSS Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "gnss-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={"device_id": "gnss-unit", "location": {"latitude": 1, "longitude": 2}},
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/locations").json()[0]["device_id"] == "gnss-unit"


def test_batch_imu_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "IMU Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "imu-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "device_id": "imu-unit",
            "imu": [{
                "acceleration_x_mps2": 0,
                "acceleration_y_mps2": 0,
                "acceleration_z_mps2": 9.8,
                "angular_velocity_x_dps": 0,
                "angular_velocity_y_dps": 0,
                "angular_velocity_z_dps": 0,
            }],
        },
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/imu").json()[0]["device_id"] == "imu-unit"


def test_batch_core_sensors_keep_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Core Sensors"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "core-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "device_id": "core-unit",
            "temperatures": [{"temperature_celsius": 20}],
            "pressures": [{"pressure_kpa": 101}],
            "salinity": [{"salinity_psu": 35}],
        },
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/temperatures").json()[0]["device_id"] == "core-unit"
    assert client.get(f"/api/v1/buoys/{buoy_id}/pressures").json()[0]["device_id"] == "core-unit"
    assert client.get(f"/api/v1/buoys/{buoy_id}/salinity").json()[0]["device_id"] == "core-unit"


def test_batch_ambient_light_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Light Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "light-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={"device_id": "light-unit", "ambient_light": [{"illuminance_lux": 400}]},
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/ambient-light").json()[0]["device_id"] == "light-unit"


def test_batch_wind_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Wind Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "wind-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "device_id": "wind-unit",
            "wind": [{"wind_speed_mps": 4, "wind_direction_degrees": 90}],
        },
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/wind").json()[0]["device_id"] == "wind-unit"


def test_batch_marine_current_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Current Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "current-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "device_id": "current-unit",
            "marine_current": [{"current_speed_mps": 1.2, "current_direction_degrees": 180}],
        },
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/marine-current").json()[0]["device_id"] == "current-unit"


def test_batch_turbidity_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Turbidity Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "turbidity-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={"device_id": "turbidity-unit", "turbidity": [{"turbidity_ntu": 12}]},
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/turbidity").json()[0]["device_id"] == "turbidity-unit"


def test_batch_dissolved_oxygen_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "Oxygen Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "oxygen-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "device_id": "oxygen-unit",
            "dissolved_oxygen": [{"dissolved_oxygen_mg_l": 8}],
        },
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/dissolved-oxygen").json()[0]["device_id"] == "oxygen-unit"


def test_batch_ph_keeps_originating_device(client):
    buoy_id = client.post("/api/v1/buoys", json={"name": "pH Device"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/devices",
        json={"device_id": "ph-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={"device_id": "ph-unit", "ph": [{"ph": 8.1}]},
    )

    assert response.status_code == 202
    assert client.get(f"/api/v1/buoys/{buoy_id}/ph").json()[0]["device_id"] == "ph-unit"


def test_batch_telemetry_rejects_device_from_another_buoy(client):
    owner = client.post("/api/v1/buoys", json={"name": "Owner"}).json()["id"]
    other = client.post("/api/v1/buoys", json={"name": "Other"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{owner}/devices",
        json={"device_id": "owned-unit", "sensor_channel": "A"},
    )

    response = client.post(
        f"/api/v1/buoys/{other}/telemetry",
        json={"device_id": "owned-unit", "location": {"latitude": 1, "longitude": 2}},
    )

    assert response.status_code == 404
