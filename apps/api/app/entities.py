from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class BuoyEntity(Base):
    __tablename__ = "buoys"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_readings: Mapped[list["TemperatureReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )


class TemperatureReadingEntity(Base):
    __tablename__ = "temperature_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="temperature_readings")
