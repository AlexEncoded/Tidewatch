"""SQLAlchemy adapter for durable telemetry-ingestion queue state."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .domain.telemetry_job import TelemetryIngestionJobSnapshot
from .entities import TelemetryIngestionJobEntity
from .application.telemetry_queue_metrics import TelemetryQueueMetricsUnavailable


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

    def observability_snapshot(
        self, now: datetime | None = None
    ) -> dict[str, int | float]:
        """Return bounded-cardinality queue counts and oldest/expired work ages."""
        try:
            return self._observability_snapshot(now)
        except SQLAlchemyError as exc:
            try:
                self.db.rollback()
            except SQLAlchemyError:
                # Preserve the application-level failure even if the broken
                # connection also prevents cleanup. The request-scoped session
                # will be discarded by its dependency lifecycle.
                pass
            raise TelemetryQueueMetricsUnavailable(
                "Telemetry queue metrics are unavailable"
            ) from exc

    def _observability_snapshot(
        self, now: datetime | None = None
    ) -> dict[str, int | float]:
        observed_at = now or datetime.now(timezone.utc)
        counts = {
            status: count
            for status, count in self.db.execute(
                select(
                    TelemetryIngestionJobEntity.status,
                    func.count(TelemetryIngestionJobEntity.id),
                ).group_by(TelemetryIngestionJobEntity.status)
            ).all()
        }
        attempts_by_status = {
            status: attempts
            for status, attempts in self.db.execute(
                select(
                    TelemetryIngestionJobEntity.status,
                    func.coalesce(func.sum(TelemetryIngestionJobEntity.attempts), 0),
                ).group_by(TelemetryIngestionJobEntity.status)
            ).all()
        }
        retried_jobs = self.db.scalar(
            select(func.count(TelemetryIngestionJobEntity.id)).where(
                TelemetryIngestionJobEntity.attempts > 1
            )
        )
        oldest_pending = self.db.scalar(
            select(func.min(TelemetryIngestionJobEntity.created_at)).where(
                TelemetryIngestionJobEntity.status == "pending"
            )
        )
        expired_leases = self.db.scalar(
            select(func.count(TelemetryIngestionJobEntity.id)).where(
                TelemetryIngestionJobEntity.status == "processing",
                TelemetryIngestionJobEntity.lease_expires_at <= observed_at,
            )
        )
        if oldest_pending is not None:
            if oldest_pending.tzinfo is None:
                oldest_pending = oldest_pending.replace(tzinfo=timezone.utc)
            oldest_pending_age = max(
                0.0, (observed_at - oldest_pending).total_seconds()
            )
        else:
            oldest_pending_age = 0.0
        return {
            **{status: counts.get(status, 0) for status in ("pending", "processing", "completed", "failed")},
            **{
                f"{status}_attempts": attempts_by_status.get(status, 0)
                for status in ("pending", "processing", "completed", "failed")
            },
            "retried_jobs": retried_jobs or 0,
            "oldest_pending_seconds": oldest_pending_age,
            "expired_leases": expired_leases or 0,
        }

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
