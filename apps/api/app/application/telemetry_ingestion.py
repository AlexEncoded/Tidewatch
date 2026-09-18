"""Application helpers for normalising incoming telemetry batches."""


def with_device_provenance(
    reading_data: dict,
    batch_device_id: str | None,
) -> dict:
    """Apply the batch device only when a reading has no explicit owner."""
    if batch_device_id is not None and reading_data.get("device_id") is None:
        reading_data["device_id"] = batch_device_id
    return reading_data
