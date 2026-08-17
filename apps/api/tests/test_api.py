from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal, create_tables
from app.entities import (
    BuoyEntity,
    BuoyLocationReadingEntity,
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
        db.execute(delete(BuoyLocationReadingEntity))
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


def test_batch_telemetry_ingestion_accepts_all_sensor_families() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Batch Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "temperatures": [{"temperature_celsius": 19.8, "sensor_channel": "A"}],
            "pressures": [
                {"pressure_kpa": 101.4, "sensor_channel": "A"},
                {"pressure_kpa": 101.5, "sensor_channel": "B"},
            ],
            "salinity": [{"salinity_psu": 35.1}],
            "battery": {"battery_percent": 87.5},
            "location": {"latitude": 36.9, "longitude": 2.7},
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "buoy_id": buoy_id,
        "accepted_readings": 5,
        "accepted_by_family": {
            "temperature": 1,
            "pressure": 2,
            "salinity": 1,
            "battery": 1,
        },
    }
    summary = client.get("/api/v1/buoys").json()[0]
    assert summary["latest_temperature"]["temperature_celsius"] == 19.8
    assert summary["latest_temperature_a"]["temperature_celsius"] == 19.8
    assert summary["latest_temperature_b"] is None
    assert summary["latest_pressure"]["pressure_kpa"] == 101.4
    assert summary["latest_pressure_a"]["pressure_kpa"] == 101.4
    assert summary["latest_pressure_b"]["pressure_kpa"] == 101.5
    assert summary["latest_salinity"]["salinity_psu"] == 35.1
    assert summary["latest_salinity_a"]["salinity_psu"] == 35.1
    assert summary["latest_salinity_b"] is None
    assert summary["latest_battery"]["battery_percent"] == 87.5
    assert summary["buoy"]["latitude"] == 36.9
    assert summary["buoy"]["longitude"] == 2.7
    redundant_pressure = client.get(
        f"/api/v1/buoys/{buoy_id}/pressures?sensor_channel=B"
    )
    assert redundant_pressure.json()[0]["pressure_kpa"] == 101.5
    locations = client.get(f"/api/v1/buoys/{buoy_id}/locations")
    assert locations.status_code == 200
    assert locations.json()[0]["latitude"] == 36.9
    assert locations.json()[0]["longitude"] == 2.7


def test_batch_telemetry_accepts_redundant_batteries() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Dual Battery Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "battery": [
                {"battery_percent": 92, "device_id": "A"},
                {"battery_percent": 88, "device_id": "B"},
            ]
        },
    )

    assert response.status_code == 202
    assert response.json()["accepted_readings"] == 2
    assert response.json()["accepted_by_family"]["battery"] == 2
    assert client.get(f"/api/v1/buoys/{buoy_id}/battery?device_id=A").json()["battery_percent"] == 92
    assert client.get(f"/api/v1/buoys/{buoy_id}/battery?device_id=B").json()["battery_percent"] == 88
    summary = client.get("/api/v1/buoys").json()[0]
    assert summary["latest_battery_a"]["battery_percent"] == 92
    assert summary["latest_battery_b"]["battery_percent"] == 88


def test_batch_telemetry_rejects_duplicate_battery_devices() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Duplicate Battery Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "battery": [
                {"battery_percent": 92, "device_id": "A"},
                {"battery_percent": 91, "device_id": "A"},
            ]
        },
    )

    assert response.status_code == 422


def test_batch_telemetry_rejects_duplicate_sensor_channels() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Duplicate Sensor Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "temperatures": [
                {"temperature_celsius": 20, "sensor_channel": "A"},
                {"temperature_celsius": 20.1, "sensor_channel": "A"},
            ]
        },
    )

    assert response.status_code == 422


def test_empty_telemetry_batch_is_rejected() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Empty Batch Buoy"}).json()["id"]

    response = client.post(f"/api/v1/buoys/{buoy_id}/telemetry", json={})

    assert response.status_code == 422


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


def test_buoy_location_can_be_updated() -> None:
    buoy_id = client.post(
        "/api/v1/buoys",
        json={"name": "Moving Buoy", "latitude": 36.7, "longitude": 3.1},
    ).json()["id"]

    updated = client.patch(
        f"/api/v1/buoys/{buoy_id}/location",
        json={"latitude": 37.2, "longitude": 2.8},
    )

    assert updated.status_code == 200
    assert updated.json()["latitude"] == 37.2
    assert updated.json()["longitude"] == 2.8
    locations = client.get(f"/api/v1/buoys/{buoy_id}/locations")
    assert locations.status_code == 200
    assert locations.json()[0]["latitude"] == 37.2


def test_buoy_location_rejects_invalid_coordinates() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Coordinate Buoy"}).json()["id"]

    response = client.patch(
        f"/api/v1/buoys/{buoy_id}/location",
        json={"latitude": 95, "longitude": 2},
    )

    assert response.status_code == 422


