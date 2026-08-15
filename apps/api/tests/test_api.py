from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal, create_tables
from app.entities import (
    BuoyEntity,
    BatteryReadingEntity,
    PressureReadingEntity,
    SalinityReadingEntity,
    TemperatureReadingEntity,
)
from app.main import app

client = TestClient(app)
create_tables()


def setup_function() -> None:
    with SessionLocal() as db:
        db.execute(delete(PressureReadingEntity))
        db.execute(delete(SalinityReadingEntity))
        db.execute(delete(BatteryReadingEntity))
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
    assert buoy.json()["status"] == "active"
    assert reading.status_code == 201
    assert reading.json()["buoy_id"] == buoy_id
    assert reading.json()["temperature_celsius"] == 19.7


def test_temperature_updates_buoy_last_seen_and_status_can_change() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Operational Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 20},
    )

    updated = client.patch(
        f"/api/v1/buoys/{buoy_id}/status",
        json={"status": "maintenance"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "maintenance"
    assert updated.json()["last_seen_at"] is not None


def test_stale_buoy_is_reported_for_maintenance() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Silent Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={
            "temperature_celsius": 20,
            "measured_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        },
    )

    stale = client.get("/api/v1/buoys/stale?max_age_minutes=30")

    assert stale.status_code == 200
    assert len(stale.json()) == 1
    assert stale.json()[0]["buoy_id"] == buoy_id
    assert stale.json()[0]["is_stale"] is True


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


def test_pressure_reading_is_recorded_and_returned_in_buoy_summary() -> None:
    buoy = client.post("/api/v1/buoys", json={"name": "Pressure Buoy"}).json()
    response = client.post(
        f"/api/v1/buoys/{buoy['id']}/pressures",
        json={"pressure_kpa": 101.325},
    )

    assert response.status_code == 201
    assert response.json()["buoy_id"] == buoy["id"]
    assert response.json()["pressure_kpa"] == 101.325

    summary = client.get("/api/v1/buoys")
    assert summary.status_code == 200
    assert summary.json()[0]["latest_pressure"]["pressure_kpa"] == 101.325


def test_reading_quality_is_persisted() -> None:
    buoy = client.post("/api/v1/buoys", json={"name": "Quality Buoy"}).json()
    response = client.post(
        f"/api/v1/buoys/{buoy['id']}/pressures",
        json={"pressure_kpa": 101.2, "quality": "suspect"},
    )

    assert response.status_code == 201
    assert response.json()["quality"] == "suspect"


def test_reading_quality_is_validated() -> None:
    buoy = client.post("/api/v1/buoys", json={"name": "Invalid Quality Buoy"}).json()
    response = client.post(
        f"/api/v1/buoys/{buoy['id']}/pressures",
        json={"pressure_kpa": 101.2, "quality": "unknown"},
    )

    assert response.status_code == 422


def test_invalid_temperature_is_kept_but_excluded_from_analysis() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Quality Analysis Buoy"}).json()["id"]
    measured_at = datetime.now(timezone.utc)
    for index, temperature in enumerate((20, 20.1, 19.9)):
        client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={
                "temperature_celsius": temperature,
                "measured_at": (measured_at + timedelta(minutes=index)).isoformat(),
            },
        )

    invalid = client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={
            "temperature_celsius": 45,
            "quality": "invalid",
            "measured_at": (measured_at + timedelta(minutes=3)).isoformat(),
        },
    )
    analysis = client.get(f"/api/v1/buoys/{buoy_id}/temperature-analysis")
    readings = client.get(f"/api/v1/buoys/{buoy_id}/temperatures?limit=10")

    assert invalid.status_code == 201
    assert analysis.status_code == 200
    assert analysis.json()["sample_count"] == 3
    assert readings.json()[0]["quality"] == "invalid"


def test_invalid_latest_reading_creates_maintenance_issue() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Invalid Reading Buoy"}).json()["id"]
    response = client.post(
        f"/api/v1/buoys/{buoy_id}/pressures",
        json={"pressure_kpa": 101.0, "quality": "invalid"},
    )

    assert response.status_code == 201
    issues = client.get("/api/v1/maintenance/issues")

    assert issues.status_code == 200
    assert any(issue["issue_type"] == "invalid_reading" for issue in issues.json())


