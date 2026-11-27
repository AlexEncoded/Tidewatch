from datetime import datetime, timezone

from app.domain.maintenance.temperature_alert import build_temperature_anomaly


def test_temperature_anomaly_builder_preserves_zero_average():
    created_at = datetime(2026, 10, 31, tzinfo=timezone.utc)

    anomaly = build_temperature_anomaly(
        "buoy-1", "North buoy", True, 10.0, 0.0, "Temperature spike", created_at
    )

    assert anomaly is not None
    assert anomaly.severity == "warning"
    assert anomaly.temperature_celsius == 10.0
    assert anomaly.average_temperature == 0.0
    assert anomaly.created_at == created_at
    assert anomaly.message == "Temperature spike"


def test_temperature_anomaly_builder_omits_non_anomalous_or_incomplete_analysis():
    assert (
        build_temperature_anomaly(
            "buoy-1",
            "North buoy",
            False,
            20.0,
            20.0,
            None,
            datetime(2026, 10, 31, tzinfo=timezone.utc),
        )
        is None
    )
