from datetime import datetime, timedelta, timezone
import logging

from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import delete

from app.database import SessionLocal, create_tables, resolve_database_url
from app.entities import (
    BuoyEntity,
    BuoyLocationReadingEntity,
    BatteryReadingEntity,
    ImuReadingEntity,
    AmbientLightReadingEntity,
    WindReadingEntity,
    MarineCurrentReadingEntity,
    TurbidityReadingEntity,
    DissolvedOxygenReadingEntity,
    PHReadingEntity,
    ConductivityReadingEntity,
    ChlorophyllAReadingEntity,
    RainfallReadingEntity,
    HumidityReadingEntity,
    AirTemperatureReadingEntity,
    AtmosphericPressureReadingEntity,
    AcousticAltimeterReadingEntity,
    PressureReadingEntity,
    SalinityReadingEntity,
    SensorHealthCheckEntity,
    TemperatureReadingEntity,
)
from app.main import app
from app.telemetry import configure_telemetry
import app.main as main_module

client = TestClient(app)
create_tables()


def test_opentelemetry_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    telemetry_app = FastAPI()

    assert configure_telemetry(telemetry_app) is False


def test_database_url_can_be_resolved_from_mounted_secret(tmp_path, monkeypatch) -> None:
    secret_file = tmp_path / "DATABASE_URL"
    secret_file.write_text("postgresql+psycopg://user:pass@db/tidewatch\n", encoding="utf-8")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL_FILE", str(secret_file))

    assert resolve_database_url() == "postgresql+psycopg://user:pass@db/tidewatch"


def setup_function() -> None:
    with SessionLocal() as db:
        db.execute(delete(PressureReadingEntity))
        db.execute(delete(SalinityReadingEntity))
        db.execute(delete(BatteryReadingEntity))
        db.execute(delete(ImuReadingEntity))
        db.execute(delete(AmbientLightReadingEntity))
        db.execute(delete(WindReadingEntity))
        db.execute(delete(MarineCurrentReadingEntity))
        db.execute(delete(TurbidityReadingEntity))
        db.execute(delete(DissolvedOxygenReadingEntity))
        db.execute(delete(PHReadingEntity))
        db.execute(delete(ConductivityReadingEntity))
        db.execute(delete(ChlorophyllAReadingEntity))
        db.execute(delete(RainfallReadingEntity))
        db.execute(delete(HumidityReadingEntity))
        db.execute(delete(AirTemperatureReadingEntity))
        db.execute(delete(AtmosphericPressureReadingEntity))
        db.execute(delete(AcousticAltimeterReadingEntity))
        db.execute(delete(TemperatureReadingEntity))
        db.execute(delete(SensorHealthCheckEntity))
        db.execute(delete(BuoyLocationReadingEntity))
        db.execute(delete(BuoyEntity))
        db.commit()


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_http_requests_are_logged(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="tidewatch.api"):
        response = client.get("/health")

    assert response.status_code == 200
    assert "http_request method=GET path=/health status_code=200" in caplog.text


