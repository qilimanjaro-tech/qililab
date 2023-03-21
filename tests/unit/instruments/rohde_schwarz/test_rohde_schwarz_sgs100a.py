"""Tests for the SGS100A class."""
import pytest

from qililab.instruments import SGS100A
from qililab.typings.enums import Parameter


class TestSGS100A:
    """Unit tests checking the SGS100A attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [(Parameter.POWER, 0.01), (Parameter.LO_FREQUENCY, 6.0e09), (Parameter.RF_ON, True), (Parameter.RF_ON, False)],
    )
    def test_setup_method(self, parameter: Parameter, value: float, rohde_schwarz: SGS100A):
        """Test setup method"""
        rohde_schwarz.setup(parameter=parameter, value=value)
        if parameter == Parameter.POWER:
            assert rohde_schwarz.settings.power == value
        if parameter == Parameter.LO_FREQUENCY:
            assert rohde_schwarz.settings.frequency == value
        if parameter == Parameter.RF_ON:
            assert rohde_schwarz.settings.rf_on == value

    @pytest.mark.parametrize("rf_on", [True, False])
    def test_initial_setup_method(self, rf_on: bool, rohde_schwarz: SGS100A):
        """Test initial setup method"""
        rohde_schwarz.setup(Parameter.RF_ON, rf_on)
        rohde_schwarz.initial_setup()
        rohde_schwarz.device.power.assert_called_with(rohde_schwarz.power)
        rohde_schwarz.device.frequency.assert_called_with(rohde_schwarz.frequency)
        if rohde_schwarz.rf_on:
            assert rohde_schwarz.settings.rf_on is True
            rohde_schwarz.device.on.assert_called()  # type: ignore
        else:
            assert rohde_schwarz.settings.rf_on is False
            rohde_schwarz.device.off.assert_called()  # type: ignore

    def test_turn_on_method(self, rohde_schwarz: SGS100A):
        """Test turn_on method"""
        rohde_schwarz.turn_on()
        assert rohde_schwarz.settings.rf_on is True
        rohde_schwarz.device.on.assert_called_once()  # type: ignore

    def test_turn_off_method(self, rohde_schwarz: SGS100A):
        """Test turn_off method"""
        rohde_schwarz.turn_off()
        assert rohde_schwarz.settings.rf_on is False
        rohde_schwarz.device.off.assert_called_once()  # type: ignore

    def test_reset_method(self, rohde_schwarz: SGS100A):
        """Test reset method"""
        rohde_schwarz.reset()
