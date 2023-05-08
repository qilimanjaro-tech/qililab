"""This file tests the the ``InstrumentController`` class"""
import pytest

from qililab.platform import Platform
from qililab.system_control.readout_system_control import ReadoutSystemControl


@pytest.fixture(name="system_control")
def fixture_system_control(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {
        "id_": 1,
        "category": "system_control",
        "instruments": ["QCM", "rs_1"],
    }
    return ReadoutSystemControl(settings=settings, platform_instruments=platform.instruments)


class TestReadoutSystemControl:
    """This class contains the unit tests for the ``ReadoutSystemControl`` class."""

    def test_error_raises_when_no_awg(self, system_control):
        """Testing that an error raises if a readout system control does not have an AWG

        Args:
            system_control (_type_): _description_
        """
        name = system_control.name
        with pytest.raises(ValueError, match=f"The system control {name} doesn't have an AWG instrument."):
            system_control.acquisition_delay_time  # pylint: disable=pointless-statement
