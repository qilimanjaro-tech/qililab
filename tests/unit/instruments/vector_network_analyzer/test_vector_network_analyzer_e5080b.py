"""Test for the VectorNetworkAnalyzer E5080B class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller import E5080BController
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.platform import Platform
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import Parameter, VNAScatteringParameters, VNASweepModes, VNATriggerModes
from tests.data import SauronVNA


@pytest.fixture(name="vector_network_analyzer_controller")
def fixture_vector_network_analyzer_controller(sauron_platform: Platform):
    """Return an instance of VectorNetworkAnalyzer controller class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b_controller)
    settings.pop("name")
    return E5080BController(settings=settings, loaded_instruments=sauron_platform.instruments)


@pytest.fixture(name="vector_network_analyzer_no_device")
def fixture_vector_network_analyzer_no_device():
    """Return an instance of VectorNetworkAnalyzer class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b)
    settings.pop("name")
    return E5080B(settings=settings)


@pytest.fixture(name="vector_network_analyzer")
@patch(
    "qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller.E5080BDriver",
    autospec=True,
)
def fixture_vector_network_analyzer(mock_device: MagicMock, vector_network_analyzer_controller: E5080BController):
    """Return connected instance of VectorNetworkAnalyzer class"""
    mock_instance = mock_device.return_value
    mock_instance.mock_add_spec(["power"])
    vector_network_analyzer_controller.connect()
    mock_device.assert_called()
    return vector_network_analyzer_controller.modules[0]


class TestE5080B:
    """Unit tests checking the VectorNetworkAnalyzer attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.POWER, -15.0),
            (Parameter.FREQUENCY_SPAN, 6.4e-3),
            (Parameter.FREQUENCY_CENTER, 8.5e-3),
            (Parameter.FREQUENCY_START, 27.5),
            (Parameter.FREQUENCY_STOP, 40.5),
            (Parameter.IF_BANDWIDTH, 50.0),
            (Parameter.DEVICE_TIMEOUT, 100.0),
            (Parameter.ELECTRICAL_DELAY, 0.0),
        ],
    )
    def test_setup_method_value_flt(self, parameter: Parameter, value, vector_network_analyzer: E5080B):
        """Test the setup method with float value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, float)
        vector_network_analyzer.setup(parameter, value)
        if parameter == Parameter.POWER:
            assert vector_network_analyzer.power == value
        if parameter == Parameter.FREQUENCY_SPAN:
            assert vector_network_analyzer.frequency_span == value
        if parameter == Parameter.FREQUENCY_CENTER:
            assert vector_network_analyzer.frequency_center == value
        if parameter == Parameter.FREQUENCY_START:
            assert vector_network_analyzer.frequency_start == value
        if parameter == Parameter.FREQUENCY_STOP:
            assert vector_network_analyzer.frequency_stop == value
        if parameter == Parameter.IF_BANDWIDTH:
            assert vector_network_analyzer.if_bandwidth == value
        if parameter == Parameter.DEVICE_TIMEOUT:
            assert vector_network_analyzer.device_timeout == value
        if parameter == Parameter.ELECTRICAL_DELAY:
            assert vector_network_analyzer.electrical_delay == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.TRIGGER_MODE, "INT"),
            (Parameter.SCATTERING_PARAMETER, "S21"),
            (Parameter.SWEEP_MODE, "cont"),
            (Parameter.SWEEP_MODE, "hold"),
        ],
    )
    def test_setup_method_value_str(self, parameter: Parameter, value, vector_network_analyzer: E5080B):
        """Test the setup method with str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        vector_network_analyzer.setup(parameter, value)
        if parameter == Parameter.TRIGGER_MODE:
            assert vector_network_analyzer.trigger_mode == VNATriggerModes(value)
        if parameter == Parameter.SCATTERING_PARAMETER:
            assert vector_network_analyzer.scattering_parameter == VNAScatteringParameters(value)
        if parameter == Parameter.SWEEP_MODE:
            assert vector_network_analyzer.sweep_mode == VNASweepModes(value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.SCATTERING_PARAMETER, "S221"),
            (Parameter.SCATTERING_PARAMETER, "s11"),
            (Parameter.SWEEP_MODE, "CONT"),
            (Parameter.SWEEP_MODE, "sweep_mode continuous"),
        ],
    )
    def test_setup_method_value_str_raises_exception(
        self, parameter: Parameter, value, vector_network_analyzer: E5080B
    ):
        """Test the setup method raises exception with incorrect str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        with pytest.raises(Exception):
            vector_network_analyzer.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value", [(Parameter.AVERAGING_ENABLED, True), (Parameter.AVERAGING_ENABLED, False)]
    )
    def test_setup_method_value_bool(self, parameter: Parameter, value, vector_network_analyzer: E5080B):
        """Test the setup method with bool value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, bool)
        vector_network_analyzer.setup(parameter, value)
        if parameter == Parameter.AVERAGING_ENABLED:
            vector_network_analyzer.averaging_enabled == value

    @pytest.mark.parametrize("parameter, value", [(Parameter.NUMBER_POINTS, 100), (Parameter.NUMBER_AVERAGES, 4)])
    def test_setup_method_value_int(self, parameter: Parameter, value, vector_network_analyzer: E5080B):
        """Test the setup method with int value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, int)
        vector_network_analyzer.setup(parameter, value)
        if parameter == Parameter.NUMBER_POINTS:
            assert vector_network_analyzer.number_points == value
        if parameter == Parameter.NUMBER_AVERAGES:
            assert vector_network_analyzer.number_averages == value

    def test_initial_setup_method(self, vector_network_analyzer: E5080B):
        """Test the initial setup method"""
        vector_network_analyzer.initial_setup()
        vector_network_analyzer.device.initial_setup.assert_called()

    def test_reset_method(self, vector_network_analyzer: E5080B):
        """Test reset method"""
        vector_network_analyzer.reset()
        vector_network_analyzer.device.reset.assert_called()

    def test_turn_on_method(self, vector_network_analyzer: E5080B):
        """Test the turn on method"""
        vector_network_analyzer.turn_on()
        vector_network_analyzer.device.start.assert_called()

    def test_turn_off_method(self, vector_network_analyzer: E5080B):
        """Test the turn off method"""
        vector_network_analyzer.turn_off()
        vector_network_analyzer.device.stop.assert_called()

    @pytest.mark.parametrize("command", [":SENS1:AVER:CLE", "SENS1:AVER:COUN 3"])
    def test_send_command_method(self, command: str, vector_network_analyzer: E5080B):
        """Test the send command method"""
        vector_network_analyzer.send_command(command)
        vector_network_analyzer.device.send_command.assert_called_with(command=command, arg="")

    def test_autoscale_method(self, vector_network_analyzer: E5080B):
        """Test autoscale method"""
        vector_network_analyzer.autoscale()
        vector_network_analyzer.device.autoscale.assert_called()

    @pytest.mark.parametrize("arg", ["ON", "OFF", 1, 0])
    def test_output_method(self, arg: str | int, vector_network_analyzer: E5080B):
        """Test output method"""
        vector_network_analyzer.output(arg)
        vector_network_analyzer.device.output.assert_called_with(arg)

    @pytest.mark.parametrize("arg", ["On", "Off", 1.0, [0]])
    def test_output_method_fails(self, arg: str | int, vector_network_analyzer: E5080B):
        """Test output method fails"""
        with pytest.raises(Exception):
            vector_network_analyzer.output(arg)

    def test_average_clear_method(self, vector_network_analyzer: E5080B):
        """Test the average clear method"""
        vector_network_analyzer.average_clear()
        vector_network_analyzer.device.average_clear.assert_called()

    def test_get_frequencies_method(self, vector_network_analyzer: E5080B):
        """Test the get frequencies method"""
        vector_network_analyzer.get_frequencies()
        vector_network_analyzer.device.get_freqs.assert_called()

    def test_ready_method(self, vector_network_analyzer: E5080B):
        """Test ready method"""
        vector_network_analyzer.ready()
        vector_network_analyzer.device.ready.assert_called()

    def test_release_method(self, vector_network_analyzer: E5080B):
        """Test release method"""
        vector_network_analyzer.release()
        assert vector_network_analyzer.settings.sweep_mode == VNASweepModes("cont")
        vector_network_analyzer.device.release.assert_called()

    def test_read_tracedata_method(self, vector_network_analyzer: E5080B):
        """Test the read tracedata method"""
        output = vector_network_analyzer.read_tracedata()
        vector_network_analyzer.device.read_tracedata.assert_called()
        assert output is not None

    def test_acquire_result_method(self, vector_network_analyzer: E5080B):
        """Test the acquire result method"""
        output = vector_network_analyzer.acquire_result()
        vector_network_analyzer.device.read_tracedata.assert_called()
        assert isinstance(output, VNAResult)

    def test_power_property(self, vector_network_analyzer_no_device: E5080B):
        """Test power property."""
        assert hasattr(vector_network_analyzer_no_device, "power")
        assert vector_network_analyzer_no_device.power == vector_network_analyzer_no_device.settings.power

    def test_scattering_parameter_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the scattering parametter property"""
        assert hasattr(vector_network_analyzer_no_device, "scattering_parameter")
        assert (
            vector_network_analyzer_no_device.scattering_parameter
            == vector_network_analyzer_no_device.settings.scattering_parameter
        )

    def test_frequency_span_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the frequency span property"""
        assert hasattr(vector_network_analyzer_no_device, "frequency_span")
        assert (
            vector_network_analyzer_no_device.frequency_span
            == vector_network_analyzer_no_device.settings.frequency_span
        )

    def test_frequency_center_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the frequency center property"""
        assert hasattr(vector_network_analyzer_no_device, "frequency_center")
        assert (
            vector_network_analyzer_no_device.frequency_center
            == vector_network_analyzer_no_device.settings.frequency_center
        )

    def test_frequency_start_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the frequency start property"""
        assert hasattr(vector_network_analyzer_no_device, "frequency_start")
        assert (
            vector_network_analyzer_no_device.frequency_start
            == vector_network_analyzer_no_device.settings.frequency_start
        )

    def test_frequency_stop_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the frequency stop property"""
        assert hasattr(vector_network_analyzer_no_device, "frequency_stop")
        assert (
            vector_network_analyzer_no_device.frequency_stop
            == vector_network_analyzer_no_device.settings.frequency_stop
        )

    def test_if_bandwidth_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the if bandwidth property"""
        assert hasattr(vector_network_analyzer_no_device, "if_bandwidth")
        assert vector_network_analyzer_no_device.if_bandwidth == vector_network_analyzer_no_device.settings.if_bandwidth

    def test_averaging_enabled_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the averaging enabled property"""
        assert hasattr(vector_network_analyzer_no_device, "averaging_enabled")
        assert (
            vector_network_analyzer_no_device.averaging_enabled
            == vector_network_analyzer_no_device.settings.averaging_enabled
        )

    def test_number_averages_propertyy(self, vector_network_analyzer_no_device: E5080B):
        """Test the number of averages property"""
        assert hasattr(vector_network_analyzer_no_device, "number_averages")
        assert (
            vector_network_analyzer_no_device.number_averages
            == vector_network_analyzer_no_device.settings.number_averages
        )

    def test_trigger_mode_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the trigger mode property"""
        assert hasattr(vector_network_analyzer_no_device, "trigger_mode")
        assert vector_network_analyzer_no_device.trigger_mode == vector_network_analyzer_no_device.settings.trigger_mode

    def test_number_points_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the number points property"""
        assert hasattr(vector_network_analyzer_no_device, "number_points")
        assert (
            vector_network_analyzer_no_device.number_points == vector_network_analyzer_no_device.settings.number_points
        )

    def test_sweep_mode_property(self, vector_network_analyzer: E5080B):
        """Test the sweep mode property"""
        assert hasattr(vector_network_analyzer, "sweep_mode")
        assert vector_network_analyzer.sweep_mode == vector_network_analyzer.settings.sweep_mode

    def test_device_timeout_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the device timeout property"""
        assert hasattr(vector_network_analyzer_no_device, "device_timeout")
        assert (
            vector_network_analyzer_no_device.device_timeout
            == vector_network_analyzer_no_device.settings.device_timeout
        )

    def test_electrical_delay_property(self, vector_network_analyzer_no_device: E5080B):
        """Test the electrical delay property"""
        assert hasattr(vector_network_analyzer_no_device, "electrical_delay")
        assert (
            vector_network_analyzer_no_device.electrical_delay
            == vector_network_analyzer_no_device.settings.electrical_delay
        )
