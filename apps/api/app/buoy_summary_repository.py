"""SQLAlchemy adapter composing buoy identity and latest sensor readings."""

from sqlalchemy.orm import Session

from .domain.buoy import BuoySummarySnapshot
from .persistence_mappers import buoy_snapshot
from .buoy_registry_repository import BuoyRegistryRepository
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
from .battery_repository import BatteryRepository


class BuoySummaryRepository:
    """Build fleet overview snapshots from fleet and telemetry adapters."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = BuoyRegistryRepository(db)
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
        self.battery = BatteryRepository(db)

    def list_buoy_summaries(self) -> list[BuoySummarySnapshot]:
        summaries = []
        telemetry_readers = {
            "temperature": self.temperature.latest_temperature,
            "pressure": self.pressure.latest_pressure,
            "salinity": self.salinity.latest_salinity,
            "imu": self.imu.latest_imu,
            "ambient_light": self.ambient_light.latest_ambient_light,
            "wind": self.wind.latest_wind,
            "marine_current": self.marine_current.latest_marine_current,
            "turbidity": self.turbidity.latest_turbidity,
            "dissolved_oxygen": self.dissolved_oxygen.latest_dissolved_oxygen,
            "ph": self.ph.latest_ph,
            "conductivity": self.conductivity.latest_conductivity,
            "chlorophyll_a": self.chlorophyll_a.latest_chlorophyll_a,
            "rainfall": self.rainfall.latest_rainfall,
            "humidity": self.humidity.latest_humidity,
            "air_temperature": self.air_temperature.latest_air_temperature,
            "atmospheric_pressure": self.atmospheric_pressure.latest_atmospheric_pressure,
        }
        buoys = self.registry.list_buoys()
        for entity in buoys:
            latest_readings = {
                family: {
                    "latest": get_latest(entity.id),
                    "A": get_latest(entity.id, "A"),
                    "B": get_latest(entity.id, "B"),
                }
                for family, get_latest in telemetry_readers.items()
            }
            latest_readings["battery"] = {
                "latest": self.battery.latest_battery(entity.id),
                "A": self.battery.latest_battery(entity.id, "A"),
                "B": self.battery.latest_battery(entity.id, "B"),
            }
            summaries.append(
                BuoySummarySnapshot(
                    buoy=buoy_snapshot(entity), latest_readings=latest_readings
                )
            )
        return summaries
