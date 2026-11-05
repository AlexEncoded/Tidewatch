from dataclasses import dataclass
from datetime import datetime, timezone

from .telemetry_types import (
    ACOUSTIC_ALTIMETER_MAX_DEPTH_METERS,
    ACOUSTIC_ALTIMETER_MIN_DEPTH_METERS,
    DEVICE_ID_MAX_LENGTH,
    DEVICE_ID_MIN_LENGTH,
    FIRMWARE_VERSION_MAX_LENGTH,
    ATMOSPHERIC_PRESSURE_MAX_KPA,
    ATMOSPHERIC_PRESSURE_MIN_KPA,
    CHLOROPHYLL_A_MAX_UG_L,
    CHLOROPHYLL_A_MIN_UG_L,
    CONDUCTIVITY_MAX_US_CM,
    CONDUCTIVITY_MIN_US_CM,
    HUMIDITY_MAX_PERCENT,
    HUMIDITY_MIN_PERCENT,
    PH_MAX,
    PH_MIN,
    RAINFALL_MAX_MM_H,
    RAINFALL_MIN_MM_H,
    ReadingQuality,
    SENSOR_ID_MAX_LENGTH,
    UNDERWATER_ACOUSTIC_MAX_ECHO_INTENSITY_DB,
    UNDERWATER_ACOUSTIC_MIN_ECHO_INTENSITY_DB,
    SensorChannel,
    AIR_TEMPERATURE_MAX_CELSIUS,
    AIR_TEMPERATURE_MIN_CELSIUS,
    VALID_READING_QUALITIES,
    VALID_SENSOR_CHANNELS,
)


class SensorTelemetrySnapshot:
    """Runtime invariants shared by snapshots for redundant sensors."""

    sensor_channel: SensorChannel
    quality: ReadingQuality

    def __post_init__(self) -> None:
        if self.sensor_channel not in VALID_SENSOR_CHANNELS:
            raise ValueError(f"Unsupported sensor channel {self.sensor_channel!r}")
        if self.quality not in VALID_READING_QUALITIES:
            raise ValueError(f"Unsupported reading quality {self.quality!r}")
        _validate_device_id(getattr(self, "device_id", None))
        sensor_id = getattr(self, "sensor_id", None)
        if sensor_id is not None and len(sensor_id) > SENSOR_ID_MAX_LENGTH:
            raise ValueError(f"Sensor ID must be at most {SENSOR_ID_MAX_LENGTH} characters")
        firmware_version = getattr(self, "firmware_version", None)
        if firmware_version is not None and len(firmware_version) > FIRMWARE_VERSION_MAX_LENGTH:
            raise ValueError(
                f"Firmware version must be at most {FIRMWARE_VERSION_MAX_LENGTH} characters"
            )


def _validate_device_id(device_id: str | None) -> None:
    if device_id is not None and not DEVICE_ID_MIN_LENGTH <= len(device_id) <= DEVICE_ID_MAX_LENGTH:
        raise ValueError(
            f"Device ID must contain between {DEVICE_ID_MIN_LENGTH} "
            f"and {DEVICE_ID_MAX_LENGTH} characters"
        )


@dataclass(frozen=True)
class PHTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one pH sample."""

    buoy_id: str
    ph: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not PH_MIN <= self.ph <= PH_MAX:
            raise ValueError(f"pH must be between {PH_MIN} and {PH_MAX}")


@dataclass(frozen=True)
class ConductivityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one conductivity sample."""

    buoy_id: str
    conductivity_us_cm: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not CONDUCTIVITY_MIN_US_CM <= self.conductivity_us_cm <= CONDUCTIVITY_MAX_US_CM:
            raise ValueError(
                f"Conductivity must be between {CONDUCTIVITY_MIN_US_CM} and "
                f"{CONDUCTIVITY_MAX_US_CM} µS/cm"
            )


