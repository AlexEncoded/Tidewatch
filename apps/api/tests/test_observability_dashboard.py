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


def test_wave_gnss_rejection_metrics_are_visible_in_grafana_dashboard() -> None:
    dashboard_path = (
        Path(__file__).resolve().parents[3]
        / "observability"
        / "grafana"
        / "dashboards"
        / "tidewatch-overview.json"
    )
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard["panels"]
    panel = next(
        panel
        for panel in panels
        if panel["title"] == "GNSS fixes rejected by wave analysis"
    )

    assert panel["targets"][0]["expr"] == "tidewatch_wave_analysis_rejected_gnss_samples"
    assert panel["targets"][0]["legendFormat"] == "{{buoy_id}} / {{reason}}"
    rate_panel = next(
        panel
        for panel in panels
        if panel["title"] == "GNSS rejection rate in wave analysis"
    )
    assert "tidewatch_wave_analysis_gnss_quality_eligible_samples" in rate_panel[
        "targets"
    ][0]["expr"]
