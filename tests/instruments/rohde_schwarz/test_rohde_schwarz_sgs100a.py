"""Tests for the SGS100A class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.rohde_schwarz.sgs100a_controller import SGS100AController
from qililab.instruments import SGS100A
from qililab.platform import Platform
from qililab.typings.enums import Parameter
from tests.data import Galadriel
from tests.test_utils import build_platform

@pytest.fixture(name="sdg100a")
def fixture_sdg100a() -> SGS100A:
    """Fixture that returns an instance of a dummy QDAC-II."""
    sdg100a = SGS100A(
        {
            "alias": "qdac",
            "power": 100,
            "frequency": 1e6,
            "rf_on": True
        }
    )
    sdg100a.device = MagicMock()
    return sdg100a

class TestSGS100A:
    """Unit tests checking the SGS100A attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [(Parameter.POWER, 0.01), (Parameter.LO_FREQUENCY, 6.0e09), (Parameter.RF_ON, True), (Parameter.RF_ON, False)],
    )
    def test_set_parameter_method(
        self, sdg100a: SGS100A, parameter: Parameter, value: float,
    ):
        """Test setup method"""
        sdg100a.set_parameter(parameter=parameter, value=value)
        if parameter == Parameter.POWER:
            assert sdg100a.settings.power == value
        if parameter == Parameter.LO_FREQUENCY:
            assert sdg100a.settings.frequency == value
        if parameter == Parameter.RF_ON:
            assert sdg100a.settings.rf_on == value

    def test_initial_setup_method(self, sdg100a: SGS100A):
        """Test initial setup method"""
        sdg100a.initial_setup()
        sdg100a.device.power.assert_called_with(sdg100a.power)
        sdg100a.device.frequency.assert_called_with(sdg100a.frequency)
        if sdg100a.rf_on:
            sdg100a.device.on.assert_called_once()
        else:
            sdg100a.device.off.assert_called_once()

    def test_turn_on_method(self, sdg100a: SGS100A):
        """Test turn_on method"""
        sdg100a.turn_on()
        assert sdg100a.settings.rf_on is True
        sdg100a.device.on.assert_called_once()

    def test_turn_off_method(self, sdg100a: SGS100A):
        """Test turn_off method"""
        sdg100a.turn_off()
        assert sdg100a.settings.rf_on is False
        sdg100a.device.off.assert_called_once()

    def test_reset_method(self, sdg100a: SGS100A):
        """Test reset method"""
        sdg100a.reset()
