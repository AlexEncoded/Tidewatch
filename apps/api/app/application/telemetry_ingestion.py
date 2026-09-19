"""Application helpers for normalising incoming telemetry batches."""


def with_device_provenance(
    reading_data: dict,
    batch_device_id: str | None,
) -> dict:
    """Return a copy with the batch device when no owner is explicit."""
    normalized = dict(reading_data)
    if batch_device_id is not None and normalized.get("device_id") is None:
        normalized["device_id"] = batch_device_id
    return normalized
