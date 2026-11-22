"""Composition of focused PostgreSQL adapters for sensor telemetry."""

from sqlalchemy.orm import Session

from .temperature_repository import TemperatureRepository
from .pressure_repository import PressureRepository
from .salinity_repository import SalinityRepository
from .imu_repository import ImuRepository
from .ambient_light_repository import AmbientLightRepository
from .wind_repository import WindRepository
from .marine_current_repository import MarineCurrentRepository
from .turbidity_repository import TurbidityRepository
from .dissolved_oxygen_repository import DissolvedOxygenRepository
from .ph_repository import PHRepository
from .conductivity_repository import ConductivityRepository
from .chlorophyll_a_repository import ChlorophyllARepository
from .rainfall_repository import RainfallRepository
from .humidity_repository import HumidityRepository
from .air_temperature_repository import AirTemperatureRepository
from .atmospheric_pressure_repository import AtmosphericPressureRepository
from .acoustic_altimeter_repository import AcousticAltimeterRepository
from .underwater_acoustic_repository import UnderwaterAcousticRepository


class SensorTelemetryRepositories:
    """Provide the focused sensor adapters used by composite gateways."""

    def __init__(self, db: Session) -> None:
        self.temperature = TemperatureRepository(db)
        self.pressure = PressureRepository(db)
        self.salinity = SalinityRepository(db)
        self.imu = ImuRepository(db)
        self.ambient_light = AmbientLightRepository(db)
        self.wind = WindRepository(db)
        self.marine_current = MarineCurrentRepository(db)
        self.turbidity = TurbidityRepository(db)
        self.dissolved_oxygen = DissolvedOxygenRepository(db)
        self.ph = PHRepository(db)
        self.conductivity = ConductivityRepository(db)
        self.chlorophyll_a = ChlorophyllARepository(db)
        self.rainfall = RainfallRepository(db)
        self.humidity = HumidityRepository(db)
        self.air_temperature = AirTemperatureRepository(db)
        self.atmospheric_pressure = AtmosphericPressureRepository(db)
        self.acoustic_altimeter = AcousticAltimeterRepository(db)
        self.underwater_acoustic = UnderwaterAcousticRepository(db)
