from datetime import datetime, timezone
from types import SimpleNamespace

from app.application.temperature_alerts import to_stored_temperature_alert


def test_temperature_alert_mapping_preserves_persisted_values() -> None:
    created_at = datetime.now(timezone.utc)
    alert = SimpleNamespace(
        id=4,
        buoy_id="buoy-1",
        buoy=SimpleNamespace(name="North buoy"),
        severity="warning",
        temperature_celsius=28.5,
        average_temperature=21.0,
        created_at=created_at,
        message="Temperature anomaly detected",
        status="open",
        resolved_at=None,
    )

    result = to_stored_temperature_alert(alert)

    assert result.id == 4
    assert result.buoy_name == "North buoy"
    assert result.temperature_celsius == 28.5
    assert result.created_at == created_at
    assert result.status == "open"