def test_pressure_must_be_in_sensor_range() -> None:
    buoy = client.post("/api/v1/buoys", json={"name": "Pressure Range Buoy"}).json()

    response = client.post(
        f"/api/v1/buoys/{buoy['id']}/pressures",
        json={"pressure_kpa": 200},
    )

    assert response.status_code == 422


def test_pressure_analysis_estimates_wave_height() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Wave Buoy"}).json()["id"]
    measured_at = datetime.now(timezone.utc)

    for index, pressure in enumerate((101.3, 101.8, 100.8)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/pressures",
            json={
                "pressure_kpa": pressure,
                "measured_at": (measured_at + timedelta(minutes=index)).isoformat(),
            },
        )
        assert response.status_code == 201

    analysis = client.get(f"/api/v1/buoys/{buoy_id}/pressure-analysis")

    assert analysis.status_code == 200
    assert analysis.json()["sample_count"] == 3
    assert analysis.json()["pressure_range_kpa"] == 1
    assert analysis.json()["estimated_wave_height_m"] == 0.102
    assert analysis.json()["confidence"] == "experimental"
    assert analysis.json()["sea_state"] == "calm"


def test_salinity_reading_is_recorded_and_validated() -> None:
    buoy = client.post("/api/v1/buoys", json={"name": "Salinity Buoy"}).json()
    response = client.post(
        f"/api/v1/buoys/{buoy['id']}/salinity",
        json={"salinity_psu": 35.2},
    )

    assert response.status_code == 201
    assert response.json()["salinity_psu"] == 35.2
    summary = client.get("/api/v1/buoys").json()[0]
    assert summary["latest_salinity"]["salinity_psu"] == 35.2

    invalid = client.post(
        f"/api/v1/buoys/{buoy['id']}/salinity",
        json={"salinity_psu": 60},
    )
    assert invalid.status_code == 422


def test_sensor_health_compares_redundant_channels() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Redundant Buoy"}).json()["id"]

    for channel, temperature, pressure, salinity in (
        ("A", 20.0, 101.3, 35.2),
        ("B", 20.1, 101.4, 35.25),
    ):
        measured_at = datetime.now(timezone.utc).isoformat()
        client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={
                "temperature_celsius": temperature,
                "sensor_channel": channel,
                "measured_at": measured_at,
            },
        )
        client.post(
            f"/api/v1/buoys/{buoy_id}/pressures",
            json={
                "pressure_kpa": pressure,
                "sensor_channel": channel,
                "measured_at": measured_at,
            },
        )
        client.post(
            f"/api/v1/buoys/{buoy_id}/salinity",
            json={
                "salinity_psu": salinity,
                "sensor_channel": channel,
                "measured_at": measured_at,
            },
        )

    health = client.get(f"/api/v1/buoys/{buoy_id}/sensor-health")

    assert health.status_code == 200
    assert health.json()["status"] == "consistent"
    assert health.json()["temperature_delta_celsius"] == 0.1
    assert health.json()["pressure_delta_kpa"] == 0.1
    assert health.json()["degraded_sensors"] == []


def test_sensor_health_identifies_degraded_sensor() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Degraded Buoy"}).json()["id"]
    measured_at = datetime.now(timezone.utc).isoformat()
    for channel, temperature in (("A", 20.0), ("B", 21.0)):
        client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={
                "temperature_celsius": temperature,
                "sensor_channel": channel,
                "measured_at": measured_at,
            },
        )

    health = client.get(f"/api/v1/buoys/{buoy_id}/sensor-health")

    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert health.json()["degraded_sensors"] == ["temperature"]


def test_maintenance_issues_reports_degraded_sensor() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Maintenance Buoy"}).json()["id"]
    for channel, temperature in (("A", 20.0), ("B", 21.0)):
        client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={"temperature_celsius": temperature, "sensor_channel": channel},
        )

    issues = client.get("/api/v1/maintenance/issues")

    assert issues.status_code == 200
    assert issues.json()[0]["issue_type"] == "degraded_sensor"
    assert issues.json()[0]["buoy_id"] == buoy_id


def test_low_battery_creates_maintenance_issue() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Low Battery Buoy"}).json()["id"]
    battery = client.post(
        f"/api/v1/buoys/{buoy_id}/battery",
        json={"battery_percent": 12.5},
    )

    assert battery.status_code == 201
    assert battery.json()["battery_percent"] == 12.5
    issues = client.get("/api/v1/maintenance/issues")

    assert any(issue["issue_type"] == "low_battery" for issue in issues.json())


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
