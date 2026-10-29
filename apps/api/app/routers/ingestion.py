"""HTTP route for batch telemetry ingestion."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from ..adapter_dependencies import (
    get_telemetry_metrics,
    get_telemetry_ingestion_gateway,
    get_telemetry_ingestion_job_repository,
    get_telemetry_batch_unit_of_work,
)
from ..application.telemetry_ports import (
    TelemetryBatchUnitOfWork,
    TelemetryIngestionGateway,
    TelemetryIngestionJobStore,
    TelemetryMetrics,
)
from ..application.telemetry_batch import TelemetryBatchCommand
from ..application.telemetry_batch_ingestion import (
    TelemetryBatchInvalid,
    TelemetryBuoyNotFound,
    TelemetryDeviceNotFound,
    TelemetryIngestOutcome,
    TelemetryQueuedOutcome,
    process_telemetry_batch,
)
from ..schemas.ingestion import TelemetryBatchCreate
from ..schemas.telemetry import TelemetryIngestResponse
from ..schemas.telemetry_job import (
    TelemetryJobAcceptedResponse,
    TelemetryJobStatusResponse,
)
from ..settings import telemetry_ingestion_is_queued


router = APIRouter()


@router.post(
    "/api/v1/buoys/{buoy_id}/telemetry",
    response_model=TelemetryIngestResponse | TelemetryJobAcceptedResponse,
    status_code=status.HTTP_200_OK,
    tags=["telemetry"],
)
def ingest_telemetry(
    buoy_id: str,
    payload: TelemetryBatchCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, min_length=1, max_length=64),
    gateway: TelemetryIngestionGateway = Depends(get_telemetry_ingestion_gateway),
    unit_of_work: TelemetryBatchUnitOfWork = Depends(get_telemetry_batch_unit_of_work),
    jobs: TelemetryIngestionJobStore | None = Depends(
        get_telemetry_ingestion_job_repository
    ),
    metrics: TelemetryMetrics = Depends(get_telemetry_metrics),
) -> TelemetryIngestResponse | TelemetryJobAcceptedResponse:
    queued_mode = telemetry_ingestion_is_queued()
    command = TelemetryBatchCommand.from_mapping(payload.model_dump())
    received_at = datetime.now(timezone.utc)
    try:
        outcome = process_telemetry_batch(
            buoy_id,
            command,
            gateway=gateway,
            unit_of_work=unit_of_work,
            metrics=metrics,
            jobs=jobs,
            idempotency_key=idempotency_key,
            queued_mode=queued_mode,
            clock_observation_at=received_at,
        )
    except TelemetryBuoyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    except TelemetryDeviceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    except TelemetryBatchInvalid as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from None

    if isinstance(outcome, TelemetryQueuedOutcome):
        response.status_code = status.HTTP_202_ACCEPTED
        response.headers["Location"] = outcome.status_url
        return TelemetryJobAcceptedResponse(
            job_id=outcome.job_id, status="pending", status_url=outcome.status_url
        )
    assert isinstance(outcome, TelemetryIngestOutcome)
    return TelemetryIngestResponse(
        buoy_id=outcome.buoy_id,
        accepted_readings=outcome.accepted_readings,
        accepted_by_family=outcome.accepted_by_family,
    )


@router.get(
    "/api/v1/telemetry/jobs/{job_id}",
    response_model=TelemetryJobStatusResponse,
    tags=["telemetry"],
)
def get_telemetry_job_status(
    job_id: str,
    jobs: TelemetryIngestionJobStore = Depends(
        get_telemetry_ingestion_job_repository
    ),
) -> TelemetryJobStatusResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Telemetry job not found"
        )
    return TelemetryJobStatusResponse(
        job_id=job.job_id,
        buoy_id=job.buoy_id,
        status=job.status,
        attempts=job.attempts,
        available_at=job.available_at,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error="processing_failed" if job.status == "failed" else None,
    )