def test_movement_analysis_estimates_distance_and_speed() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Drifting Buoy", "latitude": 0, "longitude": 0}
    ).json()["id"]
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for index, longitude in enumerate((0, 0.01, 0.02)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/telemetry",
            json={
                "temperatures": [{"temperature_celsius": 20}],
                "location": {
                    "latitude": 0,
                    "longitude": longitude,
                    "measured_at": (start + timedelta(minutes=30 * index)).isoformat(),
                },
            },
        )
        assert response.status_code == 202

    analysis = client.get(f"/api/v1/buoys/{buoy_id}/movement-analysis")

    assert analysis.status_code == 200
    assert analysis.json()["sample_count"] == 3
    assert 2200 < analysis.json()["distance_travelled_m"] < 2250
    assert analysis.json()["displacement_m"] == analysis.json()["distance_travelled_m"]
    assert 0.6 < analysis.json()["average_speed_mps"] < 0.7
    assert analysis.json()["confidence"] == "experimental"
    metrics = client.get("/metrics")
    assert "tidewatch_buoy_movement_speed_mps" in metrics.text
    assert f'buoy_id="{buoy_id}"' in metrics.text
    filtered_locations = client.get(
        f"/api/v1/buoys/{buoy_id}/locations",
        params={
            "since": (start + timedelta(minutes=30)).isoformat(),
            "until": (start + timedelta(minutes=60)).isoformat(),
        },
    )
    assert filtered_locations.status_code == 200
    assert [item["longitude"] for item in filtered_locations.json()] == [0.02, 0.01]
    export = client.get(
        f"/api/v1/buoys/{buoy_id}/locations/export",
        params={"limit": 2},
    )
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert export.headers["content-disposition"] == (
        f'attachment; filename="{buoy_id}-locations.csv"'
    )
    assert export.text.splitlines()[0] == "buoy_id,latitude,longitude,measured_at"
    assert len(export.text.splitlines()) == 3
    fleet_export = client.get("/api/v1/locations/export?limit=2")
    assert fleet_export.status_code == 200
    assert fleet_export.headers["content-disposition"] == (
        'attachment; filename="tidewatch-locations.csv"'
    )
    assert len(fleet_export.text.splitlines()) == 3
    invalid_window = client.get(
        f"/api/v1/buoys/{buoy_id}/locations",
        params={
            "since": (start + timedelta(hours=1)).isoformat(),
            "until": start.isoformat(),
        },
    )
    assert invalid_window.status_code == 422


def test_maintenance_issues_detect_buoy_drift() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Drift Alert Buoy", "latitude": 0, "longitude": 0}
    ).json()["id"]
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for index, longitude in enumerate((0, 0.01, 0.02)):
        client.post(
            f"/api/v1/buoys/{buoy_id}/telemetry",
            json={
                "temperatures": [{"temperature_celsius": 20}],
                "location": {
                    "latitude": 0,
                    "longitude": longitude,
                    "measured_at": (start + timedelta(minutes=30 * index)).isoformat(),
                },
            },
        )

    issues = client.get("/api/v1/maintenance/issues?drift_speed_mps=0.5")

    assert issues.status_code == 200
    drift_issue = next(issue for issue in issues.json() if issue["issue_type"] == "drift_detected")
    assert drift_issue["buoy_id"] == buoy_id
    assert drift_issue["severity"] == "warning"


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
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "tidewatch_reading_quality_total" in metrics.text
    assert f'buoy_id="{buoy["id"]}"' in metrics.text
    assert 'quality="suspect"' in metrics.text


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


def test_suspect_latest_reading_creates_warning_issue() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Suspect Reading Buoy"}).json()["id"]
    response = client.post(
        f"/api/v1/buoys/{buoy_id}/salinity",
        json={"salinity_psu": 35.4, "quality": "suspect"},
    )

    assert response.status_code == 201
    issues = client.get("/api/v1/maintenance/issues")

    assert issues.status_code == 200
    assert any(
        issue["issue_type"] == "suspect_reading"
        and issue["severity"] == "warning"
        for issue in issues.json()
    )


def test_quality_summary_counts_all_sensor_readings() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Quality Summary Buoy"}).json()["id"]
    for quality in ("good", "suspect", "invalid"):
        client.post(
            f"/api/v1/buoys/{buoy_id}/temperatures",
            json={"temperature_celsius": 20, "quality": quality},
        )
    client.post(
        f"/api/v1/buoys/{buoy_id}/pressures",
        json={"pressure_kpa": 101.3},
    )

    summary = client.get(f"/api/v1/buoys/{buoy_id}/quality-summary")

    assert summary.status_code == 200
    assert summary.json() == {
        "buoy_id": buoy_id,
        "total_readings": 4,
        "good_readings": 2,
        "suspect_readings": 1,
        "invalid_readings": 1,
    }


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


