"""SQLAlchemy adapter for the durable maintenance notification outbox."""

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .domain.maintenance_notification_job import MaintenanceNotificationJob
from .maintenance_entities import MaintenanceNotificationJobEntity


class MaintenanceNotificationIdempotencyConflict(ValueError):
    """An idempotency key was reused for a different notification payload."""


class MaintenanceNotificationJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def enqueue(
        self,
        idempotency_key: str,
        payload: dict,
        issue_count: int,
        now: datetime,
    ) -> MaintenanceNotificationJob:
        existing = self._by_key(idempotency_key)
        if existing is not None:
            if existing.payload != payload:
                raise MaintenanceNotificationIdempotencyConflict(
                    "Idempotency-Key was already used with a different notification"
                )
            return self._snapshot(existing)

        entity = MaintenanceNotificationJobEntity(
            id=uuid4().hex,
            idempotency_key=idempotency_key,
            payload=payload,
            issue_count=issue_count,
            status="pending",
            attempts=0,
            available_at=now,
            created_at=now,
        )
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self._by_key(idempotency_key)
            if existing is None:
                raise
            if existing.payload != payload:
                raise MaintenanceNotificationIdempotencyConflict(
                    "Idempotency-Key was already used with a different notification"
                ) from None
            return self._snapshot(existing)
        self.db.refresh(entity)
        return self._snapshot(entity)

    def get(self, job_id: str) -> MaintenanceNotificationJob | None:
        entity = self.db.get(MaintenanceNotificationJobEntity, job_id)
        return self._snapshot(entity) if entity is not None else None

    def claim_next(
        self, now: datetime, lease_seconds: int, max_attempts: int
    ) -> MaintenanceNotificationJob | None:
        if lease_seconds <= 0 or max_attempts <= 0:
            raise ValueError("Lease and maximum attempts must be greater than zero")

        exhausted = self.db.scalars(
            select(MaintenanceNotificationJobEntity)
            .where(
                MaintenanceNotificationJobEntity.status == "processing",
                MaintenanceNotificationJobEntity.lease_expires_at <= now,
                MaintenanceNotificationJobEntity.attempts >= max_attempts,
            )
            .with_for_update(skip_locked=True)
        ).all()
        for entity in exhausted:
            entity.status = "failed"
            entity.lease_expires_at = None
            entity.last_error = "worker_lease_expired"
        if exhausted:
            self.db.commit()

        eligible = or_(
            and_(
                MaintenanceNotificationJobEntity.status == "pending",
                MaintenanceNotificationJobEntity.available_at <= now,
            ),
            and_(
                MaintenanceNotificationJobEntity.status == "processing",
                MaintenanceNotificationJobEntity.lease_expires_at <= now,
                MaintenanceNotificationJobEntity.attempts < max_attempts,
            ),
        )
        entity = self.db.scalars(
            select(MaintenanceNotificationJobEntity)
            .where(eligible)
            .order_by(
                MaintenanceNotificationJobEntity.created_at,
                MaintenanceNotificationJobEntity.id,
            )
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

    def complete(
        self, job_id: str, attempt: int, now: datetime
    ) -> MaintenanceNotificationJob | None:
        entity = self._lock_active_job(job_id, attempt, now)
        if entity is None:
            return None
        entity.status = "sent"
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
        error_code: str,
        now: datetime,
        max_attempts: int,
        retry_delay_seconds: int,
    ) -> MaintenanceNotificationJob | None:
        entity = self._lock_active_job(job_id, attempt, now)
        if entity is None:
            return None
        entity.last_error = error_code[:100]
        entity.lease_expires_at = None
        if entity.attempts >= max_attempts:
            entity.status = "failed"
        else:
            entity.status = "pending"
            entity.available_at = now + timedelta(seconds=retry_delay_seconds)
        self.db.commit()
        self.db.refresh(entity)
        return self._snapshot(entity)

    def _by_key(self, idempotency_key: str) -> MaintenanceNotificationJobEntity | None:
        return self.db.scalars(
            select(MaintenanceNotificationJobEntity).where(
                MaintenanceNotificationJobEntity.idempotency_key == idempotency_key
            )
        ).first()

    def _lock_active_job(
        self, job_id: str, attempt: int, now: datetime
    ) -> MaintenanceNotificationJobEntity | None:
        return self.db.scalars(
            select(MaintenanceNotificationJobEntity)
            .where(
                MaintenanceNotificationJobEntity.id == job_id,
                MaintenanceNotificationJobEntity.status == "processing",
                MaintenanceNotificationJobEntity.attempts == attempt,
                MaintenanceNotificationJobEntity.lease_expires_at > now,
            )
            .with_for_update()
        ).first()

    @staticmethod
    def _snapshot(entity: MaintenanceNotificationJobEntity) -> MaintenanceNotificationJob:
        return MaintenanceNotificationJob(
            job_id=entity.id,
            idempotency_key=entity.idempotency_key,
            payload=entity.payload,
            issue_count=entity.issue_count,
            status=entity.status,
            attempts=entity.attempts,
            available_at=entity.available_at,
            created_at=entity.created_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            lease_expires_at=entity.lease_expires_at,
            last_error=entity.last_error,
        )
