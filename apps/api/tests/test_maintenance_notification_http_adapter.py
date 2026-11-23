from app.adapters.http.maintenance_notifications import (
    HttpxMaintenanceNotificationTransport,
)


def test_httpx_transport_forwards_the_notification_request(monkeypatch) -> None:
    response = object()
    calls = []

    def post(url, *, json, timeout):
        calls.append((url, json, timeout))
        return response

    monkeypatch.setattr("app.adapters.http.maintenance_notifications.httpx.post", post)

    result = HttpxMaintenanceNotificationTransport()(
        "https://example.test/hook",
        json={"source": "tidewatch"},
        timeout=5,
    )

    assert result is response
    assert calls == [("https://example.test/hook", {"source": "tidewatch"}, 5)]
