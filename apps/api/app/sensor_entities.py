"""Persistence mappings for core water-quality sensors."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .fleet_entities import BuoyEntity


class TemperatureReadingEntity(Base):
    __tablename__ = "temperature_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="temperature_readings")


class PressureReadingEntity(Base):
    __tablename__ = "pressure_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    pressure_kpa: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="pressure_readings")


class SalinityReadingEntity(Base):
    __tablename__ = "salinity_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    salinity_psu: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="salinity_readings")


class ImuReadingEntity(Base):
    __tablename__ = "imu_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    acceleration_x_mps2: Mapped[float] = mapped_column(Float, nullable=False)
    acceleration_y_mps2: Mapped[float] = mapped_column(Float, nullable=False)
    acceleration_z_mps2: Mapped[float] = mapped_column(Float, nullable=False)
    angular_velocity_x_dps: Mapped[float] = mapped_column(Float, nullable=False)
    angular_velocity_y_dps: Mapped[float] = mapped_column(Float, nullable=False)
    angular_velocity_z_dps: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="imu_readings")


class AmbientLightReadingEntity(Base):
    __tablename__ = "ambient_light_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    illuminance_lux: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="ambient_light_readings")


class WindReadingEntity(Base):
    __tablename__ = "wind_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    wind_speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    wind_direction_degrees: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="wind_readings")


class MarineCurrentReadingEntity(Base):
    __tablename__ = "marine_current_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    current_speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    current_direction_degrees: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="marine_current_readings")


class TurbidityReadingEntity(Base):
    __tablename__ = "turbidity_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    turbidity_ntu: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="turbidity_readings")


class DissolvedOxygenReadingEntity(Base):
    __tablename__ = "dissolved_oxygen_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    dissolved_oxygen_mg_l: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="dissolved_oxygen_readings")


class PHReadingEntity(Base):
    __tablename__ = "ph_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    ph: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="ph_readings")


class ConductivityReadingEntity(Base):
    __tablename__ = "conductivity_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    conductivity_us_cm: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="conductivity_readings")
