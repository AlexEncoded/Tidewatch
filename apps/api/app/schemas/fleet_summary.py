"""HTTP response contract for a buoy and its latest telemetry."""

from pydantic import BaseModel

from .battery import BatteryReading
from .fleet import Buoy
from .telemetry import (
    AirTemperatureReading,
    AmbientLightReading,
    AtmosphericPressureReading,
    ChlorophyllAReading,
    ConductivityReading,
    DissolvedOxygenReading,
    HumidityReading,
    ImuReading,
    MarineCurrentReading,
    PHReading,
    PressureReading,
    RainfallReading,
    SalinityReading,
    TemperatureReading,
    TurbidityReading,
    WindReading,
)


class BuoySummary(BaseModel):
    buoy: Buoy
    latest_temperature: TemperatureReading | None = None
    latest_temperature_a: TemperatureReading | None = None
    latest_temperature_b: TemperatureReading | None = None
    latest_pressure: PressureReading | None = None
    latest_pressure_a: PressureReading | None = None
    latest_pressure_b: PressureReading | None = None
    latest_salinity: SalinityReading | None = None
    latest_salinity_a: SalinityReading | None = None
    latest_salinity_b: SalinityReading | None = None
    latest_imu: ImuReading | None = None
    latest_imu_a: ImuReading | None = None
    latest_imu_b: ImuReading | None = None
    latest_ambient_light: AmbientLightReading | None = None
    latest_ambient_light_a: AmbientLightReading | None = None
    latest_ambient_light_b: AmbientLightReading | None = None
    latest_wind: WindReading | None = None
    latest_wind_a: WindReading | None = None
    latest_wind_b: WindReading | None = None
    latest_marine_current: MarineCurrentReading | None = None
    latest_marine_current_a: MarineCurrentReading | None = None
    latest_marine_current_b: MarineCurrentReading | None = None
    latest_turbidity: TurbidityReading | None = None
    latest_turbidity_a: TurbidityReading | None = None
    latest_turbidity_b: TurbidityReading | None = None
    latest_dissolved_oxygen: DissolvedOxygenReading | None = None
    latest_dissolved_oxygen_a: DissolvedOxygenReading | None = None
    latest_dissolved_oxygen_b: DissolvedOxygenReading | None = None
    latest_ph: PHReading | None = None
    latest_ph_a: PHReading | None = None
    latest_ph_b: PHReading | None = None
    latest_conductivity: ConductivityReading | None = None
    latest_conductivity_a: ConductivityReading | None = None
    latest_conductivity_b: ConductivityReading | None = None
    latest_chlorophyll_a: ChlorophyllAReading | None = None
    latest_chlorophyll_a_a: ChlorophyllAReading | None = None
    latest_chlorophyll_a_b: ChlorophyllAReading | None = None
    latest_rainfall: RainfallReading | None = None
    latest_rainfall_a: RainfallReading | None = None
    latest_rainfall_b: RainfallReading | None = None
    latest_humidity: HumidityReading | None = None
    latest_humidity_a: HumidityReading | None = None
    latest_humidity_b: HumidityReading | None = None
    latest_air_temperature: AirTemperatureReading | None = None
    latest_air_temperature_a: AirTemperatureReading | None = None
    latest_air_temperature_b: AirTemperatureReading | None = None
    latest_atmospheric_pressure: AtmosphericPressureReading | None = None
    latest_atmospheric_pressure_a: AtmosphericPressureReading | None = None
    latest_atmospheric_pressure_b: AtmosphericPressureReading | None = None
    latest_battery: BatteryReading | None = None
    latest_battery_a: BatteryReading | None = None
    latest_battery_b: BatteryReading | None = None
