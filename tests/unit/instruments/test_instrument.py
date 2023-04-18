"""Tests for the SystemControl class."""

import pytest
from qililab.platform import Platform
from qililab.system_control import SystemControl


@pytest.fixture(name="system_control")
def fixture_system_control(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {
        "id_": 1,
        "category": "system_control",
        "instruments": ["QCM", "rs_1"],
    }
    return SystemControl(settings=settings, platform_instruments=platform.instruments)

class TestInstument:
    """Unit tests checking the ``SystemControl`` methods."""

    def test_error_raises_instrument_not_connected(self, system_control: SystemControl):
        """"Test Parameter error raises if the parameter is not found."""
        with pytest.raises(ValueError, match="Instrument QCM is not connected and cannot set the new value: 45 to the parameter voltage."):
            system_control.set_parameter(parameter = 'voltage', value = '45', channel_id = 1)