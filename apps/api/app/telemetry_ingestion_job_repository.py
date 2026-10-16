"""SQLAlchemy adapter for durable telemetry-ingestion queue state."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .domain.telemetry_job import TelemetryIngestionJobSnapshot
from .entities import TelemetryIngestionJobEntity


class TelemetryIngestionJobRepository:
    """Enqueue, lease, retry and complete telemetry jobs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def enqueue(
        self,
        buoy_id: str,
        payload: dict,
        now: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> TelemetryIngestionJobSnapshot:
        created_at = now or datetime.now(timezone.utc)
        if idempotency_key is not None:
            existing = self._by_idempotency_key(buoy_id, idempotency_key)
            if existing is not None:
                return self._snapshot(existing)
        entity = TelemetryIngestionJobEntity(
            id=uuid4().hex,
            buoy_id=buoy_id,
            idempotency_key=idempotency_key,
            payload=payload,
            status="pending",
            attempts=0,
            available_at=created_at,
            created_at=created_at,
        )
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = (
                self._by_idempotency_key(buoy_id, idempotency_key)
                if idempotency_key is not None
                else None
            )
            if existing is None:
                raise
            return self._snapshot(existing)
        self.db.refresh(entity)
        return self._snapshot(entity)

    def get(self, job_id: str) -> TelemetryIngestionJobSnapshot | None:
        entity = self.db.get(TelemetryIngestionJobEntity, job_id)
        return self._snapshot(entity) if entity is not None else None

    def _by_idempotency_key(
        self, buoy_id: str, idempotency_key: str
    ) -> TelemetryIngestionJobEntity | None:
        return self.db.scalars(
            select(TelemetryIngestionJobEntity).where(
                TelemetryIngestionJobEntity.buoy_id == buoy_id,
                TelemetryIngestionJobEntity.idempotency_key == idempotency_key,
            )
        ).first()

    def claim_next(
        self, now: datetime, lease_seconds: int, max_attempts: int = 5
    ) -> TelemetryIngestionJobSnapshot | None:
        if lease_seconds <= 0:
            raise ValueError("Job lease must be greater than zero seconds")
        if max_attempts <= 0:
            raise ValueError("Maximum job attempts must be greater than zero")

        exhausted_jobs = self.db.scalars(
            select(TelemetryIngestionJobEntity)
            .where(
                TelemetryIngestionJobEntity.status == "processing",
                TelemetryIngestionJobEntity.lease_expires_at <= now,
                TelemetryIngestionJobEntity.attempts >= max_attempts,
            )
            .with_for_update(skip_locked=True)
        ).all()
        for expired in exhausted_jobs:
            expired.status = "failed"
            expired.lease_expires_at = None
            expired.last_error = "Worker lease expired after maximum attempts"
        if exhausted_jobs:
            self.db.commit()

        eligible = or_(
            and_(
                TelemetryIngestionJobEntity.status == "pending",
                TelemetryIngestionJobEntity.available_at <= now,
            ),
            and_(
                TelemetryIngestionJobEntity.status == "processing",
                TelemetryIngestionJobEntity.lease_expires_at <= now,
                TelemetryIngestionJobEntity.attempts < max_attempts,
            ),
        )
        entity = self.db.scalars(
            select(TelemetryIngestionJobEntity)
            .where(eligible)
            .order_by(TelemetryIngestionJobEntity.created_at, TelemetryIngestionJobEntity.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).first()
        if entity is None:
            return None

        entity.status = "processing"
        entity.attempts += 1
        entity.started_at = now
        entity.lease_expires_at = now + timedelta(seconds=lease_seconds)
        self.db.commit()
        self.db.refresh(entity)
        return self._snapshot(entity)

    def renew_lease(
        self, job_id: str, attempt: int, now: datetime, lease_seconds: int
    ) -> TelemetryIngestionJobSnapshot | None:
        if lease_seconds <= 0:
            raise ValueError("Job lease must be greater than zero seconds")
        entity = self._lock_processing_job(job_id, attempt, now)
        if entity is None:
            return None
        entity.lease_expires_at = now + timedelta(seconds=lease_seconds)
        self.db.commit()
        self.db.refresh(entity)
        return self._snapshot(entity)

    def complete(
        self, job_id: str, attempt: int, now: datetime
    ) -> TelemetryIngestionJobSnapshot | None:
        entity = self._lock_processing_job(job_id, attempt, now)
        if entity is None:
            return None
        entity.status = "completed"
        entity.completed_at = now
        entity.lease_expires_at = None
        entity.last_error = None
        self.db.commit()
        self.db.refresh(entity)
        return self._snapshot(entity)

    def fail(
        self,
        job_id: str,
        attempt: int,
        error: str,
        now: datetime,
        max_attempts: int,
        retry_delay_seconds: int,
    ) -> TelemetryIngestionJobSnapshot | None:
        if max_attempts <= 0 or retry_delay_seconds < 0:
            raise ValueError("Retry attempts must be positive and delay cannot be negative")
        entity = self._lock_processing_job(job_id, attempt, now)
        if entity is None:
            return None

        entity.last_error = error[:1000]
        entity.lease_expires_at = None
        if entity.attempts >= max_attempts:
            entity.status = "failed"
        else:
            entity.status = "pending"
            entity.available_at = now + timedelta(seconds=retry_delay_seconds)
        self.db.commit()
        self.db.refresh(entity)
        return self._snapshot(entity)

    def _lock_processing_job(
        self, job_id: str, attempt: int, now: datetime
    ) -> TelemetryIngestionJobEntity | None:
        entity = self.db.scalars(
            select(TelemetryIngestionJobEntity)
            .where(
                TelemetryIngestionJobEntity.id == job_id,
                TelemetryIngestionJobEntity.status == "processing",
                TelemetryIngestionJobEntity.attempts == attempt,
                TelemetryIngestionJobEntity.lease_expires_at > now,
            )
            .with_for_update()
        ).first()
        return entity

    @staticmethod
    def _snapshot(
        entity: TelemetryIngestionJobEntity,
    ) -> TelemetryIngestionJobSnapshot:
        return TelemetryIngestionJobSnapshot(
            job_id=entity.id,
            buoy_id=entity.buoy_id,
            idempotency_key=entity.idempotency_key,
            payload=entity.payload,
            status=entity.status,
            attempts=entity.attempts,
            available_at=entity.available_at,
            created_at=entity.created_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            lease_expires_at=entity.lease_expires_at,
            last_error=entity.last_error,
        )
