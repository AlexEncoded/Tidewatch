from app import prometheus_metrics_scraper as adapter_module
from app.prometheus_metrics_scraper import PrometheusMetricsScraper


def test_prometheus_metrics_scraper_returns_exposition_and_content_type(monkeypatch) -> None:
    expected_payload = b"# HELP tidewatch_test_metric test\n"
    monkeypatch.setattr(adapter_module, "generate_latest", lambda: expected_payload)
    monkeypatch.setattr(adapter_module, "CONTENT_TYPE_LATEST", "text/test-metrics")

    scraper = PrometheusMetricsScraper()

    assert scraper.render() == expected_payload
    assert scraper.content_type == "text/test-metrics"
