"""SQLAlchemy adapter for fleet-wide sensor-quality summaries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .application.ports import QualitySummaryReader
from .buoy_registry_repository import BuoyRegistryRepository
from .entities import (
    AcousticAltimeterReadingEntity,
    AirTemperatureReadingEntity,
    AmbientLightReadingEntity,
    AtmosphericPressureReadingEntity,
    ChlorophyllAReadingEntity,
    ConductivityReadingEntity,
    DissolvedOxygenReadingEntity,
    HumidityReadingEntity,
    ImuReadingEntity,
    MarineCurrentReadingEntity,
    PHReadingEntity,
    PressureReadingEntity,
    RainfallReadingEntity,
    SalinityReadingEntity,
    TemperatureReadingEntity,
    TurbidityReadingEntity,
    UnderwaterAcousticReadingEntity,
    WindReadingEntity,
)


QUALITY_READING_ENTITIES = (
    TemperatureReadingEntity,
    PressureReadingEntity,
    SalinityReadingEntity,
    ImuReadingEntity,
    AmbientLightReadingEntity,
    WindReadingEntity,
    MarineCurrentReadingEntity,
    TurbidityReadingEntity,
    DissolvedOxygenReadingEntity,
    PHReadingEntity,
    ConductivityReadingEntity,
    ChlorophyllAReadingEntity,
    RainfallReadingEntity,
    HumidityReadingEntity,
    AirTemperatureReadingEntity,
    AtmosphericPressureReadingEntity,
    AcousticAltimeterReadingEntity,
    UnderwaterAcousticReadingEntity,
)


class QualitySummaryRepository(QualitySummaryReader):
    """Aggregate quality labels across every quality-bearing sensor family."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = BuoyRegistryRepository(db)

    def buoy_exists(self, buoy_id: str) -> bool:
        return self.registry.buoy_exists(buoy_id)

    def quality_counts(self, buoy_id: str) -> dict[str, int]:
        counts = {"good": 0, "suspect": 0, "invalid": 0}
        for entity in QUALITY_READING_ENTITIES:
            query = (
                select(entity.quality, func.count())
                .where(entity.buoy_id == buoy_id)
                .group_by(entity.quality)
            )
            for quality, count in self.db.execute(query):
                if quality in counts:
                    counts[quality] += count
        return counts
