import pytest

from app.domain.telemetry_job_retry import telemetry_job_retry_delay_seconds


@pytest.mark.parametrize(
    ("attempt", "expected_delay"),
    [(1, 2), (2, 4), (3, 8), (8, 256), (9, 300), (10, 300), (10**6, 300)],
)
def test_retry_delay_uses_capped_exponential_backoff(
    attempt: int, expected_delay: int
) -> None:
    assert telemetry_job_retry_delay_seconds(attempt) == expected_delay


def test_retry_delay_supports_a_zero_delay_cap() -> None:
    assert telemetry_job_retry_delay_seconds(1, max_delay_seconds=0) == 0


@pytest.mark.parametrize(
    ("attempt", "maximum"), [(0, 300), (1, -1)]
)
def test_retry_delay_rejects_invalid_policy_values(attempt: int, maximum: int) -> None:
    with pytest.raises(ValueError):
        telemetry_job_retry_delay_seconds(attempt, maximum)