def test_http_request_metrics_are_exposed() -> None:
    client.get("/health")

    metrics = client.get("/metrics")

    assert metrics.status_code == 200
    assert "tidewatch_http_requests_total" in metrics.text
    assert 'method="GET",status_code="200"' in metrics.text
    assert "tidewatch_http_request_duration_seconds" in metrics.text


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
            "temperatures": [{
                "temperature_celsius": 19.8,
                "sensor_channel": "A",
                "sensor_id": "temp-a-01",
                "firmware_version": "2.4.1",
            }],
            "pressures": [
                {
                    "pressure_kpa": 101.4,
                    "sensor_channel": "A",
                    "sensor_id": "pressure-a-01",
                    "firmware_version": "2.4.1",
                },
                {"pressure_kpa": 101.5, "sensor_channel": "B"},
            ],
            "salinity": [{
                "salinity_psu": 35.1,
                "sensor_id": "salinity-a-01",
                "firmware_version": "2.4.1",
            }],
            "imu": [{
                "acceleration_x_mps2": 0.12,
                "acceleration_y_mps2": -0.08,
                "acceleration_z_mps2": 9.79,
                "angular_velocity_x_dps": 0.4,
                "angular_velocity_y_dps": -0.2,
                "angular_velocity_z_dps": 0.1,
                "sensor_channel": "A",
                "sensor_id": "imu-a-01",
                "firmware_version": "2.4.1",
            }],
            "battery": {"battery_percent": 87.5},
            "location": {"latitude": 36.9, "longitude": 2.7},
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "buoy_id": buoy_id,
        "accepted_readings": 6,
        "accepted_by_family": {
            "temperature": 1,
            "pressure": 2,
            "salinity": 1,
            "imu": 1,
            "ambient_light": 0,
            "wind": 0,
            "marine_current": 0,
            "turbidity": 0,
            "dissolved_oxygen": 0,
            "ph": 0,
            "conductivity": 0,
            "chlorophyll_a": 0,
            "rainfall": 0,
            "humidity": 0,
            "air_temperature": 0,
            "atmospheric_pressure": 0,
            "acoustic_altimeter": 0,
            "battery": 1,
        },
    }
    summary = client.get("/api/v1/buoys").json()[0]
    assert summary["latest_temperature"]["temperature_celsius"] == 19.8
    assert summary["latest_imu"]["acceleration_z_mps2"] == 9.79
    metrics = client.get("/metrics")
    assert "tidewatch_imu_readings_total" in metrics.text
    assert 'tidewatch_current_imu_acceleration_mps2{axis="z"' in metrics.text
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
    temperature = client.get(f"/api/v1/buoys/{buoy_id}/temperatures").json()[0]
    assert temperature["sensor_id"] == "temp-a-01"
    assert temperature["firmware_version"] == "2.4.1"
    pressure = client.get(f"/api/v1/buoys/{buoy_id}/pressures").json()[0]
    assert pressure["sensor_id"] == "pressure-a-01"
    salinity = client.get(f"/api/v1/buoys/{buoy_id}/salinity").json()[0]
    assert salinity["sensor_id"] == "salinity-a-01"
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


def test_gnss_metadata_is_persisted_with_location() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "GNSS Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/telemetry",
        json={
            "location": {
                "latitude": 36.7,
                "longitude": 3.1,
                "altitude_meters": 2.4,
                "speed_mps": 0.8,
                "hdop": 0.9,
                "satellites": 14,
            }
        },
    )

    assert response.status_code == 202
    location = client.get(f"/api/v1/buoys/{buoy_id}/locations").json()[0]
    assert location["altitude_meters"] == 2.4
    assert location["speed_mps"] == 0.8
    assert location["hdop"] == 0.9
    assert location["satellites"] == 14
    metrics = client.get("/metrics")
    assert "tidewatch_current_gnss_altitude_meters" in metrics.text
    assert "tidewatch_current_gnss_speed_mps" in metrics.text
    assert "tidewatch_current_gnss_hdop" in metrics.text
    assert "tidewatch_current_gnss_satellites" in metrics.text


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


def test_maintenance_notification_requires_webhook_configuration(
    monkeypatch,
) -> None:
    monkeypatch.delenv("MAINTENANCE_WEBHOOK_URL", raising=False)

    response = client.post("/api/v1/maintenance/notifications")

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_maintenance_notification_delivers_current_issues(monkeypatch) -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Webhook Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 20, "sensor_channel": "A"},
    )
    captured = {}

    class WebhookResponse:
        def raise_for_status(self) -> None:
            return None

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["payload"] = kwargs["json"]
        return WebhookResponse()

    monkeypatch.setenv("MAINTENANCE_WEBHOOK_URL", "https://hooks.example.test/tidewatch")
    monkeypatch.setattr(main_module.httpx, "post", fake_post)

    response = client.post("/api/v1/maintenance/notifications")

    assert response.status_code == 202
    assert response.json()["status"] == "sent"
    assert captured["url"] == "https://hooks.example.test/tidewatch"
    assert captured["payload"]["source"] == "tidewatch"
    assert any(
        issue["issue_type"] == "missing_sensor_channel"
        for issue in captured["payload"]["issues"]
    )


