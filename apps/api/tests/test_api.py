from fastapi.testclient import TestClient

from app.main import app, store

client = TestClient(app)


def setup_function() -> None:
    store.buoys.clear()
    store.readings.clear()


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_buoy_and_record_temperature() -> None:
    buoy = client.post("/api/v1/buoys", json={"name": "Mediterranean Sentinel"})
    buoy_id = buoy.json()["id"]

    reading = client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 19.7},
    )

    assert buoy.status_code == 201
    assert reading.status_code == 201
    assert reading.json()["buoy_id"] == buoy_id
    assert reading.json()["temperature_celsius"] == 19.7


def test_temperature_must_be_in_valid_range() -> None:
    buoy = client.post("/api/v1/buoys", json={"name": "Test Buoy"}).json()

    response = client.post(
        f"/api/v1/buoys/{buoy['id']}/temperatures",
        json={"temperature_celsius": 80},
    )

    assert response.status_code == 422


def test_unknown_buoy_returns_not_found() -> None:
    response = client.post(
        "/api/v1/buoys/UNKNOWN/temperatures",
        json={"temperature_celsius": 20},
    )

    assert response.status_code == 404
