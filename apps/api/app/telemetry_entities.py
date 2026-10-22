"""Persistence mappings for durable telemetry ingestion."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class TelemetryIngestionJobEntity(Base):
    __tablename__ = "telemetry_ingestion_jobs"
    __table_args__ = (
        Index("ix_telemetry_ingestion_jobs_claim", "status", "available_at", "created_at"),
        Index("ix_telemetry_ingestion_jobs_expired", "status", "lease_expires_at"),
        UniqueConstraint(
            "buoy_id",
            "idempotency_key",
            name="uq_telemetry_job_buoy_idempotency",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    buoy_id: Mapped[str] = mapped_column(
        ForeignKey("buoys.id", ondelete="CASCADE"), nullable=False
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
