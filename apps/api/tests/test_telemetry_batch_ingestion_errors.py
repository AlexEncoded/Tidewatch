from datetime import datetime, timezone

import pytest

from app.application.telemetry_batch import TelemetryBatchCommand
from app.application.telemetry_batch_ingestion import (
    TelemetryIdempotencyConflict,
    process_telemetry_batch,
)
from app.domain.telemetry.job import TelemetryJobIdempotencyConflict


def test_batch_use_case_translates_idempotency_conflict_from_job_store() -> None:
    class Gateway:
        def buoy_exists(self, buoy_id):
            return True

        def mark_buoy_seen_by_id(self, buoy_id, seen_at):
            pass

    class UnitOfWork:
        def run_atomically(self, action):
            return action()

    class Metrics:
        def metric(self, name):
            return self

        def labels(self, **labels):
            return self

        def set(self, value):
            pass

    class Jobs:
        def enqueue(self, *args, **kwargs):
            raise TelemetryJobIdempotencyConflict(
                "Idempotency key was already used for another request"
            )

    with pytest.raises(TelemetryIdempotencyConflict, match="another request"):
        process_telemetry_batch(
            "buoy-1",
            TelemetryBatchCommand.from_mapping({}),
            gateway=Gateway(),
            unit_of_work=UnitOfWork(),
            metrics=Metrics(),
            jobs=Jobs(),
            idempotency_key="request-1",
            queued_mode=True,
            clock_observation_at=datetime.now(timezone.utc),
            idempotency_fingerprint="a" * 64,
        )
