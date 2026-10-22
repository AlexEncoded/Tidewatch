"""Persistence mappings for application alerts."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .fleet_entities import BuoyEntity


class TemperatureAlertEntity(Base):
    __tablename__ = "temperature_alerts"
    __table_args__ = (UniqueConstraint("buoy_id", "reading_measured_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    reading_measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    average_temperature: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    buoy: Mapped[BuoyEntity] = relationship()
