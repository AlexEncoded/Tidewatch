"""Transport-neutral command data for a validated telemetry batch."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from ..domain.telemetry_family import TELEMETRY_READING_FAMILIES, TelemetryInputFamily


def _json_compatible(value: Any) -> Any:
    """Convert validated Python values to JSON-compatible data for the queue."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value


@dataclass(frozen=True)
class TelemetryBatchCommand:
    """Validated batch values after the transport adapter has normalized input."""

    device_id: str | None
    readings: Mapping[TelemetryInputFamily, tuple[Mapping[str, Any], ...]]
    location: Mapping[str, Any] | None = None
    device_runtime: Mapping[str, Any] | None = None
    device_communications: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "TelemetryBatchCommand":
        readings = {
            family: tuple(dict(reading) for reading in data.get(family, ()))
            for family in TELEMETRY_READING_FAMILIES
        }
        location = data.get("location")
        device_runtime = data.get("device_runtime")
        device_communications = data.get("device_communications")
        return cls(
            device_id=data.get("device_id"),
            readings=readings,
            location=dict(location) if location is not None else None,
            device_runtime=(
                dict(device_runtime) if device_runtime is not None else None
            ),
            device_communications=(
                dict(device_communications)
                if device_communications is not None
                else None
            ),
        )

    def as_json_mapping(self) -> dict[str, Any]:
        """Return a JSON-ready representation suitable for durable queue storage."""
        data = {
            "device_id": self.device_id,
            **{family: list(self.readings[family]) for family in TELEMETRY_READING_FAMILIES},
            "location": self.location,
            "device_runtime": self.device_runtime,
            "device_communications": self.device_communications,
        }
        return _json_compatible(data)
