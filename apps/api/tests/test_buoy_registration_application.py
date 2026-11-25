from datetime import timezone

import pytest

from app.application.buoy_registration import (
    register_buoy,
    register_buoy_and_publish_heartbeat,
)
from app.domain.fleet.buoy import BuoyRegistrationCommand


class FakeBuoyRegistrar:
    def register_buoy(self, buoy):
        self.buoy = buoy
        return buoy


def test_registration_assigns_generated_identity_and_persists_domain_snapshot():
    registrar = FakeBuoyRegistrar()

    buoy = register_buoy(
        registrar,
        BuoyRegistrationCommand("New buoy", 36.7, 3.1),
    )

    assert buoy.buoy_id.startswith("TW-")
    assert len(buoy.buoy_id) == 11
    assert buoy.name == "New buoy"
    assert buoy.latitude == 36.7
    assert buoy.longitude == 3.1
    assert buoy.status == "active"
    assert buoy.created_at.tzinfo == timezone.utc
    assert registrar.buoy is buoy


def test_registration_publishes_initial_heartbeat_after_persisting():
    events = []

    class Registrar:
        def register_buoy(self, buoy):
            events.append(("register_buoy", buoy))
            return buoy

    class Metrics:
        def record_buoy_heartbeat(self, buoy_id, last_seen_at):
            events.append(("record_buoy_heartbeat", buoy_id, last_seen_at))

    buoy = register_buoy_and_publish_heartbeat(
        Registrar(), Metrics(), BuoyRegistrationCommand("New buoy", 36.7, 3.1)
    )

    assert buoy.buoy_id.startswith("TW-")
    assert [event[0] for event in events] == [
        "register_buoy",
        "record_buoy_heartbeat",
    ]
    assert events[-1] == ("record_buoy_heartbeat", buoy.buoy_id, None)


@pytest.mark.parametrize(
    "name, latitude, longitude",
    [
        ("", None, None),
        ("   ", None, None),
        ("x" * 101, None, None),
        ("Buoy", 90.01, None),
        ("Buoy", None, -180.01),
        ("Buoy", 36.7, None),
        ("Buoy", None, 3.1),
    ],
)
def test_registration_command_rejects_values_outside_domain_bounds(
    name, latitude, longitude
):
    with pytest.raises(ValueError):
        BuoyRegistrationCommand(name, latitude, longitude)
