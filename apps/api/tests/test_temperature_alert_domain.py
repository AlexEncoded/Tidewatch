from datetime import datetime, timezone

from app.domain.temperature import TemperatureAnalysisSnapshot
from app.domain.temperature_alert import build_temperature_anomaly


def test_temperature_anomaly_builder_preserves_zero_average():
    analysis = TemperatureAnalysisSnapshot(
        buoy_id="buoy-1",
        sample_count=3,
        latest_temperature=10.0,
        average_temperature=0.0,
        is_anomaly=True,
        anomaly_reason="Temperature spike",
    )
    created_at = datetime(2026, 10, 31, tzinfo=timezone.utc)

    anomaly = build_temperature_anomaly("buoy-1", "North buoy", analysis, created_at)

    assert anomaly is not None
    assert anomaly.severity == "warning"
    assert anomaly.temperature_celsius == 10.0
    assert anomaly.average_temperature == 0.0
    assert anomaly.created_at == created_at
    assert anomaly.message == "Temperature spike"


def test_temperature_anomaly_builder_omits_non_anomalous_or_incomplete_analysis():
    analysis = TemperatureAnalysisSnapshot(
        buoy_id="buoy-1",
        sample_count=1,
        latest_temperature=20.0,
        average_temperature=20.0,
    )

    assert (
        build_temperature_anomaly(
            "buoy-1",
            "North buoy",
            analysis,
            datetime(2026, 10, 31, tzinfo=timezone.utc),
        )
        is None
    )
