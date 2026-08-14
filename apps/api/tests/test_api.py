from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal, create_tables
from app.entities import BuoyEntity, TemperatureReadingEntity
from app.main import app

client = TestClient(app)
create_tables()


def setup_function() -> None:
    with SessionLocal() as db:
        db.execute(delete(TemperatureReadingEntity))
        db.execute(delete(BuoyEntity))
        db.commit()


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_buoy_and_record_temperature() -> None:
    buoy = client.post(
        "/api/v1/buoys",
        json={
            "name": "Mediterranean Sentinel",
            "latitude": 36.7,
            "longitude": 3.1,
        },
    )
    buoy_id = buoy.json()["id"]

    reading = client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 19.7},
    )

    assert buoy.status_code == 201
    assert buoy.json()["latitude"] == 36.7
    assert buoy.json()["longitude"] == 3.1
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


def test_temperature_analysis_detects_anomaly() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Analysis Buoy"}).json()["id"]

    measured_at = datetime.now(timezone.utc)
    for index, temperature in enumerate((20, 20.1, 19.9, 25)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={
                "temperature_celsius": temperature,
                "measured_at": (measured_at + timedelta(minutes=index)).isoformat(),
            },
        )
        assert response.status_code == 201

    analysis = client.get(
        f"/api/v1/buoys/{buoy_id}/temperature-analysis?threshold=2"
    )

    assert analysis.status_code == 200
    assert analysis.json()["sample_count"] == 4
    assert analysis.json()["is_anomaly"] is True
    assert analysis.json()["trend"] == "rising"
    assert analysis.json()["change_celsius"] == 5


def test_temperature_alerts_returns_anomalous_buoy() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Alert Buoy"}).json()["id"]

    measured_at = datetime.now(timezone.utc)
    for index, temperature in enumerate((18, 18.1, 17.9, 24)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={
                "temperature_celsius": temperature,
                "measured_at": (measured_at + timedelta(minutes=index)).isoformat(),
            },
        )
        assert response.status_code == 201

    alerts = client.get("/api/v1/alerts/temperature?threshold=2")

    assert alerts.status_code == 200
    assert len(alerts.json()) == 1
    assert alerts.json()[0]["buoy_id"] == buoy_id
    assert alerts.json()[0]["severity"] == "warning"


def test_temperature_alert_can_be_persisted_and_resolved() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Persistent Alert Buoy"}).json()["id"]

    measured_at = datetime.now(timezone.utc)
    for index, temperature in enumerate((18, 18.1, 17.9, 24)):
        client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={
                "temperature_celsius": temperature,
                "measured_at": (measured_at + timedelta(minutes=index)).isoformat(),
            },
        )

    evaluated = client.post("/api/v1/alerts/temperature/evaluate?threshold=2")
    assert evaluated.status_code == 200
    assert len(evaluated.json()) == 1
    alert_id = evaluated.json()[0]["id"]

    resolved = client.post(f"/api/v1/alerts/temperature/{alert_id}/resolve")
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
