from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .fleet_entities import BuoyEntity, BuoyLocationReadingEntity, DeviceEntity
from .sensor_entities import (
    AmbientLightReadingEntity,
    ConductivityReadingEntity,
    DissolvedOxygenReadingEntity,
    ImuReadingEntity,
    MarineCurrentReadingEntity,
    PHReadingEntity,
    PressureReadingEntity,
    SalinityReadingEntity,
    TemperatureReadingEntity,
    TurbidityReadingEntity,
    WindReadingEntity,
)


class ChlorophyllAReadingEntity(Base):
    __tablename__ = "chlorophyll_a_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    chlorophyll_a_ug_l: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="chlorophyll_a_readings")


class RainfallReadingEntity(Base):
    __tablename__ = "rainfall_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    rainfall_mm_h: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="rainfall_readings")


class HumidityReadingEntity(Base):
    __tablename__ = "humidity_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    humidity_percent: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="humidity_readings")


class AirTemperatureReadingEntity(Base):
    __tablename__ = "air_temperature_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    air_temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="air_temperature_readings")


class AtmosphericPressureReadingEntity(Base):
    __tablename__ = "atmospheric_pressure_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    atmospheric_pressure_kpa: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="atmospheric_pressure_readings")


class AcousticAltimeterReadingEntity(Base):
    __tablename__ = "acoustic_altimeter_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    depth_meters: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="acoustic_altimeter_readings")


class UnderwaterAcousticReadingEntity(Base):
    __tablename__ = "underwater_acoustic_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    echo_intensity_db: Mapped[float] = mapped_column(Float, nullable=False)
    sensor_channel: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sensor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality: Mapped[str] = mapped_column(String(12), nullable=False, default="good")
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="underwater_acoustic_readings")


class SensorHealthCheckEntity(Base):
    __tablename__ = "sensor_health_checks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    temperature_delta_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_delta_kpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    salinity_delta_psu: Mapped[float | None] = mapped_column(Float, nullable=True)
    imu_acceleration_delta_mps2: Mapped[float | None] = mapped_column(Float, nullable=True)
    ambient_light_delta_lux: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_delta_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction_delta_degrees: Mapped[float | None] = mapped_column(Float, nullable=True)
    marine_current_speed_delta_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    marine_current_direction_delta_degrees: Mapped[float | None] = mapped_column(Float, nullable=True)
    turbidity_delta_ntu: Mapped[float | None] = mapped_column(Float, nullable=True)
    dissolved_oxygen_delta_mg_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    ph_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    conductivity_delta_us_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    chlorophyll_a_delta_ug_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_delta_mm_h: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_delta_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_temperature_delta_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    atmospheric_pressure_delta_kpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    acoustic_altimeter_delta_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    underwater_acoustic_delta_db: Mapped[float | None] = mapped_column(Float, nullable=True)
    degraded_sensors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    missing_sensors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    decisions: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship()


class BatteryReadingEntity(Base):
    __tablename__ = "battery_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buoy_id: Mapped[str] = mapped_column(ForeignKey("buoys.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(String(1), nullable=False, default="A")
    physical_device_id: Mapped[str | None] = mapped_column(
        ForeignKey("devices.device_id", ondelete="SET NULL"), nullable=True, index=True
    )
    battery_percent: Mapped[float] = mapped_column(Float, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    buoy: Mapped[BuoyEntity] = relationship(back_populates="battery_readings")


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
