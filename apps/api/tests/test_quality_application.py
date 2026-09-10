from app.application.quality_summary import summarize_quality


class FakeQualityReader:
    def quality_counts(self, buoy_id: str) -> dict[str, int]:
        assert buoy_id == "buoy-1"
        return {"good": 7, "suspect": 2, "invalid": 1}


def test_quality_summary_is_built_through_reader_port() -> None:
    summary = summarize_quality(FakeQualityReader(), "buoy-1")

    assert summary.buoy_id == "buoy-1"
    assert summary.total_readings == 10
    assert summary.good_readings == 7
    assert summary.suspect_readings == 2
    assert summary.invalid_readings == 1
