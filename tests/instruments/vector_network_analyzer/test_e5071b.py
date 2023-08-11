"""Test for the VectorNetworkAnalyzer E5071B class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.vector_network_analyzer.agilent_E5071B_vna_controller import E5071BController
from qililab.instruments.agilent.e5071b_vna import E5071B
from qililab.instruments.instrument import ParameterNotFound
from qililab.platform import Platform
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import Parameter, VNAScatteringParameters, VNATriggerModes
from tests.data import SauronVNA
from tests.test_utils import build_platform


@pytest.fixture(name="sauron_platform")
def fixture_sauron_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronVNA.runcard)


@pytest.fixture(name="e5071b_controller")
def fixture_e5071b_controller(sauron_platform: Platform):
    """Return an instance of VectorNetworkAnalyzer controller class"""
    settings = copy.deepcopy(SauronVNA.agilent_e5071b_controller)
    settings.pop("name")
    return E5071BController(settings=settings, loaded_instruments=sauron_platform.instruments)


@pytest.fixture(name="e5071b_no_device")
def fixture_e5071b_no_device():
    """Return an instance of VectorNetworkAnalyzer class"""
    settings = copy.deepcopy(SauronVNA.agilent_e5071b)
    settings.pop("name")
    return E5071B(settings=settings)


@pytest.fixture(name="e5071b")
@patch(
    "qililab.instrument_controllers.vector_network_analyzer.agilent_E5071B_vna_controller.VectorNetworkAnalyzerDriver",
    autospec=True,
)
def fixture_e5071b(mock_device: MagicMock, e5071b_controller: E5071BController):
    """Return connected instance of VectorNetworkAnalyzer class"""
    mock_instance = mock_device.return_value
    mock_instance.mock_add_spec(["power"])
    e5071b_controller.connect()
    mock_device.assert_called()
    return e5071b_controller.modules[0]


class TestE5071B:
    """Unit tests checking the VectorNetworkAnalyzer E5071B attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.POWER, -15.0),
            (Parameter.FREQUENCY_SPAN, 6.4e-3),
            (Parameter.FREQUENCY_CENTER, 8.5e-3),
            (Parameter.FREQUENCY_START, 27.5),
            (Parameter.FREQUENCY_STOP, 40.5),
            (Parameter.IF_BANDWIDTH, 50.0),
            (Parameter.ELECTRICAL_DELAY, 0.0),
        ],
    )
    def test_setup_method_value_flt(self, parameter: Parameter, value, e5071b: E5071B):
        """Test the setup method with float value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, float)
        e5071b.setup(parameter, value)
        if parameter == Parameter.POWER:
            assert e5071b.power == value
        if parameter == Parameter.FREQUENCY_SPAN:
            assert e5071b.frequency_span == value
        if parameter == Parameter.FREQUENCY_CENTER:
            assert e5071b.frequency_center == value
        if parameter == Parameter.FREQUENCY_START:
            assert e5071b.frequency_start == value
        if parameter == Parameter.FREQUENCY_STOP:
            assert e5071b.frequency_stop == value
        if parameter == Parameter.IF_BANDWIDTH:
            assert e5071b.if_bandwidth == value
        if parameter == Parameter.ELECTRICAL_DELAY:
            assert e5071b.electrical_delay == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, 0.34),
            (Parameter.VOLTAGE, -20.1),
        ],
    )
    def test_setup_method_flt_raises_exception(self, parameter, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect float parameter"""
        with pytest.raises(ParameterNotFound):
            e5071b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.TRIGGER_MODE, "INT"),
            (Parameter.SCATTERING_PARAMETER, "S21"),
        ],
    )
    def test_setup_method_value_str(self, parameter: Parameter, value, e5071b: E5071B):
        """Test the setup method with str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        e5071b.setup(parameter, value)
        if parameter == Parameter.TRIGGER_MODE:
            assert e5071b.trigger_mode == VNATriggerModes(value)
        if parameter == Parameter.SCATTERING_PARAMETER:
            assert e5071b.scattering_parameter == VNAScatteringParameters(value)

    @pytest.mark.parametrize(
        "value",
        [
            "S221",
            "s11",
        ],
    )
    def test_setup_scattering_value_raises_exception(self, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect str value"""
        assert isinstance(value, str)
        with pytest.raises(ValueError):
            e5071b.scattering_parameter = value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, "foo"),
            (Parameter.VOLTAGE, "bar"),
        ],
    )
    def test_setup_method_str_raises_exception(self, parameter, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect str parameter"""
        with pytest.raises(ParameterNotFound):
            e5071b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value", [(Parameter.AVERAGING_ENABLED, True), (Parameter.AVERAGING_ENABLED, False)]
    )
    def test_setup_method_value_bool(self, parameter: Parameter, value, e5071b: E5071B):
        """Test the setup method with bool value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, bool)
        e5071b.setup(parameter, value)
        if parameter == Parameter.AVERAGING_ENABLED:
            assert e5071b.averaging_enabled == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, True),
            (Parameter.VOLTAGE, False),
        ],
    )
    def test_setup_method_bool_raises_exception(self, parameter, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect bool parameter"""
        with pytest.raises(ParameterNotFound):
            e5071b.setup(parameter, value)

    @pytest.mark.parametrize("parameter, value", [(Parameter.NUMBER_POINTS, 100), (Parameter.NUMBER_AVERAGES, 4)])
    def test_setup_method_value_int(self, parameter: Parameter, value, e5071b: E5071B):
        """Test the setup method with int value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, int)
        e5071b.setup(parameter, value)
        if parameter == Parameter.NUMBER_POINTS:
            assert e5071b.number_points == value
        if parameter == Parameter.NUMBER_AVERAGES:
            assert e5071b.number_averages == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, 0),
            (Parameter.VOLTAGE, -20),
        ],
    )
    def test_setup_method_int_raises_exception(self, parameter, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect int parameter"""
        with pytest.raises(ParameterNotFound):
            e5071b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.SCATTERING_PARAMETER, ["S221"]),
            (Parameter.SCATTERING_PARAMETER, {}),
        ],
    )
    def test_setup_method_raises_exception(self, parameter, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect value type"""
        with pytest.raises(ParameterNotFound):
            e5071b.setup(parameter, value)

    def test_to_dict_method(self, e5071b_no_device: E5071B):
        """Test the dict method"""
        assert isinstance(e5071b_no_device.to_dict(), dict)

    def test_reset_method(self, e5071b: E5071B):
        """Test the reset method"""
        e5071b.reset()
        e5071b.device.reset.assert_called()

    def test_turn_on_method(self, e5071b: E5071B):
        """Test turn on method"""
        e5071b.turn_on()
        e5071b.device.send_command.assert_called_with(command=":OUTP", arg="ON")

    def test_turn_off_method(self, e5071b: E5071B):
        """Test turn off method"""
        e5071b.turn_off()
        e5071b.device.send_command.assert_called_with(command=":OUTP", arg="OFF")

    @pytest.mark.parametrize("command, arg", [(":SENS1:AVER:CLE", ""), ("SENS1:AVER:COUN", "3")])
    def test_send_command_method(self, command, arg, e5071b: E5071B):
        """Test the send command method"""
        assert isinstance(command, str)
        assert isinstance(arg, str)
        e5071b.send_command(command, arg)
        e5071b.device.send_command.assert_called_with(command, arg)

    @patch("numpy.frombuffer")
    def test_get_data_method(self, mock_frombuffer, e5071b: E5071B):  # sourcery skip: simplify-division
        """Test the get data method"""
        mock_buffer = MagicMock(name="mock_frombuffer")
        mock_frombuffer.return_value = mock_buffer
        e5071b.get_data()
        e5071b.device.send_command.assert_called()
        e5071b.device.read_raw.assert_called()

    @patch("numpy.frombuffer")
    def test_acquire_result_method(self, mock_frombuffer, e5071b: E5071B):
        """Test the acquire result method"""
        mock_buffer = MagicMock(name="mock_frombuffer")
        mock_frombuffer.return_value = mock_buffer
        output = e5071b.acquire_result()
        assert isinstance(output, VNAResult)

    @pytest.mark.parametrize("continuous", [True, False])
    def test_continuous_method(self, continuous, e5071b: E5071B):
        """Test the continuous method"""
        e5071b.continuous(continuous)
        if continuous:
            e5071b.device.send_command.assert_called_with(":INIT:CONT", "ON")
        else:
            e5071b.device.send_command.assert_called_with(":INIT:CONT", "OFF")

    @pytest.mark.parametrize("query", [":SENS1:SWE:MODE?"])
    def test_send_query_method(self, query: str, e5071b: E5071B):
        """Test the send query method"""
        assert isinstance(query, str)
        e5071b.send_query(query)
        e5071b.device.send_query.assert_called_with(query)

    @pytest.mark.parametrize("query", ["SENS:X?", "CALC1:MEAS1:DATA:SDAT?"])
    def test_send_binary_query_method(self, query: str, e5071b: E5071B):
        """Test the send binary query method"""
        assert isinstance(query, str)
        e5071b.send_binary_query(query)
        e5071b.device.send_binary_query.assert_called_with(query)

    def test_read_method(self, e5071b: E5071B):
        """Test the read method"""
        e5071b.read()
        e5071b.device.read.assert_called()

    def test_read_raw_method(self, e5071b: E5071B):
        """Test the read method"""
        e5071b.read_raw()
        e5071b.device.read_raw.assert_called()

    def test_set_timeout_method(self, e5071b: E5071B):
        """Test the set timeout method"""
        e5071b.set_timeout(100)
        e5071b.device.set_timeout.assert_called_with(100)

    @pytest.mark.parametrize(
        "state, command, arg", [(True, "SENS1:AVER:STAT", "ON"), (False, "SENS1:AVER:STAT", "OFF")]
    )
    def test_average_state_method(self, state, command, arg, e5071b: E5071B):
        """Test the auxiliary private method average state"""
        e5071b._average_state(state)
        e5071b.device.send_command.assert_called_with(command=command, arg=arg)

    def test_average_count_method(self, e5071b: E5071B):
        """Set the average count"""
        e5071b._average_count(1, 1)  # Have to know if you can select which one was called
        e5071b.device.send_command.assert_called()

    def test_autoscale_method(self, e5071b: E5071B):
        """Test the autoscale method"""
        e5071b.autoscale()
        e5071b.device.send_command.assert_called_with(command="DISP:WIND:TRAC:Y:AUTO", arg="")

    def test_power_property(self, e5071b_no_device: E5071B):
        """Test power property."""
        assert hasattr(e5071b_no_device, "power")
        assert e5071b_no_device.power == e5071b_no_device.settings.power

    def test_scattering_parameter_property(self, e5071b_no_device: E5071B):
        """Test the scattering parametter property"""
        assert hasattr(e5071b_no_device, "scattering_parameter")
        assert e5071b_no_device.scattering_parameter == e5071b_no_device.settings.scattering_parameter

    def test_frequency_span_property(self, e5071b_no_device: E5071B):
        """Test the frequency span property"""
        assert hasattr(e5071b_no_device, "frequency_span")
        assert e5071b_no_device.frequency_span == e5071b_no_device.settings.frequency_span

    def test_frequency_center_property(self, e5071b_no_device: E5071B):
        """Test the frequency center property"""
        assert hasattr(e5071b_no_device, "frequency_center")
        assert e5071b_no_device.frequency_center == e5071b_no_device.settings.frequency_center

    def test_frequency_start_property(self, e5071b_no_device: E5071B):
        """Test the frequency start property"""
        assert hasattr(e5071b_no_device, "frequency_start")
        assert e5071b_no_device.frequency_start == e5071b_no_device.settings.frequency_start

    def test_frequency_stop_property(self, e5071b_no_device: E5071B):
        """Test the frequency stop property"""
        assert hasattr(e5071b_no_device, "frequency_stop")
        assert e5071b_no_device.frequency_stop == e5071b_no_device.settings.frequency_stop

    def test_if_bandwidth_property(self, e5071b_no_device: E5071B):
        """Test the if bandwidth property"""
        assert hasattr(e5071b_no_device, "if_bandwidth")
        assert e5071b_no_device.if_bandwidth == e5071b_no_device.settings.if_bandwidth

    def test_averaging_enabled_property(self, e5071b_no_device: E5071B):
        """Test the averaging enabled property"""
        assert hasattr(e5071b_no_device, "averaging_enabled")
        assert e5071b_no_device.averaging_enabled == e5071b_no_device.settings.averaging_enabled

    def test_number_averages_propertyy(self, e5071b_no_device: E5071B):
        """Test the number of averages property"""
        assert hasattr(e5071b_no_device, "number_averages")
        assert e5071b_no_device.number_averages == e5071b_no_device.settings.number_averages

    def test_trigger_mode_property(self, e5071b_no_device: E5071B):
        """Test the trigger mode property"""
        assert hasattr(e5071b_no_device, "trigger_mode")
        assert e5071b_no_device.trigger_mode == e5071b_no_device.settings.trigger_mode

    def test_number_points_property(self, e5071b_no_device: E5071B):
        """Test the number points property"""
        assert hasattr(e5071b_no_device, "number_points")
        assert e5071b_no_device.number_points == e5071b_no_device.settings.number_points

    def test_electrical_delay_property(self, e5071b_no_device: E5071B):
        """Test the electrical delay property"""
        assert hasattr(e5071b_no_device, "electrical_delay")
        assert e5071b_no_device.electrical_delay == e5071b_no_device.settings.electrical_delay