def test_sensor_health_reports_stale_redundant_channel_as_missing() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Stale Sensor Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={
            "temperature_celsius": 20,
            "sensor_channel": "A",
            "measured_at": (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat(),
        },
    )
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 20.1, "sensor_channel": "B"},
    )

    health = client.get(f"/api/v1/buoys/{buoy_id}/sensor-health?max_age_minutes=30")

    assert health.status_code == 200
    assert health.json()["missing_sensors"] == ["temperature:A"]
    assert health.json()["status"] == "degraded"


def test_sensor_health_check_is_persisted_and_retrievable() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Health History Buoy"}).json()["id"]
    client.post(
        f"/api/v1/buoys/{buoy_id}/temperatures",
        json={"temperature_celsius": 20, "sensor_channel": "A"},
    )

    check = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")
    history = client.get(f"/api/v1/buoys/{buoy_id}/sensor-health/history")

    assert check.status_code == 201
    assert check.json()["status"] == "degraded"
    assert check.json()["missing_sensors"] == ["temperature:B"]
    assert check.json()["decisions"]["temperature"] == "fallback_a"
    assert history.status_code == 200
    assert history.json()[0]["id"] == check.json()["id"]
    assert history.json()[0]["decisions"]["temperature"] == "fallback_a"
    metrics = client.get("/metrics")
    assert 'tidewatch_sensor_health_decision{buoy_id="' in metrics.text
    assert 'decision="fallback_a",sensor="temperature"} 1.0' in metrics.text


def test_sensor_health_compares_redundant_imu_acceleration() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "IMU Health Buoy"}).json()["id"]
    for channel, x_value in (("A", 0.10), ("B", 0.25)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/imu",
            json={
                "acceleration_x_mps2": x_value,
                "acceleration_y_mps2": 0.0,
                "acceleration_z_mps2": 9.8,
                "angular_velocity_x_dps": 0.1,
                "angular_velocity_y_dps": 0.1,
                "angular_velocity_z_dps": 0.1,
                "sensor_channel": channel,
            },
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["imu_acceleration_delta_mps2"] == 0.15
    assert health.json()["decisions"]["imu"] == "average"


def test_ambient_light_ingestion_exposes_latest_lux() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Light Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/ambient-light",
        json={
            "illuminance_lux": 845.5,
            "sensor_channel": "A",
            "sensor_id": "ambient-light-a-01",
            "firmware_version": "2.4.1",
        },
    )

    assert response.status_code == 201
    assert response.json()["illuminance_lux"] == 845.5
    listing = client.get(f"/api/v1/buoys/{buoy_id}/ambient-light")
    assert listing.status_code == 200
    assert listing.json()[0]["buoy_id"] == buoy_id
    metrics = client.get("/metrics")
    assert "tidewatch_ambient_light_readings_total" in metrics.text
    assert "tidewatch_current_ambient_light_lux" in metrics.text


