import importlib.util
from pathlib import Path

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
        assert payload["temperatures"][0]["sensor_channel"] == channel
        assert payload["pressures"][0]["sensor_channel"] == channel
        assert payload["salinity"][0]["sensor_channel"] == channel
        assert payload["battery"][0]["device_id"] == channel
        assert payload["battery"][0]["physical_device_id"] == devices[channel]["device_id"]
        assert payload["device_runtime"]["cpu_usage_percent"] <= 100
        assert -150 <= payload["device_communications"]["signal_strength_dbm"] <= 0
        assert payload["device_communications"]["signal_to_noise_ratio_db"] >= -30

    timestamps = {
        payload["temperatures"][0]["measured_at"] for payload in payloads.values()
    }
    assert len(timestamps) == 1


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