def test_sensor_health_identifies_missing_redundant_channel() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Missing Sensor Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 20, "sensor_channel": "A"},
    )

    health = client.get(f"/api/v1/buoys/{buoy_id}/sensor-health")

    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert health.json()["degraded_sensors"] == []
    assert health.json()["missing_sensors"] == ["temperature:B"]

    metrics = client.get("/metrics")
    assert 'tidewatch_sensor_channel_missing{buoy_id="' in metrics.text
    assert 'sensor="temperature",sensor_channel="B"} 1.0' in metrics.text


def test_maintenance_issues_reports_missing_sensor_channel() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Missing Sensor Maintenance"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/pressures",
        json={"pressure_kpa": 101.3, "sensor_channel": "B"},
    )

    issues = client.get("/api/v1/maintenance/issues")

    missing_issue = next(
        issue for issue in issues.json() if issue["issue_type"] == "missing_sensor_channel"
    )
    assert missing_issue["buoy_id"] == buoy_id
    assert "pressure:A" in missing_issue["message"]


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


def test_invalid_reading_is_ignored_by_sensor_health_comparison() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Invalid Health Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 20, "sensor_channel": "A"},
    )
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={
            "temperature_celsius": 45,
            "sensor_channel": "A",
            "quality": "invalid",
        },
    )
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 20.1, "sensor_channel": "B"},
    )

    health = client.get(f"/api/v1/buoys/{buoy_id}/sensor-health")

    assert health.status_code == 200
    assert health.json()["status"] == "consistent"
    assert health.json()["temperature_delta_celsius"] == 0.1


def test_low_battery_creates_maintenance_issue() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Low Battery Buoy"}).json()["id"]
    battery = client.post(
        f"/api/v1/buoys/{buoy_id}/battery",
        json={"battery_percent": 12.5},
    )

    assert battery.status_code == 201
    assert battery.json()["battery_percent"] == 12.5
    assert battery.json()["device_id"] == "A"
    backup_battery = client.post(
        f"/api/v1/buoys/{buoy_id}/battery",
        json={
            "battery_percent": 96,
            "device_id": "B",
            "measured_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        },
    )
    assert backup_battery.status_code == 201
    assert backup_battery.json()["device_id"] == "B"
    latest_backup = client.get(f"/api/v1/buoys/{buoy_id}/battery?device_id=B")
    assert latest_backup.status_code == 200
    assert latest_backup.json()["battery_percent"] == 96
    battery_history = client.get(
        f"/api/v1/buoys/{buoy_id}/battery/history?device_id=B"
    )
    assert battery_history.status_code == 200
    assert battery_history.json()[0]["device_id"] == "B"
    assert battery_history.json()[0]["battery_percent"] == 96
    battery_analysis = client.get(
        f"/api/v1/buoys/{buoy_id}/battery-analysis?device_id=A"
    )
    assert battery_analysis.status_code == 200
    assert battery_analysis.json()["sample_count"] == 1
    assert battery_analysis.json()["confidence"] == "insufficient_data"
    health = client.get(f"/api/v1/buoys/{buoy_id}/battery-health")
    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert health.json()["degraded_devices"] == ["A"]
    metrics = client.get("/metrics")
    assert "tidewatch_battery_device_percent" in metrics.text
    assert 'device_id="A"' in metrics.text
    assert "tidewatch_battery_delta_percent" in metrics.text
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "tidewatch_battery_percent" in metrics.text
    assert f'buoy_id="{buoy_id}"' in metrics.text
    issues = client.get("/api/v1/maintenance/issues")

    low_battery_issue = next(
        issue for issue in issues.json() if issue["issue_type"] == "low_battery"
    )
    assert "device A" in low_battery_issue["message"]


def test_missing_redundant_battery_device_creates_maintenance_issue() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Single Battery Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/battery",
        json={"battery_percent": 80, "device_id": "A"},
    )

    issues = client.get("/api/v1/maintenance/issues")

    missing_issue = next(
        issue for issue in issues.json() if issue["issue_type"] == "missing_redundant_device"
    )
    assert missing_issue["buoy_id"] == buoy_id
    assert "device B" in missing_issue["message"]


def test_battery_analysis_estimates_discharge_rate() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Battery Analysis Buoy"}).json()["id"]
    now = datetime.now(timezone.utc)
    for hours_ago, battery_percent in ((2, 80), (1, 70), (0, 60)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/battery",
            json={
                "battery_percent": battery_percent,
                "device_id": "A",
                "measured_at": (now - timedelta(hours=hours_ago)).isoformat(),
            },
        )
        assert response.status_code == 201

    analysis = client.get(f"/api/v1/buoys/{buoy_id}/battery-analysis?device_id=A")

    assert analysis.status_code == 200
    assert analysis.json()["sample_count"] == 3
    assert analysis.json()["change_percent"] == -20
    assert analysis.json()["discharge_rate_percent_per_hour"] == 10
    assert analysis.json()["estimated_hours_remaining"] == 6
    assert analysis.json()["confidence"] == "experimental"
    metrics = client.get("/metrics")
    assert "tidewatch_redundant_device_missing" in metrics.text
    assert f'buoy_id="{buoy_id}"' in metrics.text
    assert 'device_id="B"' in metrics.text


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