def test_sensor_health_compares_redundant_ambient_light() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Light Health Buoy"}).json()["id"]
    for channel, lux in (("A", 800.0), ("B", 1200.0)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/ambient-light",
            json={"illuminance_lux": lux, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["ambient_light_delta_lux"] == 400.0
    assert health.json()["decisions"]["ambient_light"] == "average"


def test_wind_ingestion_exposes_speed_and_direction() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Wind Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/wind",
        json={
            "wind_speed_mps": 6.4,
            "wind_direction_degrees": 275.0,
            "sensor_channel": "A",
            "sensor_id": "wind-a-01",
            "firmware_version": "2.4.1",
        },
    )

    assert response.status_code == 201
    assert response.json()["wind_speed_mps"] == 6.4
    assert client.get(f"/api/v1/buoys/{buoy_id}/wind").json()[0]["wind_direction_degrees"] == 275.0
    metrics = client.get("/metrics")
    assert "tidewatch_wind_readings_total" in metrics.text
    assert "tidewatch_current_wind_speed_mps" in metrics.text
    assert "tidewatch_current_wind_direction_degrees" in metrics.text


def test_sensor_health_compares_wind_direction_circularly() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Wind Health Buoy"}).json()["id"]
    for channel, direction in (("A", 359.0), ("B", 1.0)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/wind",
            json={
                "wind_speed_mps": 5.0,
                "wind_direction_degrees": direction,
                "sensor_channel": channel,
            },
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["wind_speed_delta_mps"] == 0.0
    assert health.json()["wind_direction_delta_degrees"] == 2.0
    assert health.json()["decisions"]["wind"] == "average"


def test_marine_current_ingestion_and_circular_health() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Current Buoy"}).json()["id"]
    for channel, direction in (("A", 359.0), ("B", 1.0)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/marine-current",
            json={
                "current_speed_mps": 0.8,
                "current_direction_degrees": direction,
                "sensor_channel": channel,
            },
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["marine_current_speed_delta_mps"] == 0.0
    assert health.json()["marine_current_direction_delta_degrees"] == 2.0
    assert health.json()["decisions"]["marine_current"] == "average"
    assert client.get(f"/api/v1/buoys/{buoy_id}/marine-current").json()[0]["current_speed_mps"] == 0.8
    metrics = client.get("/metrics")
    assert "tidewatch_marine_current_readings_total" in metrics.text


def test_turbidity_ingestion_exposes_latest_ntu() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Turbidity Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/turbidity",
        json={
            "turbidity_ntu": 12.5,
            "sensor_channel": "A",
            "sensor_id": "turbidity-a-01",
            "firmware_version": "2.4.1",
        },
    )

    assert response.status_code == 201
    assert response.json()["turbidity_ntu"] == 12.5
    assert client.get(f"/api/v1/buoys/{buoy_id}/turbidity").json()[0]["turbidity_ntu"] == 12.5
    assert "tidewatch_turbidity_readings_total" in client.get("/metrics").text


def test_sensor_health_compares_redundant_turbidity() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Turbidity Health Buoy"}).json()["id"]
    for channel, turbidity in (("A", 10.0), ("B", 12.5)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/turbidity",
            json={"turbidity_ntu": turbidity, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["turbidity_delta_ntu"] == 2.5
    assert health.json()["decisions"]["turbidity"] == "average"


def test_dissolved_oxygen_ingestion_exposes_latest_concentration() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Dissolved Oxygen Buoy"}
    ).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/dissolved-oxygen",
        json={
            "dissolved_oxygen_mg_l": 7.5,
            "sensor_channel": "A",
            "sensor_id": "dissolved-oxygen-a-01",
            "firmware_version": "2.4.1",
        },
    )

    assert response.status_code == 201
    assert response.json()["dissolved_oxygen_mg_l"] == 7.5
    assert (
        client.get(f"/api/v1/buoys/{buoy_id}/dissolved-oxygen").json()[0][
            "dissolved_oxygen_mg_l"
        ]
        == 7.5
    )
    assert "tidewatch_dissolved_oxygen_readings_total" in client.get(
        "/metrics"
    ).text


def test_sensor_health_compares_redundant_dissolved_oxygen() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Dissolved Oxygen Health Buoy"}
    ).json()["id"]
    for channel, concentration in (("A", 7.0), ("B", 7.5)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/dissolved-oxygen",
            json={
                "dissolved_oxygen_mg_l": concentration,
                "sensor_channel": channel,
            },
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["dissolved_oxygen_delta_mg_l"] == 0.5
    assert health.json()["decisions"]["dissolved_oxygen"] == "average"


def test_ph_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "pH Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/ph",
        json={
            "ph": 8.1,
            "sensor_channel": "A",
            "sensor_id": "ph-a-01",
            "firmware_version": "2.4.1",
        },
    )

    assert response.status_code == 201
    assert response.json()["ph"] == 8.1
    assert client.get(f"/api/v1/buoys/{buoy_id}/ph").json()[0]["ph"] == 8.1
    assert client.get(f"/api/v1/buoys/{buoy_id}/ph").json()[0]["sensor_id"] == "ph-a-01"
    assert "tidewatch_ph_readings_total" in client.get("/metrics").text

    invalid = client.post(f"/api/v1/buoys/{buoy_id}/ph", json={"ph": 15})
    assert invalid.status_code == 422


def test_sensor_health_compares_redundant_ph() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "pH Health Buoy"}).json()["id"]
    for channel, value in (("A", 8.0), ("B", 8.1)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/ph",
            json={"ph": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["ph_delta"] == 0.1
    assert health.json()["decisions"]["ph"] == "average"


def test_conductivity_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Conductivity Buoy"}
    ).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/conductivity",
        json={
            "conductivity_us_cm": 51000,
            "sensor_channel": "A",
            "sensor_id": "conductivity-a-01",
        },
    )

    assert response.status_code == 201
    assert response.json()["conductivity_us_cm"] == 51000
    assert client.get(f"/api/v1/buoys/{buoy_id}/conductivity").json()[0][
        "conductivity_us_cm"
    ] == 51000
    assert "tidewatch_conductivity_readings_total" in client.get("/metrics").text
    invalid = client.post(
        f"/api/v1/buoys/{buoy_id}/conductivity",
        json={"conductivity_us_cm": 200001},
    )
    assert invalid.status_code == 422


