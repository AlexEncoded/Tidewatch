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
    temperature_readings: Mapped[list["TemperatureReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    pressure_readings: Mapped[list["PressureReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    salinity_readings: Mapped[list["SalinityReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    imu_readings: Mapped[list["ImuReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    ambient_light_readings: Mapped[list["AmbientLightReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    wind_readings: Mapped[list["WindReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    marine_current_readings: Mapped[list["MarineCurrentReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    turbidity_readings: Mapped[list["TurbidityReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    dissolved_oxygen_readings: Mapped[list["DissolvedOxygenReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    ph_readings: Mapped[list["PHReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    conductivity_readings: Mapped[list["ConductivityReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    chlorophyll_a_readings: Mapped[list["ChlorophyllAReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    rainfall_readings: Mapped[list["RainfallReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    humidity_readings: Mapped[list["HumidityReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    air_temperature_readings: Mapped[list["AirTemperatureReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    atmospheric_pressure_readings: Mapped[list["AtmosphericPressureReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    acoustic_altimeter_readings: Mapped[list["AcousticAltimeterReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
    underwater_acoustic_readings: Mapped[list["UnderwaterAcousticReadingEntity"]] = relationship(
        back_populates="buoy", cascade="all, delete-orphan"
    )
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
