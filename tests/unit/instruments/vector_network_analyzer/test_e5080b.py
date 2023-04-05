"""Test for the VectorNetworkAnalyzer E5080B class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller import E5080BController
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.platform import Platform
from qililab.typings.enums import Parameter, VNAScatteringParameters, VNASweepModes, VNATriggerModes
from tests.data import SauronVNA


@pytest.fixture(name="e5080b_controller")
def fixture_e5080b_controller(sauron_platform: Platform):
    """Return an instance of VectorNetworkAnalyzer controller class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b_controller)
    settings.pop("name")
    return E5080BController(settings=settings, loaded_instruments=sauron_platform.instruments)


@pytest.fixture(name="e5080b_no_device")
def fixture_e5080b_no_device():
    """Return an instance of VectorNetworkAnalyzer class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b)
    settings.pop("name")
    return E5080B(settings=settings)


@pytest.fixture(name="e5080b")
@patch(
    "qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller.E5080BDriver",
    autospec=True,
)
def fixture_e5080b(mock_device: MagicMock, e5080b_controller: E5080BController):
    """Return connected instance of VectorNetworkAnalyzer class"""
    mock_instance = mock_device.return_value
    mock_instance.mock_add_spec(["power"])
    e5080b_controller.connect()
    mock_device.assert_called()
    return e5080b_controller.modules[0]


class TestE5080B:
    """Unit tests checking the VectorNetworkAnalyzer E5080B attributes and methods"""

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
    def test_setup_method_value_flt(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with float value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, float)
        e5080b.setup(parameter, value)
        if parameter == Parameter.POWER:
            assert e5080b.power == value
        if parameter == Parameter.FREQUENCY_SPAN:
            assert e5080b.frequency_span == value
        if parameter == Parameter.FREQUENCY_CENTER:
            assert e5080b.frequency_center == value
        if parameter == Parameter.FREQUENCY_START:
            assert e5080b.frequency_start == value
        if parameter == Parameter.FREQUENCY_STOP:
            assert e5080b.frequency_stop == value
        if parameter == Parameter.IF_BANDWIDTH:
            assert e5080b.if_bandwidth == value
        if parameter == Parameter.DEVICE_TIMEOUT:
            assert e5080b.device_timeout == value
        if parameter == Parameter.ELECTRICAL_DELAY:
            assert e5080b.electrical_delay == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.TRIGGER_MODE, "INT"),
            (Parameter.SCATTERING_PARAMETER, "S21"),
            (Parameter.SWEEP_MODE, "cont"),
            (Parameter.SWEEP_MODE, "hold"),
        ],
    )
    def test_setup_method_value_str(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        e5080b.setup(parameter, value)
        if parameter == Parameter.TRIGGER_MODE:
            assert e5080b.trigger_mode == VNATriggerModes(value)
        if parameter == Parameter.SCATTERING_PARAMETER:
            assert e5080b.scattering_parameter == VNAScatteringParameters(value)
        if parameter == Parameter.SWEEP_MODE:
            assert e5080b.sweep_mode == VNASweepModes(value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.SCATTERING_PARAMETER, "S221"),
            (Parameter.SCATTERING_PARAMETER, "s11"),
            (Parameter.SWEEP_MODE, "CONT"),
            (Parameter.SWEEP_MODE, "sweep_mode continuous"),
        ],
    )
    def test_setup_method_value_str_raises_exception(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method raises exception with incorrect str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        with pytest.raises(Exception):
            e5080b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value", [(Parameter.AVERAGING_ENABLED, True), (Parameter.AVERAGING_ENABLED, False)]
    )
    def test_setup_method_value_bool(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with bool value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, bool)
        e5080b.setup(parameter, value)
        if parameter == Parameter.AVERAGING_ENABLED:
            assert e5080b.averaging_enabled == value

    @pytest.mark.parametrize("parameter, value", [(Parameter.NUMBER_POINTS, 100), (Parameter.NUMBER_AVERAGES, 4)])
    def test_setup_method_value_int(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with int value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, int)
        e5080b.setup(parameter, value)
        if parameter == Parameter.NUMBER_POINTS:
            assert e5080b.number_points == value
        if parameter == Parameter.NUMBER_AVERAGES:
            assert e5080b.number_averages == value

    def test_get_sweep_mode_method(self, e5080b: E5080B):
        """Test the get sweep mode method"""
        output = e5080b._get_sweep_mode()
        e5080b.device.send_query.assert_called()
        assert isinstance(output, str)

    def test_get_trace_method(self, e5080b: E5080B):
        """Test auxiliarty private method get trace."""
        e5080b._get_trace()
        e5080b.device.send_command.assert_called()
        e5080b.device.send_binary_query.assert_called_once()

    @pytest.mark.parametrize(
        "state, command, arg", [(True, "SENS1:AVER:STAT", "ON"), (False, "SENS1:AVER:STAT", "OFF")]
    )
    def test_average_state_method(self, state, command, arg, e5080b: E5080B):
        """Test the auxiliary private method average state"""
        e5080b._average_state(state)
        e5080b.device.send_command.assert_called_with(command=command, arg=arg)

    def test_average_count_method(self, e5080b: E5080B):
        """Set the average count"""
        e5080b._average_count(1, 1)  # Have to know if you can select which one was called
        e5080b.device.send_command.assert_called()

    @pytest.mark.parametrize("count", ["1", "3", "5"])
    def test_set_count_method(self, count: str, e5080b: E5080B):
        """Test the auxiliary private method set count"""
        e5080b._set_count(count)
        e5080b.device.send_command.assert_called_with(command="SENS1:SWE:GRO:COUN", arg=count)

    def test_pre_measurement_method(self, e5080b: E5080B):
        """Test the auxiliary private method pre measurment"""
        e5080b._pre_measurement()
        assert e5080b.averaging_enabled

    def test_start_measurement_method(self, e5080b: E5080B):
        """Test the auxiliary private method start measurment"""
        e5080b._start_measurement()
        assert e5080b.sweep_mode == VNASweepModes("group")

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    def test_wait_until_ready_method(self, mock_ready, e5080b: E5080B):
        """Test the auxiliary private method wait until ready"""
        mock_ready.return_value = True
        output = e5080b._wait_until_ready()
        assert isinstance(output, bool)

    def test_average_clear_method(self, e5080b: E5080B):
        """Test the average clear method"""
        e5080b.average_clear()
        e5080b.device.send_command.assert_called()

    def test_get_frequencies_method(self, e5080b: E5080B):
        """Test the get frequencies method"""
        e5080b.get_frequencies()
        e5080b.device.send_binary_query.assert_called()

    def test_ready_method(self, e5080b: E5080B):
        """Test ready method"""
        output = e5080b.ready()
        assert isinstance(output, bool)

    def test_release_method(self, e5080b: E5080B):
        """Test release method"""
        e5080b.release()
        assert e5080b.settings.sweep_mode == VNASweepModes("cont")

    def test_autoscale_method(self, e5080b: E5080B):
        """Test the autoscale method"""
        e5080b.autoscale()
        e5080b.device.send_command.assert_called_with(command="DISP:WIND:TRAC:Y:AUTO", arg="")

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    def test_read_tracedata_method(self, mock_ready, e5080b: E5080B):
        """Test the read tracedata method"""
        mock_ready.return_value = True
        output = e5080b.read_tracedata()
        assert output is not None

    def test_power_property(self, e5080b_no_device: E5080B):
        """Test power property."""
        assert hasattr(e5080b_no_device, "power")
        assert e5080b_no_device.power == e5080b_no_device.settings.power

    def test_scattering_parameter_property(self, e5080b_no_device: E5080B):
        """Test the scattering parametter property"""
        assert hasattr(e5080b_no_device, "scattering_parameter")
        assert e5080b_no_device.scattering_parameter == e5080b_no_device.settings.scattering_parameter

    def test_frequency_span_property(self, e5080b_no_device: E5080B):
        """Test the frequency span property"""
        assert hasattr(e5080b_no_device, "frequency_span")
        assert e5080b_no_device.frequency_span == e5080b_no_device.settings.frequency_span

    def test_frequency_center_property(self, e5080b_no_device: E5080B):
        """Test the frequency center property"""
        assert hasattr(e5080b_no_device, "frequency_center")
        assert e5080b_no_device.frequency_center == e5080b_no_device.settings.frequency_center

    def test_frequency_start_property(self, e5080b_no_device: E5080B):
        """Test the frequency start property"""
        assert hasattr(e5080b_no_device, "frequency_start")
        assert e5080b_no_device.frequency_start == e5080b_no_device.settings.frequency_start

    def test_frequency_stop_property(self, e5080b_no_device: E5080B):
        """Test the frequency stop property"""
        assert hasattr(e5080b_no_device, "frequency_stop")
        assert e5080b_no_device.frequency_stop == e5080b_no_device.settings.frequency_stop

    def test_if_bandwidth_property(self, e5080b_no_device: E5080B):
        """Test the if bandwidth property"""
        assert hasattr(e5080b_no_device, "if_bandwidth")
        assert e5080b_no_device.if_bandwidth == e5080b_no_device.settings.if_bandwidth

    def test_averaging_enabled_property(self, e5080b_no_device: E5080B):
        """Test the averaging enabled property"""
        assert hasattr(e5080b_no_device, "averaging_enabled")
        assert e5080b_no_device.averaging_enabled == e5080b_no_device.settings.averaging_enabled

    def test_number_averages_propertyy(self, e5080b_no_device: E5080B):
        """Test the number of averages property"""
        assert hasattr(e5080b_no_device, "number_averages")
        assert e5080b_no_device.number_averages == e5080b_no_device.settings.number_averages

    def test_trigger_mode_property(self, e5080b_no_device: E5080B):
        """Test the trigger mode property"""
        assert hasattr(e5080b_no_device, "trigger_mode")
        assert e5080b_no_device.trigger_mode == e5080b_no_device.settings.trigger_mode

    def test_number_points_property(self, e5080b_no_device: E5080B):
        """Test the number points property"""
        assert hasattr(e5080b_no_device, "number_points")
        assert e5080b_no_device.number_points == e5080b_no_device.settings.number_points

    def test_sweep_mode_property(self, e5080b: E5080B):
        """Test the sweep mode property"""
        assert hasattr(e5080b, "sweep_mode")
        assert e5080b.sweep_mode == e5080b.settings.sweep_mode

    def test_device_timeout_property(self, e5080b_no_device: E5080B):
        """Test the device timeout property"""
        assert hasattr(e5080b_no_device, "device_timeout")
        assert e5080b_no_device.device_timeout == e5080b_no_device.settings.device_timeout

    def test_electrical_delay_property(self, e5080b_no_device: E5080B):
        """Test the electrical delay property"""
        assert hasattr(e5080b_no_device, "electrical_delay")
        assert e5080b_no_device.electrical_delay == e5080b_no_device.settings.electrical_delay
