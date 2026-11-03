from app import prometheus_http_request_metrics as adapter_module
from app.prometheus_http_request_metrics import PrometheusHttpRequestMetrics


class FakeSample:
    def __init__(self, action: str, labels: dict[str, str], calls: list[tuple]) -> None:
        self.action = action
        self.labels = labels
        self.calls = calls

    def inc(self) -> None:
        self.calls.append((self.action, self.labels))

    def observe(self, value: float) -> None:
        self.calls.append((self.action, self.labels, value))


class FakeInstrument:
    def __init__(self, action: str, calls: list[tuple]) -> None:
        self.action = action
        self.calls = calls

    def labels(self, **labels: str) -> FakeSample:
        return FakeSample(self.action, labels, self.calls)


def test_http_metrics_adapter_records_count_and_duration(monkeypatch) -> None:
    calls: list[tuple] = []
    monkeypatch.setattr(
        adapter_module, "http_requests_total", FakeInstrument("increment", calls)
    )
    monkeypatch.setattr(
        adapter_module,
        "http_request_duration_seconds",
        FakeInstrument("observe", calls),
    )

    PrometheusHttpRequestMetrics().record_request("POST", 201, 0.125)

    assert calls == [
        ("increment", {"method": "POST", "status_code": "201"}),
        ("observe", {"method": "POST"}, 0.125),
    ]
