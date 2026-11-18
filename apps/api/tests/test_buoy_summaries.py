from datetime import datetime, timezone
from types import SimpleNamespace

from app.application.buoy_summaries import list_buoy_summaries
from app.domain.buoy import BuoySnapshot, BuoySummarySnapshot


def test_buoy_summary_query_returns_snapshots_from_reader_port() -> None:
    buoy = BuoySnapshot(
        "buoy-1", "North buoy", None, None, "active", None, datetime.now(timezone.utc)
    )
    channel_a = SimpleNamespace(sensor_channel="A", quality="suspect")
    channel_b = SimpleNamespace(sensor_channel="B", quality="good")
    snapshots = [
        BuoySummarySnapshot(
            buoy=buoy,
            latest_readings={
                "temperature": {
                    "latest": channel_a,
                    "A": channel_a,
                    "B": channel_b,
                }
            },
        )
    ]

    class Reader:
        def list_buoy_summaries(self):
            return snapshots

    result = list_buoy_summaries(Reader())

    assert result is not snapshots
    assert result[0].buoy is buoy
    assert result[0].latest_readings["temperature"]["latest"] is channel_b
    assert result[0].latest_readings["temperature"]["A"] is channel_a
    assert result[0].latest_readings["temperature"]["B"] is channel_b
