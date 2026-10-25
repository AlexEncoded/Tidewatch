"""Persistence mappings for core water-quality sensors."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
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
