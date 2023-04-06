"""Tests for the SGS100A class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.yokogawa.gs200_controller import GS200Controller
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.yokogawa.gs200 import GS200
from qililab.platform import Platform
from qililab.typings.enums import Parameter, YokogawaSourceModes
from tests.data import Galadriel, SauronYokogawa


@pytest.fixture(name="yokogawa_gs200_controller")
def fixture_yokogawa_gs200_controller(sauron_yoko_platform: Platform):
    """Return an instance of GS200 controller class"""
    settings = copy.deepcopy(SauronYokogawa.yokogawa_gs200_controller)
    settings.pop("name")
    return GS200Controller(settings=settings, loaded_instruments=sauron_yoko_platform.instruments)


@pytest.fixture(name="yokogawa_gs200")
@patch("qililab.instrument_controllers.yokogawa.gs200_controller.YokogawaGS200", autospec=True)
def fixture_yokogawa_gs200(mock_rs: MagicMock, yokogawa_gs200_controller: GS200Controller):
    """Return connected instance of GS200 class"""
    # add dynamically created attributes
    mock_instance = mock_rs.return_value
    mock_instance.mock_add_spec(["output_status", "current_value"])
    yokogawa_gs200_controller.connect()
    return yokogawa_gs200_controller.modules[0]


class TestGS200:
    """Unit tests checking the GS200 attributes and methods"""

    @pytest.mark.parametrize("parameter, value", [(Parameter.CURRENT_VALUE, 0.001), (Parameter.CURRENT_VALUE, 0.0005)])
    def test_setup_method_value_flt(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the setup method with float value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, float)
        yokogawa_gs200.setup(parameter, value)
        if parameter == Parameter.CURRENT_VALUE:
            assert yokogawa_gs200.current_value == value

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.CURRENT, 0.0005)])
    def test_setup_method_value_flt_raises_exception(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the setup method with float value raises an exception with wrong parameters"""
        with pytest.raises(ParameterNotFound):
            yokogawa_gs200.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value", [(Parameter.SOURCE_MODE, "current"), (Parameter.SOURCE_MODE, "voltage")]
    )
    def test_setup_method_value_str(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the setup method with str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        yokogawa_gs200.setup(parameter, value)
        if parameter == Parameter.SOURCE_MODE:
            assert yokogawa_gs200.source_mode == YokogawaSourceModes(value)

    @pytest.mark.parametrize("parameter, value", [(Parameter.GAIN, "foo"), (Parameter.INTEGRATION, "bar")])
    def test_setup_method_value_str_raises_exception(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the setup method with string value raises an exception with wrong parameters"""
        with pytest.raises(ParameterNotFound):
            yokogawa_gs200.setup(parameter, value)

    def test_to_dict_method(self, yokogawa_gs200: GS200):
        """Test the dict method"""
        assert isinstance(yokogawa_gs200.to_dict(), dict)

    @pytest.mark.parametrize("ramp_to, step, delay", [(0.001, 0.0001, 0), (0.001, 0.0001, 1), (0.0001, 0.00005, 10)])
    def test_ramp_current_method(self, ramp_to, step, delay, yokogawa_gs200: GS200):
        """Test the ramp current method"""
        yokogawa_gs200.ramp_current(ramp_to, step, delay)
        yokogawa_gs200.device.ramp_current.assert_called_with(ramp_to=ramp_to, step=step, delay=delay)
        assert yokogawa_gs200.settings.current_value == ramp_to

    def test_start_method(self, yokogawa_gs200: GS200):
        """Test start method"""
        yokogawa_gs200.start()
        yokogawa_gs200.device.on.assert_called()
        assert yokogawa_gs200.settings.output_status

    def test_stop_method(self, yokogawa_gs200: GS200):
        """Test stop method"""
        yokogawa_gs200.stop()
        yokogawa_gs200.device.off.assert_called()
        assert not yokogawa_gs200.settings.output_status

    def test_initial_setup_method(self, yokogawa_gs200: GS200):
        """Test the initial setup method"""
        yokogawa_gs200.initial_setup()
        yokogawa_gs200.device._set_source_mode.assert_called_with(YokogawaSourceModes.CURR.name)

    def test_source_mode_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "source_mode")
        assert yokogawa_gs200.source_mode == yokogawa_gs200.settings.source_mode

    def test_output_status_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "output_status")
        assert yokogawa_gs200.output_status == yokogawa_gs200.settings.output_status

    def test_current_value_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "current_value")
        assert yokogawa_gs200.current_value == yokogawa_gs200.settings.current_value


@pytest.fixture(name="yokogawa_gs200_controller_fail")
def fixture_yokogawa_gs200_controller_fail(platform: Platform):
    """Return an instance of GS200 controller class"""
    settings = copy.deepcopy(Galadriel.pulsar_controller_qcm_0)
    settings.pop("name")
    settings.pop("reference_clock")
    return GS200Controller(settings=settings, loaded_instruments=platform.instruments)


class TestGS200Controller:
    """Unit tests checking the GS200 Controller attributes and methods"""

    def test_check_supported_modules_raises_exception(self, yokogawa_gs200_controller_fail: GS200Controller):
        with pytest.raises(ValueError):
            yokogawa_gs200_controller_fail._check_supported_modules()
