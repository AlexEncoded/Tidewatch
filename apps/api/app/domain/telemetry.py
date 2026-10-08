from dataclasses import dataclass
from datetime import datetime, timezone

from .telemetry_types import (
    AMBIENT_LIGHT_MAX_LUX,
    AMBIENT_LIGHT_MIN_LUX,
    ACOUSTIC_ALTIMETER_MAX_DEPTH_METERS,
    ACOUSTIC_ALTIMETER_MIN_DEPTH_METERS,
    DIRECTION_MAX_DEGREES,
    DIRECTION_MIN_DEGREES,
    ATMOSPHERIC_PRESSURE_MAX_KPA,
    ATMOSPHERIC_PRESSURE_MIN_KPA,
    CHLOROPHYLL_A_MAX_UG_L,
    CHLOROPHYLL_A_MIN_UG_L,
    CONDUCTIVITY_MAX_US_CM,
    CONDUCTIVITY_MIN_US_CM,
    DISSOLVED_OXYGEN_MAX_MG_L,
    DISSOLVED_OXYGEN_MIN_MG_L,
    HUMIDITY_MAX_PERCENT,
    HUMIDITY_MIN_PERCENT,
    IMU_ACCELERATION_MAX_MPS2,
    IMU_ACCELERATION_MIN_MPS2,
    IMU_ANGULAR_VELOCITY_MAX_DPS,
    IMU_ANGULAR_VELOCITY_MIN_DPS,
    MARINE_CURRENT_SPEED_MAX_MPS,
    MARINE_CURRENT_SPEED_MIN_MPS,
    PH_MAX,
    PH_MIN,
    RAINFALL_MAX_MM_H,
    RAINFALL_MIN_MM_H,
    ReadingQuality,
    SALINITY_MAX_PSU,
    SALINITY_MIN_PSU,
    TURBIDITY_MAX_NTU,
    TURBIDITY_MIN_NTU,
    UNDERWATER_ACOUSTIC_MAX_ECHO_INTENSITY_DB,
    UNDERWATER_ACOUSTIC_MIN_ECHO_INTENSITY_DB,
    SensorChannel,
    AIR_TEMPERATURE_MAX_CELSIUS,
    AIR_TEMPERATURE_MIN_CELSIUS,
    VALID_READING_QUALITIES,
    VALID_SENSOR_CHANNELS,
    WIND_SPEED_MAX_MPS,
    WIND_SPEED_MIN_MPS,
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


@dataclass(frozen=True)
class LocationTelemetrySnapshot:
    """Domain representation of one buoy position telemetry sample."""

    buoy_id: str
    latitude: float
    longitude: float
    measured_at: datetime
    altitude_meters: float | None = None
    speed_mps: float | None = None
    hdop: float | None = None
    satellites: int | None = None
    device_id: str | None = None


@dataclass(frozen=True)
class SalinityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one salinity sample."""

    buoy_id: str
    salinity_psu: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not SALINITY_MIN_PSU <= self.salinity_psu <= SALINITY_MAX_PSU:
            raise ValueError(
                f"Salinity must be between {SALINITY_MIN_PSU} and "
                f"{SALINITY_MAX_PSU} PSU"
            )


@dataclass(frozen=True)
class ImuTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one inertial measurement sample."""

    buoy_id: str
    acceleration_x_mps2: float
    acceleration_y_mps2: float
    acceleration_z_mps2: float
    angular_velocity_x_dps: float
    angular_velocity_y_dps: float
    angular_velocity_z_dps: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        acceleration = (
            self.acceleration_x_mps2,
            self.acceleration_y_mps2,
            self.acceleration_z_mps2,
        )
        if any(
            not IMU_ACCELERATION_MIN_MPS2 <= value <= IMU_ACCELERATION_MAX_MPS2
            for value in acceleration
        ):
            raise ValueError(
                "IMU acceleration components must be between "
                f"{IMU_ACCELERATION_MIN_MPS2} and {IMU_ACCELERATION_MAX_MPS2} m/s²"
            )

        angular_velocity = (
            self.angular_velocity_x_dps,
            self.angular_velocity_y_dps,
            self.angular_velocity_z_dps,
        )
        if any(
            not IMU_ANGULAR_VELOCITY_MIN_DPS <= value <= IMU_ANGULAR_VELOCITY_MAX_DPS
            for value in angular_velocity
        ):
            raise ValueError(
                "IMU angular-velocity components must be between "
                f"{IMU_ANGULAR_VELOCITY_MIN_DPS} and "
                f"{IMU_ANGULAR_VELOCITY_MAX_DPS} degrees per second"
            )


@dataclass(frozen=True)
class AmbientLightTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one ambient-light sample."""

    buoy_id: str
    illuminance_lux: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not AMBIENT_LIGHT_MIN_LUX <= self.illuminance_lux <= AMBIENT_LIGHT_MAX_LUX:
            raise ValueError(
                f"Ambient light must be between {AMBIENT_LIGHT_MIN_LUX} and "
                f"{AMBIENT_LIGHT_MAX_LUX} lux"
            )


@dataclass(frozen=True)
class WindTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one wind speed and direction sample."""

    buoy_id: str
    wind_speed_mps: float
    wind_direction_degrees: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not WIND_SPEED_MIN_MPS <= self.wind_speed_mps <= WIND_SPEED_MAX_MPS:
            raise ValueError(
                f"Wind speed must be between {WIND_SPEED_MIN_MPS} and "
                f"{WIND_SPEED_MAX_MPS} m/s"
            )
        if not DIRECTION_MIN_DEGREES <= self.wind_direction_degrees < DIRECTION_MAX_DEGREES:
            raise ValueError(
                "Wind direction must be greater than or equal to "
                f"{DIRECTION_MIN_DEGREES} and less than {DIRECTION_MAX_DEGREES} degrees"
            )


@dataclass(frozen=True)
class MarineCurrentTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one marine-current sample."""

    buoy_id: str
    current_speed_mps: float
    current_direction_degrees: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not MARINE_CURRENT_SPEED_MIN_MPS <= self.current_speed_mps <= MARINE_CURRENT_SPEED_MAX_MPS:
            raise ValueError(
                "Marine-current speed must be between "
                f"{MARINE_CURRENT_SPEED_MIN_MPS} and "
                f"{MARINE_CURRENT_SPEED_MAX_MPS} m/s"
            )
        if not DIRECTION_MIN_DEGREES <= self.current_direction_degrees < DIRECTION_MAX_DEGREES:
            raise ValueError(
                "Marine-current direction must be greater than or equal to "
                f"{DIRECTION_MIN_DEGREES} and less than {DIRECTION_MAX_DEGREES} degrees"
            )


@dataclass(frozen=True)
class TurbidityTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one turbidity sample."""

    buoy_id: str
    turbidity_ntu: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not TURBIDITY_MIN_NTU <= self.turbidity_ntu <= TURBIDITY_MAX_NTU:
            raise ValueError(
                f"Turbidity must be between {TURBIDITY_MIN_NTU} and "
                f"{TURBIDITY_MAX_NTU} NTU"
            )


@dataclass(frozen=True)
class DissolvedOxygenTelemetrySnapshot(SensorTelemetrySnapshot):
    """Domain representation of one dissolved-oxygen sample."""

    buoy_id: str
    dissolved_oxygen_mg_l: float
    measured_at: datetime
    sensor_channel: SensorChannel = "A"
    device_id: str | None = None
    sensor_id: str | None = None
    firmware_version: str | None = None
    quality: ReadingQuality = "good"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not DISSOLVED_OXYGEN_MIN_MG_L <= self.dissolved_oxygen_mg_l <= DISSOLVED_OXYGEN_MAX_MG_L:
            raise ValueError(
                "Dissolved oxygen must be between "
                f"{DISSOLVED_OXYGEN_MIN_MG_L} and "
                f"{DISSOLVED_OXYGEN_MAX_MG_L} mg/L"
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


@dataclass(frozen=True)
class BatteryTelemetrySnapshot:
    """Domain representation of one device-battery sample."""

    buoy_id: str
    battery_percent: float
    device_id: SensorChannel
    measured_at: datetime

    def __post_init__(self) -> None:
        if self.device_id not in VALID_SENSOR_CHANNELS:
            raise ValueError(f"Unsupported battery device channel {self.device_id!r}")
        if not 0 <= self.battery_percent <= 100:
            raise ValueError("Battery percentage must be between 0 and 100")


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
