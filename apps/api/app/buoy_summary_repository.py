"""SQLAlchemy adapter composing buoy identity and latest sensor readings."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .domain.buoy import BuoySummarySnapshot
from .entities import BuoyEntity
from .persistence_mappers import buoy_snapshot
from .repository import BuoyRepository


class BuoySummaryRepository:
    """Build fleet overview snapshots from fleet and telemetry adapters."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.telemetry = BuoyRepository(db)

    def list_buoy_summaries(self) -> list[BuoySummarySnapshot]:
        summaries = []
        telemetry_readers = {
            "temperature": self.telemetry.latest_temperature,
            "pressure": self.telemetry.latest_pressure,
            "salinity": self.telemetry.latest_salinity,
            "imu": self.telemetry.latest_imu,
            "ambient_light": self.telemetry.latest_ambient_light,
            "wind": self.telemetry.latest_wind,
            "marine_current": self.telemetry.latest_marine_current,
            "turbidity": self.telemetry.latest_turbidity,
            "dissolved_oxygen": self.telemetry.latest_dissolved_oxygen,
            "ph": self.telemetry.latest_ph,
            "conductivity": self.telemetry.latest_conductivity,
            "chlorophyll_a": self.telemetry.latest_chlorophyll_a,
            "rainfall": self.telemetry.latest_rainfall,
            "humidity": self.telemetry.latest_humidity,
            "air_temperature": self.telemetry.latest_air_temperature,
            "atmospheric_pressure": self.telemetry.latest_atmospheric_pressure,
        }
        buoys = self.db.scalars(
            select(BuoyEntity).order_by(BuoyEntity.created_at)
        ).all()
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
                "latest": self.telemetry.latest_battery(entity.id),
                "A": self.telemetry.latest_battery(entity.id, "A"),
                "B": self.telemetry.latest_battery(entity.id, "B"),
            }
            summaries.append(
                BuoySummarySnapshot(
                    buoy=buoy_snapshot(entity), latest_readings=latest_readings
                )
            )
        return summaries
