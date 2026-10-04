from datetime import timezone

import pytest

from app.application.buoy_registration import register_buoy
from app.domain.buoy import BuoyRegistrationCommand


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


@pytest.mark.parametrize(
    "name, latitude, longitude",
    [
        ("", None, None),
        ("x" * 101, None, None),
        ("Buoy", 90.01, None),
        ("Buoy", None, -180.01),
    ],
)
def test_registration_command_rejects_values_outside_domain_bounds(
    name, latitude, longitude
):
    with pytest.raises(ValueError):
        BuoyRegistrationCommand(name, latitude, longitude)
