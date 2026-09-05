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
