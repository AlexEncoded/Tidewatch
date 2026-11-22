"""Analytics HTTP dependency providers."""

from fastapi import Depends
from sqlalchemy.orm import Session
from ..application.alert_ports import TemperatureAlertsReader, TemperatureAlertStore
from ..application.analysis_ports import (
    PressureAnalysisReader,
    TemperatureAnalysisReader,
    WaveAnalysisMetrics,
    WaveAnalysisReader,
)
from ..adapters.postgres.database import get_db
from ..adapters.postgres.temperature_alert_repository import TemperatureAlertRepository
from ..adapters.postgres.temperature_repository import TemperatureRepository
from ..adapters.postgres.pressure_repository import PressureRepository
from ..adapters.prometheus.wave_analysis import PrometheusWaveAnalysisMetrics
from ..adapters.postgres.wave_analysis import WaveAnalysisRepository



def get_pressure_analysis_reader(
    db: Session = Depends(get_db),
) -> PressureAnalysisReader:
    """Compose pressure analysis with its SQL telemetry adapter."""
    return PressureRepository(db)


def get_wave_analysis_reader(
    db: Session = Depends(get_db),
) -> WaveAnalysisReader:
    """Compose wave analysis through the compatibility telemetry facade."""
    return WaveAnalysisRepository(db)


def get_wave_analysis_metrics() -> WaveAnalysisMetrics:
    """Compose wave-analysis metrics with the Prometheus adapter."""
    return PrometheusWaveAnalysisMetrics()


def get_temperature_analysis_reader(
    db: Session = Depends(get_db),
) -> TemperatureAnalysisReader:
    """Compose temperature analysis with its SQL telemetry adapter."""
    return TemperatureRepository(db)


def get_temperature_alerts_reader(
    db: Session = Depends(get_db),
) -> TemperatureAlertsReader:
    """Compose fleet temperature-alert queries with the alert adapter."""
    return TemperatureAlertRepository(db)


def get_temperature_alert_store(
    db: Session = Depends(get_db),
) -> TemperatureAlertStore:
    """Compose temperature-alert use cases with the alert persistence adapter."""
    return TemperatureAlertRepository(db)
