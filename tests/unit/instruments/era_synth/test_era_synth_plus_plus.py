"""Tests for the EraSynthPlusPlus class."""
import pytest

from qililab.instruments import EraSynthPlusPlus
from qililab.typings.enums import Parameter


class TestEraSynthPlusPlus:
    """Unit tests checking the EraSynthPlusPlus attributes and methods"""

    @pytest.mark.parametrize("parameter, value", [(Parameter.POWER, 0.01), (Parameter.LO_FREQUENCY, 6.0e09)])
    def test_setup_method(self, parameter: Parameter, value: float, era: EraSynthPlusPlus):
        """Test setup method"""
        era.setup(parameter=parameter, value=value)
        if parameter == Parameter.POWER:
            assert era.settings.power == value
        if parameter == Parameter.LO_FREQUENCY:
            assert era.settings.frequency == value

    def test_initial_setup_method(self, era: EraSynthPlusPlus):
        """Test initial setup method"""
        era.initial_setup()
        era.device.power.assert_called_with(era.power)
        era.device.frequency.assert_called_with(era.frequency)

    def test_turn_on_method(self, era: EraSynthPlusPlus):
        """Test turn_on method"""
        era.turn_on()
        era.device.on.assert_called_once()  # type: ignore

    def test_turn_off_method(self, era: EraSynthPlusPlus):
        """Test turn_off method"""
        era.turn_off()
        era.device.off.assert_called_once()  # type: ignore

    def test_reset_method(self, era: EraSynthPlusPlus):
        """Test reset method"""
        era.reset()
