from app.application.quality_summary import summarize_quality
from app.domain.quality import QualitySummarySnapshot
from app.domain.quality import summarize_quality_counts
import pytest


class FakeQualityReader:
    def buoy_exists(self, buoy_id: str) -> bool:
        return buoy_id == "buoy-1"

    def quality_counts(self, buoy_id: str) -> dict[str, int]:
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
