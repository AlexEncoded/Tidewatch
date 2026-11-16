from app.application.telemetry_job_queries import get_telemetry_job


def test_telemetry_job_query_delegates_to_store_port() -> None:
    expected = object()

    class Store:
        def get(self, job_id):
            assert job_id == "job-1"
            return expected

    assert get_telemetry_job(Store(), "job-1") is expected


def test_telemetry_job_query_preserves_missing_result() -> None:
    class Store:
        def get(self, job_id):
            return None

    assert get_telemetry_job(Store(), "missing") is None