def test_sensor_health_compares_redundant_conductivity() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Conductivity Health Buoy"}
    ).json()["id"]
    for channel, value in (("A", 51000), ("B", 52000)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/conductivity",
            json={"conductivity_us_cm": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["conductivity_delta_us_cm"] == 1000
    assert health.json()["decisions"]["conductivity"] == "average"


def test_chlorophyll_a_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Chlorophyll Buoy"}
    ).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/chlorophyll-a",
        json={
            "chlorophyll_a_ug_l": 4.2,
            "sensor_channel": "A",
            "sensor_id": "chlorophyll-a-01",
        },
    )

    assert response.status_code == 201
    assert response.json()["chlorophyll_a_ug_l"] == 4.2
    assert client.get(f"/api/v1/buoys/{buoy_id}/chlorophyll-a").json()[0][
        "chlorophyll_a_ug_l"
    ] == 4.2
    assert "tidewatch_chlorophyll_a_readings_total" in client.get("/metrics").text
    invalid = client.post(
        f"/api/v1/buoys/{buoy_id}/chlorophyll-a",
        json={"chlorophyll_a_ug_l": 1001},
    )
    assert invalid.status_code == 422


def test_rainfall_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Rainfall Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/rainfall",
        json={
            "rainfall_mm_h": 12.5,
            "sensor_channel": "A",
            "sensor_id": "rain-gauge-a-01",
        },
    )

    assert response.status_code == 201
    assert response.json()["rainfall_mm_h"] == 12.5
    assert client.get(f"/api/v1/buoys/{buoy_id}/rainfall").json()[0]["rainfall_mm_h"] == 12.5
    assert "tidewatch_rainfall_readings_total" in client.get("/metrics").text
    invalid = client.post(
        f"/api/v1/buoys/{buoy_id}/rainfall", json={"rainfall_mm_h": 501}
    )
    assert invalid.status_code == 422


def test_humidity_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Humidity Buoy"}).json()["id"]

    response = client.post(
        f"/api/v1/buoys/{buoy_id}/humidity",
        json={
            "humidity_percent": 78.5,
            "sensor_channel": "A",
            "sensor_id": "humidity-a-01",
        },
    )

    assert response.status_code == 201
    assert response.json()["humidity_percent"] == 78.5
    assert client.get(f"/api/v1/buoys/{buoy_id}/humidity").json()[0]["humidity_percent"] == 78.5
    assert "tidewatch_humidity_readings_total" in client.get("/metrics").text
    invalid = client.post(
        f"/api/v1/buoys/{buoy_id}/humidity", json={"humidity_percent": 101}
    )
    assert invalid.status_code == 422


def test_air_temperature_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Air Temperature Buoy"}).json()["id"]
    response = client.post(
        f"/api/v1/buoys/{buoy_id}/air-temperature",
        json={"air_temperature_celsius": 24.5, "sensor_channel": "A", "sensor_id": "air-temp-a-01"},
    )

    assert response.status_code == 201
    assert response.json()["air_temperature_celsius"] == 24.5
    assert client.get(f"/api/v1/buoys/{buoy_id}/air-temperature").json()[0]["air_temperature_celsius"] == 24.5
    assert "tidewatch_air_temperature_readings_total" in client.get("/metrics").text
    invalid = client.post(f"/api/v1/buoys/{buoy_id}/air-temperature", json={"air_temperature_celsius": 61})
    assert invalid.status_code == 422


