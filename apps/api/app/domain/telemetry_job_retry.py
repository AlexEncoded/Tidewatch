"""Retry policy for durable telemetry-ingestion jobs."""


def telemetry_job_retry_delay_seconds(
    attempt: int, max_delay_seconds: int = 300
) -> int:
    """Return capped exponential backoff for a one-based failed attempt."""
    if attempt < 1:
        raise ValueError("Attempt number must be greater than zero")
    if max_delay_seconds < 0:
        raise ValueError("Maximum retry delay cannot be negative")
    if max_delay_seconds == 0:
        return 0
    if attempt >= max_delay_seconds.bit_length():
        return max_delay_seconds
    return 2**attempt
