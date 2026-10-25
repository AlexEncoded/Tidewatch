"""Persistence mappings for fleet identity and physical devices."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class BuoyEntity(Base):
    __tablename__ = "buoys"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    battery_readings: Mapped[list["BatteryReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    location_readings: Mapped[list["BuoyLocationReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    devices: Mapped[list["DeviceEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )


class DeviceEntity(Base):
    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("buoy_id", "sensor_channel", name="uq_devices_buoy_channel"),
    )

    device_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="devices")


class BuoyLocationReadingEntity(Base):
    __tablename__ = "buoy_location_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(
        ForeignKey("buoys.id", ondelete="CASCADE"), index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    altitude_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    hdop: Mapped[float | None] = mapped_column(Float, nullable=True)
    satellites: Mapped[int | None] = mapped_column(nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    buoy: Mapped[BuoyEntity] = relationship(back_populates="location_readings")


class BatteryReadingEntity(Base):
    __tablename__ = "battery_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(
        ForeignKey("buoys.id", ondelete="CASCADE"), index=True
    )
    device_id: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    physical_device_id: Mapped[str | None] = mapped_column(
        ForeignKey("devices.device_id", ondelete="SET NULL"), nullable=True, index=True
    )
    battery_percent: Mapped[float] = mapped_column(Float, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    buoy: Mapped[BuoyEntity] = relationship(back_populates="battery_readings")
