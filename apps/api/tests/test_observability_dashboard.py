import json
from pathlib import Path


def test_device_radio_metrics_are_visible_in_grafana_dashboard() -> None:
    dashboard_path = (
        Path(__file__).resolve().parents[3]
        / "observability"
        / "grafana"
        / "dashboards"
        / "tidewatch-overview.json"
    )
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard["panels"]
    panel_ids = [panel["id"] for panel in panels]
    panel_targets = {
        target["expr"]
        for panel in panels
        for target in panel.get("targets", [])
    }

    assert len(panel_ids) == len(set(panel_ids))
    assert "tidewatch_device_signal_strength_dbm" in panel_targets
    assert "tidewatch_device_signal_to_noise_ratio_db" in panel_targets
