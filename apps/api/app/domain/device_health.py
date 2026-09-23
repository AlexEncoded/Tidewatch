"""Domain snapshot for the operational health of a physical device."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class DeviceHealthSnapshot:
    buoy_id: str
    device_id: str
    sensor_channel: Literal["A", "B"]
    status: Literal["active", "maintenance", "inactive"]
    is_stale: bool
    last_seen_at: datetime | None = None
    age_seconds: float | None = None
