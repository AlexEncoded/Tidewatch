"""HTTPX outbound adapter for maintenance notification delivery."""

import httpx


class HttpxMaintenanceNotificationTransport:
    """Send notification payloads over HTTP using HTTPX."""

    def __call__(self, url: str, *, json: dict, timeout: float) -> httpx.Response:
        return httpx.post(url, json=json, timeout=timeout)
