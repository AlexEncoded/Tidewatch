from app.application.quality_ports import QualitySummaryReader
from app.application.quality_summary import summarize_quality
from app.domain.telemetry.quality import QualitySummarySnapshot
from app.domain.telemetry.quality import summarize_quality_counts
import pytest
from typing import get_args, get_type_hints

from app.domain.sensors.reading_quality import ReadingQuality


class FakeQualityReader:
    def buoy_exists(self, buoy_id: str) -> bool:
        return buoy_id == "buoy-1"

    def quality_counts(self, buoy_id: str) -> dict[ReadingQuality, int]:
        assert buoy_id == "buoy-1"
        return {"good": 7, "suspect": 2, "invalid": 1}


def test_quality_summary_is_built_through_reader_port() -> None:
    summary = summarize_quality(FakeQualityReader(), "buoy-1")

    assert summary.buoy_id == "buoy-1"
    assert summary.total_readings == 10
    assert summary.good_readings == 7
    assert summary.suspect_readings == 2
    assert summary.invalid_readings == 1
    assert isinstance(summary, QualitySummarySnapshot)


def test_quality_summary_returns_none_when_buoy_does_not_exist() -> None:
    assert summarize_quality(FakeQualityReader(), "missing") is None


def test_quality_summary_counts_only_recognized_categories() -> None:
    summary = summarize_quality_counts(
        "buoy-1", {"good": 2, "suspect": 1, "invalid": 1, "unknown": 9}
    )

    assert summary.total_readings == 4


@pytest.mark.parametrize(
    ("total", "good", "suspect", "invalid"),
    [(0, -1, 0, 0), (2, 1, 0, 0)],
)
def test_quality_summary_snapshot_rejects_invalid_invariants(
    total: int, good: int, suspect: int, invalid: int
) -> None:
    with pytest.raises(ValueError):
        QualitySummarySnapshot(
            buoy_id="buoy-1",
            total_readings=total,
            good_readings=good,
            suspect_readings=suspect,
            invalid_readings=invalid,
        )


def test_quality_count_contract_uses_the_closed_reading_quality_type() -> None:
    domain_keys = get_args(get_type_hints(summarize_quality_counts)["counts"])[0]
    port_values = get_args(
        get_type_hints(QualitySummaryReader.quality_counts)["return"]
    )[0]

    assert get_args(domain_keys) == ("good", "suspect", "invalid")
    assert port_values is domain_keys
