"""Persistence mapping for durable maintenance notification delivery."""

from datetime import datetime

from sqlalchemy import DateTime, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class MaintenanceNotificationJobEntity(Base):
    __tablename__ = "maintenance_notification_jobs"
    __table_args__ = (
        Index(
            "ix_maintenance_notification_claim",
            "status",
            "available_at",
            "created_at",
        ),
        Index("ix_maintenance_notification_expired", "status", "lease_expires_at"),
        UniqueConstraint(
            "idempotency_key", name="uq_maintenance_notification_key"
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    issue_count: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(String(100), nullable=True)
