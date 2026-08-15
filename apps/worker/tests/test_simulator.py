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