def test_atmospheric_pressure_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Atmospheric Pressure Buoy"}).json()["id"]
    response = client.post(
        f"/api/v1/buoys/{buoy_id}/atmospheric-pressure",
        json={"atmospheric_pressure_kpa": 101.3, "sensor_channel": "A", "sensor_id": "barometer-a-01"},
    )

    assert response.status_code == 201
    assert response.json()["atmospheric_pressure_kpa"] == 101.3
    assert client.get(f"/api/v1/buoys/{buoy_id}/atmospheric-pressure").json()[0]["atmospheric_pressure_kpa"] == 101.3
    assert "tidewatch_atmospheric_pressure_readings_total" in client.get("/metrics").text
    invalid = client.post(f"/api/v1/buoys/{buoy_id}/atmospheric-pressure", json={"atmospheric_pressure_kpa": 121})
    assert invalid.status_code == 422


def test_sensor_health_compares_redundant_atmospheric_pressure() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Atmospheric Pressure Health Buoy"}).json()["id"]
    for channel, value in (("A", 101.0), ("B", 101.2)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/atmospheric-pressure",
            json={"atmospheric_pressure_kpa": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["atmospheric_pressure_delta_kpa"] == 0.2
    assert health.json()["decisions"]["atmospheric_pressure"] == "average"


def test_acoustic_altimeter_ingestion_exposes_latest_value_and_metrics() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Altimeter Buoy"}).json()["id"]
    response = client.post(
        f"/api/v1/buoys/{buoy_id}/acoustic-altimeter",
        json={"depth_meters": 12.5, "sensor_channel": "A", "sensor_id": "altimeter-a-01"},
    )

    assert response.status_code == 201
    assert response.json()["depth_meters"] == 12.5
    assert client.get(f"/api/v1/buoys/{buoy_id}/acoustic-altimeter").json()[0]["depth_meters"] == 12.5
    assert "tidewatch_acoustic_altimeter_readings_total" in client.get("/metrics").text
    invalid = client.post(f"/api/v1/buoys/{buoy_id}/acoustic-altimeter", json={"depth_meters": -1})
    assert invalid.status_code == 422


def test_sensor_health_compares_redundant_acoustic_altimeter() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Altimeter Health Buoy"}).json()["id"]
    for channel, value in (("A", 12.0), ("B", 12.3)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/acoustic-altimeter",
            json={"depth_meters": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["acoustic_altimeter_delta_meters"] == 0.3
    assert health.json()["decisions"]["acoustic_altimeter"] == "average"


def test_sensor_health_compares_redundant_air_temperature() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Air Temperature Health Buoy"}).json()["id"]
    for channel, value in (("A", 24.0), ("B", 24.3)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/air-temperature",
            json={"air_temperature_celsius": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["air_temperature_delta_celsius"] == 0.3
    assert health.json()["decisions"]["air_temperature"] == "average"


def test_sensor_health_compares_redundant_humidity() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Humidity Health Buoy"}).json()["id"]
    for channel, value in (("A", 75.0), ("B", 78.0)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/humidity",
            json={"humidity_percent": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["humidity_delta_percent"] == 3.0
    assert health.json()["decisions"]["humidity"] == "average"


def test_sensor_health_compares_redundant_rainfall() -> None:
    buoy_id = client.post("/api/v1/buoys", json={"name": "Rainfall Health Buoy"}).json()["id"]
    for channel, value in (("A", 10.0), ("B", 15.0)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/rainfall",
            json={"rainfall_mm_h": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["rainfall_delta_mm_h"] == 5.0
    assert health.json()["decisions"]["rainfall"] == "average"


def test_sensor_health_compares_redundant_chlorophyll_a() -> None:
    buoy_id = client.post(
        "/api/v1/buoys", json={"name": "Chlorophyll Health Buoy"}
    ).json()["id"]
    for channel, value in (("A", 4.0), ("B", 4.8)):
        response = client.post(
            f"/api/v1/buoys/{buoy_id}/chlorophyll-a",
            json={"chlorophyll_a_ug_l": value, "sensor_channel": channel},
        )
        assert response.status_code == 201

    health = client.post(f"/api/v1/buoys/{buoy_id}/sensor-health/check")

    assert health.status_code == 201
    assert health.json()["chlorophyll_a_delta_ug_l"] == 0.8
    assert health.json()["decisions"]["chlorophyll_a"] == "average"


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
