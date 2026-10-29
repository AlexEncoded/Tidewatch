from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

from app.domain.wave import estimate_fused_wave_period
from app.schemas.ingestion import TelemetryBatchCreate


SIMULATOR_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "telemetry_simulator.py"
)
SPEC = importlib.util.spec_from_file_location("tidewatch_telemetry_simulator", SIMULATOR_PATH)
SIMULATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SIMULATOR)


def test_simulator_builds_synchronized_per_device_payloads() -> None:
    devices = {
        "A": {"device_id": "physical-unit-a", "sensor_channel": "A"},
        "B": {"device_id": "physical-unit-b", "sensor_channel": "B"},
    }

    payloads = SIMULATOR.build_payloads(devices)

    assert set(payloads) == {"A", "B"}
    assert payloads["A"]["device_id"] == "physical-unit-a"
    assert payloads["B"]["device_id"] == "physical-unit-b"
    for channel, payload in payloads.items():
        batch = TelemetryBatchCreate.model_validate(payload)
        assert batch.device_id == devices[channel]["device_id"]
        assert batch.location is not None
        assert batch.location.device_id == devices[channel]["device_id"]
        assert batch.location.measured_at == batch.temperatures[0].measured_at
        assert -90 <= batch.location.latitude <= 90
        assert -180 <= batch.location.longitude <= 180
        assert batch.location.satellites >= 4
        assert payload["temperatures"][0]["sensor_channel"] == channel
        assert payload["air_temperature"][0]["sensor_channel"] == channel
        assert -60 <= payload["air_temperature"][0]["air_temperature_celsius"] <= 60
        assert payload["pressures"][0]["sensor_channel"] == channel
        assert payload["atmospheric_pressure"][0]["sensor_channel"] == channel
        assert 80 <= payload["atmospheric_pressure"][0]["atmospheric_pressure_kpa"] <= 120
        assert payload["acoustic_altimeter"][0]["sensor_channel"] == channel
        assert 0 <= payload["acoustic_altimeter"][0]["depth_meters"] <= 20_000
        assert payload["underwater_acoustic"][0]["sensor_channel"] == channel
        assert -200 <= payload["underwater_acoustic"][0]["echo_intensity_db"] <= 100
        assert payload["salinity"][0]["sensor_channel"] == channel
        assert payload["ambient_light"][0]["sensor_channel"] == channel
        assert 0 <= payload["ambient_light"][0]["illuminance_lux"] <= 150_000
        assert payload["wind"][0]["sensor_channel"] == channel
        assert 0 <= payload["wind"][0]["wind_speed_mps"] <= 100
        assert 0 <= payload["wind"][0]["wind_direction_degrees"] < 360
        assert payload["marine_current"][0]["sensor_channel"] == channel
        assert 0 <= payload["marine_current"][0]["current_speed_mps"] <= 20
        assert 0 <= payload["marine_current"][0]["current_direction_degrees"] < 360
        assert payload["turbidity"][0]["sensor_channel"] == channel
        assert 0 <= payload["turbidity"][0]["turbidity_ntu"] <= 5000
        assert payload["dissolved_oxygen"][0]["sensor_channel"] == channel
        assert 0 <= payload["dissolved_oxygen"][0]["dissolved_oxygen_mg_l"] <= 20
        assert payload["ph"][0]["sensor_channel"] == channel
        assert 0 <= payload["ph"][0]["ph"] <= 14
        assert payload["conductivity"][0]["sensor_channel"] == channel
        assert 0 <= payload["conductivity"][0]["conductivity_us_cm"] <= 200_000
        assert payload["chlorophyll_a"][0]["sensor_channel"] == channel
        assert 0 <= payload["chlorophyll_a"][0]["chlorophyll_a_ug_l"] <= 1000
        assert payload["rainfall"][0]["sensor_channel"] == channel
        assert 0 <= payload["rainfall"][0]["rainfall_mm_h"] <= 500
        assert payload["humidity"][0]["sensor_channel"] == channel
        assert 0 <= payload["humidity"][0]["humidity_percent"] <= 100
        assert payload["imu"][0]["sensor_channel"] == channel
        assert payload["imu"][0]["measured_at"] == payload["temperatures"][0]["measured_at"]
        assert payload["battery"][0]["device_id"] == channel
        assert payload["battery"][0]["physical_device_id"] == devices[channel]["device_id"]
        assert payload["device_runtime"]["cpu_usage_percent"] <= 100
        assert -200 <= payload["imu"][0]["acceleration_z_mps2"] <= 200
        assert -150 <= payload["device_communications"]["signal_strength_dbm"] <= 0
        assert payload["device_communications"]["signal_to_noise_ratio_db"] >= -30

    timestamps = {
        payload["temperatures"][0]["measured_at"] for payload in payloads.values()
    }
    assert len(timestamps) == 1


