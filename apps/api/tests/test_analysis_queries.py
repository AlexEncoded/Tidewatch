from app.application.analysis_queries import analyze_if_buoy_exists


def test_analysis_query_runs_for_existing_buoy() -> None:
    class Reader:
        def buoy_exists(self, buoy_id: str) -> bool:
            assert buoy_id == "buoy-1"
            return True

    result = analyze_if_buoy_exists(
        Reader(), "buoy-1", lambda: {"sample_count": 3}
    )

    assert result == {"sample_count": 3}


def test_analysis_query_skips_work_for_unknown_buoy() -> None:
    class Reader:
        def buoy_exists(self, buoy_id: str) -> bool:
            return False

    def analyze() -> object:
        raise AssertionError("unknown buoy must not run analysis")

    assert analyze_if_buoy_exists(Reader(), "missing", analyze) is None
