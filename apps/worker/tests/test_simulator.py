import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import simulator


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.request = httpx.Request("POST", "http://api.test/telemetry")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status {self.status_code}",
                request=self.request,
                response=self,
            )


class FakeClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls = 0

    def post(self, *_args, **_kwargs) -> FakeResponse:
        response = self.responses[self.calls]
        self.calls += 1
        return response


def test_send_telemetry_retries_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient([FakeResponse(503), FakeResponse(202)])
    monkeypatch.setattr(simulator, "TELEMETRY_RETRIES", 1)
    monkeypatch.setattr(simulator.time, "sleep", lambda _seconds: None)

    simulator.send_telemetry(client, "TW-TEST", {"temperatures": []})

    assert client.calls == 2


def test_send_telemetry_does_not_retry_client_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient([FakeResponse(422), FakeResponse(202)])
    monkeypatch.setattr(simulator, "TELEMETRY_RETRIES", 1)

    with pytest.raises(httpx.HTTPStatusError):
        simulator.send_telemetry(client, "TW-TEST", {"temperatures": []})

    assert client.calls == 1


def test_battery_reading_discharges_one_device(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(simulator.random, "uniform", lambda _minimum, _maximum: 0.03)

    assert simulator.battery_reading(100) == 99.97


def test_imu_reading_stays_within_calm_buoy_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        simulator.random,
        "uniform",
        lambda minimum, maximum: (minimum + maximum) / 2,
    )

    reading = simulator.imu_reading()

    assert set(reading) == {
        "acceleration_x_mps2",
        "acceleration_y_mps2",
        "acceleration_z_mps2",
        "angular_velocity_x_dps",
        "angular_velocity_y_dps",
        "angular_velocity_z_dps",
    }
    assert reading["acceleration_z_mps2"] == 9.8
    assert abs(reading["angular_velocity_z_dps"]) <= 2


def test_ambient_light_reading_stays_within_sensor_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(simulator.random, "uniform", lambda _minimum, _maximum: 50)

    assert simulator.ambient_light_reading(1000) == 1050
    assert simulator.ambient_light_reading(149999.9) <= 150000


def test_wind_reading_wraps_direction_and_bounds_speed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(simulator.random, "uniform", lambda _minimum, _maximum: 0.5)

    reading = simulator.wind_reading(99.9, 359.8)

    assert reading["wind_speed_mps"] == 100
    assert reading["wind_direction_degrees"] == 0.3


def test_marine_current_reading_stays_within_sensor_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(simulator.random, "uniform", lambda _minimum, _maximum: 0.04)

    reading = simulator.marine_current_reading(19.99, 359.9)

    assert reading["current_speed_mps"] == 20
    assert reading["current_direction_degrees"] == 0.04