def test_simulator_populates_and_synchronizes_every_batch_field() -> None:
    devices = {
        "A": {"device_id": "physical-unit-a", "sensor_channel": "A"},
        "B": {"device_id": "physical-unit-b", "sensor_channel": "B"},
    }
    payloads = SIMULATOR.build_payloads(devices)
    expected_fields = set(TelemetryBatchCreate.model_fields)

    for channel, payload in payloads.items():
        assert set(payload) == expected_fields
        measured_at = payload["location"]["measured_at"]
        for field, value in payload.items():
            if isinstance(value, list):
                assert value
                for reading in value:
                    assert reading["measured_at"] == measured_at
                    if "sensor_channel" in reading:
                        assert reading["sensor_channel"] == channel
                    elif field == "battery":
                        assert reading["device_id"] == channel
            elif isinstance(value, dict):
                assert value["measured_at"] == measured_at


def test_simulator_wave_altitude_and_imu_share_a_reproducible_period() -> None:
    devices = {"A": {"device_id": "physical-unit-a", "sensor_channel": "A"}}
    origin = datetime.fromtimestamp(0, timezone.utc)
    offsets = (0.0, 7.5, 15.0, 22.5, 30.0)

    payloads = [
        SIMULATOR.build_payloads(devices, origin + timedelta(seconds=offset))["A"]
        for offset in offsets
    ]
    altitudes = [payload["location"]["altitude_meters"] for payload in payloads]
    vertical_accelerations = [
        payload["imu"][0]["acceleration_z_mps2"] for payload in payloads
    ]

    assert altitudes == [2.0, 2.2, 2.0, 1.8, 2.0]
    assert vertical_accelerations[1] < 9.81 < vertical_accelerations[3]
    assert vertical_accelerations[0] == vertical_accelerations[2] == 9.81
    assert round(vertical_accelerations[1] + vertical_accelerations[3], 4) == 19.62


def test_simulated_gnss_and_imu_fuse_to_the_configured_wave_period() -> None:
    devices = {"A": {"device_id": "physical-unit-a", "sensor_channel": "A"}}
    origin = datetime.fromtimestamp(0, timezone.utc)
    gnss_samples = []
    imu_samples = []

    for offset in range(0, 151, 10):
        measured_at = origin + timedelta(seconds=offset)
        payload = SIMULATOR.build_payloads(devices, measured_at)["A"]
        gnss_samples.append((measured_at, payload["location"]["altitude_meters"]))
        imu_samples.append((measured_at, payload["imu"][0]["acceleration_z_mps2"]))

    estimate = estimate_fused_wave_period(gnss_samples, imu_samples)

    assert estimate.estimated_period_seconds == SIMULATOR.SIMULATED_WAVE_PERIOD_SECONDS
    assert estimate.confidence == "experimental"


def test_simulator_registers_missing_redundant_devices(monkeypatch) -> None:
    calls = []

    def fake_request_json(url, method, payload=None):
        calls.append((method, payload))
        if method == "GET":
            return []
        return {
            "device_id": payload["device_id"],
            "sensor_channel": payload["sensor_channel"],
        }

    monkeypatch.setattr(SIMULATOR, "request_json", fake_request_json)
    devices = SIMULATOR.ensure_simulator_devices("http://api", "buoy-1")

    assert devices["A"]["device_id"] == "sim-buoy-1-A"
    assert devices["B"]["device_id"] == "sim-buoy-1-B"
    assert [method for method, _ in calls] == ["GET", "POST", "POST"]


def test_simulator_creates_buoy_at_simulated_gnss_origin(monkeypatch) -> None:
    requests = []

    def fake_request_json(url, method, payload=None):
        requests.append((url, method, payload))
        return {"id": "buoy-1"}

    monkeypatch.setattr(SIMULATOR, "request_json", fake_request_json)

    buoy_id = SIMULATOR.create_buoy("http://api", "Test Buoy")

    assert buoy_id == "buoy-1"
    assert requests[0][2] == {
        "name": "Test Buoy",
        "latitude": SIMULATOR.SIMULATED_LATITUDE,
        "longitude": SIMULATOR.SIMULATED_LONGITUDE,
    }


def test_simulator_reuses_devices_already_registered(monkeypatch) -> None:
    registered = [
        {"device_id": "existing-a", "sensor_channel": "A"},
        {"device_id": "existing-b", "sensor_channel": "B"},
    ]
    calls = []

    def fake_request_json(url, method, payload=None):
        calls.append(method)
        return registered

    monkeypatch.setattr(SIMULATOR, "request_json", fake_request_json)
    devices = SIMULATOR.ensure_simulator_devices("http://api", "buoy-1")

    assert devices == {"A": registered[0], "B": registered[1]}
    assert calls == ["GET"]