@dataclass(frozen=True)
class ChlorophyllATelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one chlorophyll-a sample."""

    buoy_id: str
    chlorophyll_a_ug_l: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not CHLOROPHYLL_A_MIN_UG_L <= self.chlorophyll_a_ug_l <= CHLOROPHYLL_A_MAX_UG_L:
            raise ValueError(
                f"Chlorophyll-a must be between {CHLOROPHYLL_A_MIN_UG_L} and "
                f"{CHLOROPHYLL_A_MAX_UG_L} µg/L"
            )


@dataclass(frozen=True)
class RainfallTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one rainfall sample."""

    buoy_id: str
    rainfall_mm_h: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not RAINFALL_MIN_MM_H <= self.rainfall_mm_h <= RAINFALL_MAX_MM_H:
            raise ValueError(
                f"Rainfall must be between {RAINFALL_MIN_MM_H} and "
                f"{RAINFALL_MAX_MM_H} mm/h"
            )


@dataclass(frozen=True)
class HumidityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one humidity sample."""

    buoy_id: str
    humidity_percent: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not HUMIDITY_MIN_PERCENT <= self.humidity_percent <= HUMIDITY_MAX_PERCENT:
            raise ValueError(
                f"Humidity must be between {HUMIDITY_MIN_PERCENT} and "
                f"{HUMIDITY_MAX_PERCENT} percent"
            )


@dataclass(frozen=True)
class AirTemperatureTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one air-temperature sample."""

    buoy_id: str
    air_temperature_celsius: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not AIR_TEMPERATURE_MIN_CELSIUS <= self.air_temperature_celsius <= AIR_TEMPERATURE_MAX_CELSIUS:
            raise ValueError(
                "Air temperature must be between "
                f"{AIR_TEMPERATURE_MIN_CELSIUS} and {AIR_TEMPERATURE_MAX_CELSIUS} °C"
            )


@dataclass(frozen=True)
class AtmosphericPressureTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one atmospheric-pressure sample."""

    buoy_id: str
    atmospheric_pressure_kpa: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not ATMOSPHERIC_PRESSURE_MIN_KPA <= self.atmospheric_pressure_kpa <= ATMOSPHERIC_PRESSURE_MAX_KPA:
            raise ValueError(
                "Atmospheric pressure must be between "
                f"{ATMOSPHERIC_PRESSURE_MIN_KPA} and "
                f"{ATMOSPHERIC_PRESSURE_MAX_KPA} kPa"
            )


@dataclass(frozen=True)
class AcousticAltimeterTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one acoustic-altimeter sample."""

    buoy_id: str
    depth_meters: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not ACOUSTIC_ALTIMETER_MIN_DEPTH_METERS <= self.depth_meters <= ACOUSTIC_ALTIMETER_MAX_DEPTH_METERS:
            raise ValueError(
                "Acoustic-altimeter depth must be between "
                f"{ACOUSTIC_ALTIMETER_MIN_DEPTH_METERS} and "
                f"{ACOUSTIC_ALTIMETER_MAX_DEPTH_METERS} meters"
            )


@dataclass(frozen=True)
class UnderwaterAcousticTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one underwater-acoustic sample."""

    buoy_id: str
    echo_intensity_db: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not UNDERWATER_ACOUSTIC_MIN_ECHO_INTENSITY_DB <= self.echo_intensity_db <= UNDERWATER_ACOUSTIC_MAX_ECHO_INTENSITY_DB:
            raise ValueError(
                "Underwater acoustic echo intensity must be between "
                f"{UNDERWATER_ACOUSTIC_MIN_ECHO_INTENSITY_DB} and "
                f"{UNDERWATER_ACOUSTIC_MAX_ECHO_INTENSITY_DB} dB"
            )


def latest_usable_reading(
    readings: list,
    max_age_seconds: float | None = None,
    now: datetime | None = None,
) -> list:
    """Return the newest valid reading within the optional age window."""
    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    for reading in readings:
        if reading.quality == "invalid":
            continue
        if max_age_seconds is not None:
            measured_at = reading.measured_at
            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=timezone.utc)
            if (reference_time - measured_at).total_seconds() > max_age_seconds:
                continue
        return [reading]
    return []
