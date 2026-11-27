"""Prometheus adapter for wave-analysis results."""

from time import time

from ...application.analysis_ports import WaveAnalysisMetrics
from ...domain.analytics.wave import WaveAnalysisSnapshot
from .instruments import (
    current_estimated_wave_height_m,
    current_estimated_wave_period_seconds,
    wave_analysis_last_run_timestamp_seconds,
    wave_analysis_gnss_quality_eligible_samples,
    wave_analysis_rejected_gnss_samples,
    wave_period_sensor_disagreement,
)


class PrometheusWaveAnalysisMetrics(WaveAnalysisMetrics):
    """Publish the latest wave analysis and clear unavailable estimates."""

    def record_analysis(self, result: WaveAnalysisSnapshot) -> None:
        wave_analysis_last_run_timestamp_seconds.labels(
            buoy_id=result.buoy_id
        ).set(time())
        wave_analysis_gnss_quality_eligible_samples.labels(
            buoy_id=result.buoy_id
        ).set(result.gnss_quality_eligible_sample_count)
        wave_analysis_rejected_gnss_samples.labels(
            buoy_id=result.buoy_id, reason="satellite_count"
        ).set(result.rejected_gnss_satellite_sample_count)
        wave_analysis_rejected_gnss_samples.labels(
            buoy_id=result.buoy_id, reason="hdop"
        ).set(result.rejected_gnss_hdop_sample_count)
        self._set_or_remove(
            current_estimated_wave_height_m,
            result.buoy_id,
            result.estimated_wave_height_m,
        )
        self._set_or_remove(
            current_estimated_wave_period_seconds,
            result.buoy_id,
            result.estimated_period_seconds,
        )
        wave_period_sensor_disagreement.labels(buoy_id=result.buoy_id).set(
            int(result.period_confidence == "sensor_disagreement")
        )

    @staticmethod
    def _set_or_remove(metric, buoy_id: str, value: float | None) -> None:
        if value is not None:
            metric.labels(buoy_id=buoy_id).set(value)
            return
        try:
            metric.remove(buoy_id)
        except KeyError:
            pass
