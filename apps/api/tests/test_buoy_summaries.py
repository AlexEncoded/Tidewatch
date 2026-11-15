from app.application.buoy_summaries import list_buoy_summaries


def test_buoy_summary_query_returns_snapshots_from_reader_port() -> None:
    snapshots = [object(), object()]

    class Reader:
        def list_buoy_summaries(self):
            return snapshots

    assert list_buoy_summaries(Reader()) is snapshots
