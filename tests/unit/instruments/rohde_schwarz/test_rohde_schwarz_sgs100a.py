"""Tests for the SGS100A class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.rohde_schwarz.sgs100a_controller import SGS100AController
from qililab.instruments import SGS100A
from qililab.platform import Platform
from qililab.typings.enums import Parameter
from tests.data import Galadriel


@pytest.fixture(name="rohde_schwarz_controller")
def fixture_rohde_schwarz_controller(platform: Platform):
    """Return an instance of SGS100A controller class"""
    settings = copy.deepcopy(Galadriel.rohde_schwarz_controller_0)
    settings.pop("name")
    return SGS100AController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="rohde_schwarz_no_device")
def fixture_rohde_schwarz_no_device():
    """Return an instance of SGS100A class"""
    settings = copy.deepcopy(Galadriel.rohde_schwarz_0)
    settings.pop("name")
    return SGS100A(settings=settings)


@pytest.fixture(name="rohde_schwarz")
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
def fixture_rohde_schwarz(mock_rs: MagicMock, rohde_schwarz_controller: SGS100AController):
    """Return connected instance of SGS100A class"""
    # add dynamically created attributes
    mock_instance = mock_rs.return_value
    mock_instance.mock_add_spec(["power", "frequency", "rf_on"])
    rohde_schwarz_controller.connect()
    return rohde_schwarz_controller.modules[0]


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
